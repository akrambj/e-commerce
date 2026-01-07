from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.responses import ok
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repository import OrdersRepository
from app.modules.orders.schemas import OrderOut, OrdersListOut
from app.modules.orders.service import OrdersService
from app.api.dependencies.admin_auth import require_admin


router = APIRouter(prefix="/admin/orders", tags=["admin:orders"], dependencies=[Depends(require_admin)])


def get_orders_service() -> OrdersService:
    return OrdersService(repo=OrdersRepository())


@router.get("", response_model=None)
def list_orders(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    phone_number: str | None = Query(None),
):
    service = get_orders_service()

    items, total = service.list_orders(
        db,
        page=page,
        page_size=page_size,
        status=status,
        phone_number=phone_number,
    )

    data = OrdersListOut(
        items=[OrderOut.model_validate(o) for o in items],
        total=total,
        page=page,
        page_size=page_size,
    ).model_dump()

    return ok(data, message="Orders fetched")


@router.get("/{order_id}", response_model=None)
def get_order(order_id: int, db: Session = Depends(get_db)):
    service = get_orders_service()
    order = service.get_order_by_id(db, order_id=order_id)

    data = OrderOut.model_validate(order).model_dump()
    return ok(data, message="Order fetched")


@router.patch("/{order_id}/confirm", response_model=None)
def confirm_order(order_id: int, db: Session = Depends(get_db)):
    service = get_orders_service()
    order = service.set_order_status(db, order_id=order_id, new_status="CONFIRMED")

    data = OrderOut.model_validate(order).model_dump()
    return ok(data, message="Order confirmed")


@router.patch("/{order_id}/cancel", response_model=None)
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    service = get_orders_service()
    order = service.set_order_status(db, order_id=order_id, new_status="CANCELED")

    data = OrderOut.model_validate(order).model_dump()
    return ok(data, message="Order canceled")


@router.patch("/{order_id}/deliver", response_model=None)
def deliver_order(order_id: int, db: Session = Depends(get_db)):
    service = get_orders_service()
    order = service.set_order_status(db, order_id=order_id, new_status="DELIVERED")

    data = OrderOut.model_validate(order).model_dump()
    return ok(data, message="Order delivered")


# ---------------------------
# Sheets retry (Step 21.4)
# ---------------------------

@router.post("/{order_id}/sheets/retry", response_model=None)
def retry_sheets_sync(order_id: int, db: Session = Depends(get_db)):
    service = get_orders_service()
    order = service.retry_sheets_sync(db, order_id=order_id)

    data = OrderOut.model_validate(order).model_dump()
    return ok(data, message="Sheets sync retried")
