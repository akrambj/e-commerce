from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.repository import OrdersRepository

db = SessionLocal()
repo = OrdersRepository()

try:
    order = repo.get_order_by_id(db, order_id=1, include_items=False)
    if not order:
        raise SystemExit("Order id=1 not found. Use a real existing order id.")

    repo.set_sheets_sync_result(db, order=order, status="FAILED", error="test failure")
    db.commit()
    print("✅ set FAILED")

    repo.set_sheets_sync_result(db, order=order, status="SUCCESS")
    db.commit()
    print("✅ set SUCCESS")
finally:
    db.close()
