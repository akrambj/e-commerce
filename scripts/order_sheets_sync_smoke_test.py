from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.repository import OrdersRepository
from app.modules.orders.sheets_sync import try_sync_order_to_sheets

db = SessionLocal()
repo = OrdersRepository()

try:
    order_id = 1  # use a real order id
    try_sync_order_to_sheets(db, order_id=order_id, repo=repo)
    db.commit()
    print("✅ sync attempted (check sheet + DB fields)")
finally:
    db.close()
