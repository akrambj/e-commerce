from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import (
    InsufficientStockError,
    InvalidOrderPayloadError,
    OrderNotFoundError,
    OrderStatusTransitionError,
    ProductUnavailableError,
)
from app.infrastructure.db.models import Order, OrderItem, Product
from app.infrastructure.db.repository import OrdersRepository
from app.modules.orders.sheets_sync import try_sync_order_to_sheets


ALLOWED_DELIVERY_MODES = {"HOME", "STOP_DESK"}
ALLOWED_ORDER_STATUSES = {"PENDING", "CONFIRMED", "DELIVERED", "CANCELED"}


@dataclass(frozen=True)
class CreateOrderItemIn:
    product_id: int
    quantity: int


@dataclass(frozen=True)
class CreateOrderIn:
    first_name: str
    last_name: str
    phone_number: str
    wilaya: str
    baladiya: str
    delivery_mode: str  # HOME | STOP_DESK
    address_line: str | None
    delivery_fee: int
    items: Sequence[CreateOrderItemIn]


class OrdersService:
    def __init__(self, repo: OrdersRepository) -> None:
        self.repo = repo

    # ---------------------------
    # Admin reads (Step 21.1)
    # ---------------------------

    def list_orders(
        self,
        db: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        phone_number: str | None = None,
    ) -> Tuple[Sequence[Order], int]:
        return self.repo.list_orders(
            db,
            page=page,
            page_size=page_size,
            status=status,
            phone_number=phone_number,
        )

    def get_order_by_id(self, db: Session, *, order_id: int) -> Order:
        order = self.repo.get_order_by_id(db, order_id=order_id, include_items=True)
        if not order:
            raise OrderNotFoundError(message="Order not found")
        return order

    # ---------------------------
    # Sheets retry (Step 21.4)
    # ---------------------------

    def retry_sheets_sync(self, db: Session, *, order_id: int) -> Order:
        """
        Best-effort manual retry of Google Sheets sync.
        - Does not fail the request if Sheets fails.
        - Updates sheets_status/sheets_error via repo helper inside try_sync_order_to_sheets.
        Returns the latest order state.
        """
        order = self.repo.get_order_by_id(db, order_id=order_id, include_items=True)
        if not order:
            raise OrderNotFoundError(message="Order not found")

        try:
            try_sync_order_to_sheets(db, order_id=order_id, repo=self.repo)
        except Exception:
            # Never break admin endpoint due to external integration surprises
            pass

        updated = self.repo.get_order_by_id(db, order_id=order_id, include_items=True)
        if not updated:
            raise OrderNotFoundError(message="Order not found")
        return updated

    # ---------------------------
    # Public writes
    # ---------------------------

    def create_order(self, db: Session, payload: CreateOrderIn) -> Order:
        self._validate_create_payload(payload)

        # Merge duplicate items (same product_id) -> single quantity
        requested_qty_by_pid: Dict[int, int] = {}
        for it in payload.items:
            requested_qty_by_pid[it.product_id] = requested_qty_by_pid.get(it.product_id, 0) + it.quantity

        product_ids = list(requested_qty_by_pid.keys())

        # Only purchasable products (active + not deleted)
        products = self.repo.get_active_products_by_ids(db, product_ids=product_ids)
        products_by_id: Dict[int, Product] = {p.id: p for p in products}

        # Missing/unavailable products
        missing = [pid for pid in product_ids if pid not in products_by_id]
        if missing:
            raise ProductUnavailableError(
                message="One or more products are not available",
                details={"missing_product_ids": missing},
            )

        # Stock validation
        insufficient: List[dict] = []
        for pid, req_qty in requested_qty_by_pid.items():
            p = products_by_id[pid]
            if p.quantity < req_qty:
                insufficient.append(
                    {"product_id": pid, "requested": req_qty, "available": p.quantity}
                )

        if insufficient:
            raise InsufficientStockError(
                message="Insufficient stock for one or more products",
                details={"items": insufficient},
            )

        # Build order items snapshots + totals
        order_items: List[OrderItem] = []
        items_subtotal = 0

        for pid, qty in requested_qty_by_pid.items():
            p = products_by_id[pid]
            line_total = p.price * qty
            items_subtotal += line_total

            order_items.append(
                OrderItem(
                    order_id=0,  # set after order flush
                    product_id=p.id,
                    product_slug=p.slug,
                    product_name=p.name,
                    unit_price=p.price,
                    quantity=qty,
                    line_total=line_total,
                )
            )

        total_amount = items_subtotal + payload.delivery_fee

        order = Order(
            status="PENDING",
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            phone_number=payload.phone_number.strip(),
            wilaya=payload.wilaya.strip(),
            baladiya=payload.baladiya.strip(),
            delivery_mode=payload.delivery_mode.strip().upper(),
            address_line=(payload.address_line.strip() if payload.address_line else None),
            items_subtotal=items_subtotal,
            delivery_fee=payload.delivery_fee,
            total_amount=total_amount,
            sheets_status="PENDING",
            sheets_synced_at=None,
            sheets_error=None,
        )

        # Transaction boundary: commit/rollback here
        try:
            # decrement stock
            for pid, qty in requested_qty_by_pid.items():
                products_by_id[pid].quantity -= qty
                db.add(products_by_id[pid])

            self.repo.create_order(db, order=order, items=order_items)

            db.commit()
            db.refresh(order)
            return order
        except Exception:
            db.rollback()
            raise

    def set_order_status(self, db: Session, *, order_id: int, new_status: str) -> Order:
        ns = new_status.strip().upper()

        if ns not in ALLOWED_ORDER_STATUSES:
            raise InvalidOrderPayloadError(
                message="Invalid order payload",
                details={"status": new_status},
            )

        order = self.repo.get_order_by_id(db, order_id=order_id, include_items=True)
        if not order:
            raise OrderNotFoundError(message="Order not found")

        old = (order.status or "").strip().upper()
        if old == ns:
            return order

        allowed = {
            "PENDING": {"CONFIRMED", "CANCELED"},
            "CONFIRMED": {"DELIVERED", "CANCELED"},
            "DELIVERED": set(),
            "CANCELED": set(),
        }

        if ns not in allowed.get(old, set()):
            raise OrderStatusTransitionError(
                message="Invalid order status transition",
                details={"from": old, "to": ns},
            )

        try:
            # Cancel restores stock (Option B)
            if ns == "CANCELED":
                self._restore_stock_for_order(db, order)

            self.repo.update_order_status(db, order=order, status=ns)

            db.commit()
            db.refresh(order)
            return order
        except Exception:
            db.rollback()
            raise

    def _restore_stock_for_order(self, db: Session, order: Order) -> None:
        """
        Restore stock once on cancel.
        We only call this when transitioning INTO CANCELED, so it’s idempotent by design.
        """
        product_ids = [it.product_id for it in order.items]
        if not product_ids:
            return

        # Restore even if products are now inactive/deleted
        products = db.query(Product).filter(Product.id.in_(product_ids)).all()
        products_by_id = {p.id: p for p in products}

        for it in order.items:
            p = products_by_id.get(it.product_id)
            if p:
                p.quantity += it.quantity
                db.add(p)

    def _validate_create_payload(self, payload: CreateOrderIn) -> None:
        if not payload.items or len(payload.items) == 0:
            raise InvalidOrderPayloadError(
                message="Invalid order payload",
                details={"items": "at least one item is required"},
            )

        if payload.delivery_fee < 0:
            raise InvalidOrderPayloadError(
                message="Invalid order payload",
                details={"delivery_fee": payload.delivery_fee},
            )

        dm = payload.delivery_mode.strip().upper()
        if dm not in ALLOWED_DELIVERY_MODES:
            raise InvalidOrderPayloadError(
                message="Invalid order payload",
                details={"delivery_mode": payload.delivery_mode},
            )

        required_str_fields = {
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "phone_number": payload.phone_number,
            "wilaya": payload.wilaya,
            "baladiya": payload.baladiya,
        }
        for k, v in required_str_fields.items():
            if not v or not v.strip():
                raise InvalidOrderPayloadError(
                    message="Invalid order payload",
                    details={k: "required"},
                )

        for it in payload.items:
            if it.product_id <= 0:
                raise InvalidOrderPayloadError(
                    message="Invalid order payload",
                    details={"product_id": it.product_id},
                )
            if it.quantity <= 0:
                raise InvalidOrderPayloadError(
                    message="Invalid order payload",
                    details={"quantity": it.quantity},
                )
