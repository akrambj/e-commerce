from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.db.repository import OrdersRepository
from app.infrastructure.integrations.google_sheets import get_sheets_client


def _format_items_summary(items) -> str:
    # simple v1: "slug xqty | slug xqty"
    parts: list[str] = []
    for it in items:
        parts.append(f"{it.product_slug} x{it.quantity}")
    return " | ".join(parts)


def build_order_row(order) -> list[str]:
    """
    Returns a single row (list of strings) to append to Sheets.
    Keep it dumb and readable for humans (v1).
    """
    return [
        str(order.id),
        order.created_at.isoformat() if order.created_at else "",
        order.status,
        f"{order.first_name} {order.last_name}",
        order.phone_number,
        order.wilaya,
        order.baladiya,
        order.delivery_mode,
        order.address_line or "",
        _format_items_summary(order.items or []),
        str(order.items_subtotal),
        str(order.delivery_fee),
        str(order.total_amount),
    ]


def try_sync_order_to_sheets(
    db: Session,
    *,
    order_id: int,
    repo: OrdersRepository,
) -> None:
    """
    Best-effort sheets sync:
    - loads order + items
    - appends row to Sheets
    - updates order sheets_status to SUCCESS/FAILED
    - NEVER raises (so it can't break the API response)
    """
    order = repo.get_order_by_id(db, order_id=order_id, include_items=True)
    if not order:
        return

    try:
        client = get_sheets_client()
        row = build_order_row(order)
        client.append_row(row)

        repo.set_sheets_sync_result(db, order=order, status="SUCCESS")
    except Exception as e:
        # store a short error for debugging
        repo.set_sheets_sync_result(db, order=order, status="FAILED", error=str(e))
