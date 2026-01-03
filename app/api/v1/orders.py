from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.responses import ok
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repository import OrdersRepository
from app.modules.orders.schemas import OrderCreateIn, OrderOut
from app.modules.orders.service import (
    OrdersService,
    CreateOrderIn,
    CreateOrderItemIn,
)
from app.modules.orders.sheets_sync import try_sync_order_to_sheets

router = APIRouter(prefix="/orders", tags=["orders"])

logger = get_logger("sheets")


def get_orders_service() -> OrdersService:
    # simple v1 wiring (no DI container yet)
    return OrdersService(repo=OrdersRepository())


@router.post("", response_model=None)
def create_order(payload: OrderCreateIn, request: Request, db: Session = Depends(get_db)):
    service = get_orders_service()

    service_payload = CreateOrderIn(
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone_number=payload.phone_number,
        wilaya=payload.wilaya,
        baladiya=payload.baladiya,
        delivery_mode=payload.delivery_mode,
        address_line=payload.address_line,
        delivery_fee=payload.delivery_fee,
        items=[
            CreateOrderItemIn(product_id=i.product_id, quantity=i.quantity)
            for i in payload.items
        ],
    )

    # 1) Create order in DB (this should commit inside service in your current setup)
    order = service.create_order(db, service_payload)

    # 2) Best-effort Sheets sync (must never break response)
    try:
        try_sync_order_to_sheets(db, order_id=order.id, repo=OrdersRepository())
        logger.info(
            "Sheets sync attempted",
            extra={
                "order_id": order.id,
                "request_id": getattr(request.state, "request_id", None),
            },
        )
    except Exception:
        # Should not happen because try_sync already catches,
        # but keep a safety net.
        logger.exception(
            "Unexpected error calling sheets sync",
            extra={
                "order_id": order.id,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    # 3) Response
    data = OrderOut.model_validate(order).model_dump()
    return ok(data, message="Order created")
