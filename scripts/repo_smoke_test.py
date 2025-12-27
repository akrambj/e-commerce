from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.repository import ProductsRepository

repo = ProductsRepository()

db = SessionLocal()
try:
    items, total = repo.list_public_products(db, page=1, page_size=10)
    print("total:", total)
    print("items:", [p.slug for p in items])
finally:
    db.close()


# to run this script type the following command 
# python -m scripts.repo_smoke_test