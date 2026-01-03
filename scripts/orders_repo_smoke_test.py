from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.repository import OrdersRepository

repo = OrdersRepository()
db = SessionLocal()

try:
    items, total = repo.list_orders(db, page=1, page_size=10)
    print("total orders:", total)
    print("items:", [o.id for o in items])
finally:
    db.close()
