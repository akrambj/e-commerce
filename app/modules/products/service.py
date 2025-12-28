# app/modules/products/service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Sequence

from sqlalchemy.orm import Session

from app.core.exceptions import ProductNotFoundError, ProductNotPublicError
from app.infrastructure.db.models import Product
from app.infrastructure.db.repository import ProductsRepository


@dataclass
class ProductsService:
    """
    Service layer = business rules + orchestration.
    - No FastAPI imports
    - No HTTP concerns
    - No SQL queries
    """
    repo: ProductsRepository

    def list_public_products(
        self,
        db: Session,
        *,
        page: int = 1,
        page_size: int = 10,
        category: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Tuple[Sequence[Product], int]:
        # Business guardrails (light v1)
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 1
        if page_size > 100:
            page_size = 100

        return self.repo.list_public_products(
            db,
            page=page,
            page_size=page_size,
            category=category,
            min_price=min_price,
            max_price=max_price,
            search=search,
        )

    def get_public_product_by_slug(self, db: Session, *, slug: str) -> Product:
        slug = (slug or "").strip()
        if not slug:
            raise ProductNotFoundError("Product not found.", details={"slug": slug})

        product = self.repo.get_public_product_by_slug(db, slug=slug)

        if product is None:
            raise ProductNotFoundError("Product not found.", details={"slug": slug})

        return product

    def get_product_by_id(self, db: Session, *, product_id: int) -> Product:
        product = self.repo.get_product_by_id(db, product_id=product_id)
        if product is None:
            raise ProductNotFoundError("Product not found.", details={"product_id": product_id})
        return product
