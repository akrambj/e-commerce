from datetime import datetime, timezone

import pytest

from app.infrastructure.db.models import Product
from app.infrastructure.db.repository import ProductsRepository


@pytest.fixture()
def repo() -> ProductsRepository:
    return ProductsRepository()


def seed_product(db, **overrides) -> Product:
    p = Product(
        slug=overrides.get("slug", "p-1"),
        name=overrides.get("name", "Product 1"),
        description=overrides.get("description"),
        price=overrides.get("price", 1000),
        category=overrides.get("category", "uncategorized"),
        quantity=overrides.get("quantity", 5),
        thumbnail_url=overrides.get("thumbnail_url", "https://img/1.png"),
        is_active=overrides.get("is_active", True),
        deleted_at=overrides.get("deleted_at", None),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def test_list_public_products_filters_out_inactive_and_deleted(db, repo):
    seed_product(db, slug="public-1", is_active=True, deleted_at=None)
    seed_product(db, slug="inactive-1", is_active=False, deleted_at=None)
    seed_product(db, slug="deleted-1", is_active=True, deleted_at=datetime.now(timezone.utc))

    items, total = repo.list_public_products(db, page=1, page_size=20)

    slugs = [p.slug for p in items]
    assert "public-1" in slugs
    assert "inactive-1" not in slugs
    assert "deleted-1" not in slugs
    assert total == 1
