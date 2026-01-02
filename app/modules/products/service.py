# app/modules/products/service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ProductNotFoundError,
    ProductSlugConflictError,
    ValidationError,
)
from app.infrastructure.db.models import Product
from app.infrastructure.db.repository import ProductsRepository
from app.modules.products.schemas import ProductCreateIn, ProductUpdateIn


@dataclass
class ProductsService:
    repo: ProductsRepository

    # ---------- public methods ----------

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

    # ---------- admin methods ----------

    def list_admin_products(
        self,
        db: Session,
        *,
        page: int = 1,
        page_size: int = 10,
        category: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False,
    ) -> Tuple[Sequence[Product], int]:
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 1
        if page_size > 100:
            page_size = 100

        return self.repo.list_admin_products(
            db,
            page=page,
            page_size=page_size,
            category=category,
            min_price=min_price,
            max_price=max_price,
            search=search,
            is_active=is_active,
            include_deleted=include_deleted,
        )

    def get_product_by_id(self, db: Session, *, product_id: int) -> Product:
        product = self.repo.get_product_by_id(db, product_id=product_id)
        if product is None:
            raise ProductNotFoundError("Product not found.", details={"product_id": product_id})
        return product

    def create_product(self, db: Session, *, payload: ProductCreateIn) -> Product:
        slug = (payload.slug or "").strip()
        if not slug:
            raise ValidationError("Slug is required.", details={"slug": slug})

        existing = self.repo.get_product_by_slug_any(db, slug=slug)
        if existing is not None:
            raise ProductSlugConflictError("Slug already exists.", details={"slug": slug})

        image_urls = [u.strip() for u in payload.images if u and u.strip()]

        product = self.repo.create_product(
            db,
            slug=slug,
            name=payload.name.strip(),
            description=payload.description,
            price=payload.price,
            category=(payload.category or "uncategorized").strip(),
            quantity=payload.quantity,
            thumbnail_url=payload.thumbnail_url.strip(),
            is_active=payload.is_active,
            image_urls=image_urls,
        )

        return product

    def update_product(self, db: Session, *, product_id: int, payload: ProductUpdateIn) -> Product:
        product = self.repo.get_product_by_id(db, product_id=product_id, include_images=False)
        if product is None:
            raise ProductNotFoundError("Product not found.", details={"product_id": product_id})

        slug = (payload.slug or "").strip()
        if not slug:
            raise ValidationError("Slug is required.", details={"slug": slug})

        if slug != product.slug:
            existing = self.repo.get_product_by_slug_any(db, slug=slug)
            if existing is not None and existing.id != product.id:
                raise ProductSlugConflictError("Slug already exists.", details={"slug": slug})

        image_urls = [u.strip() for u in payload.images if u and u.strip()]

        updated = self.repo.update_product(
            db,
            product=product,
            slug=slug,
            name=payload.name.strip(),
            description=payload.description,
            price=payload.price,
            category=(payload.category or "uncategorized").strip(),
            quantity=payload.quantity,
            thumbnail_url=payload.thumbnail_url.strip(),
            is_active=payload.is_active,
            image_urls=image_urls,
        )

        return updated

    def activate_product(self, db: Session, *, product_id: int) -> Product:
        product = self.repo.get_product_by_id(db, product_id=product_id, include_images=False)
        if product is None:
            raise ProductNotFoundError("Product not found.", details={"product_id": product_id})

        return self.repo.set_product_active(db, product=product, is_active=True)

    def deactivate_product(self, db: Session, *, product_id: int) -> Product:
        product = self.repo.get_product_by_id(db, product_id=product_id, include_images=False)
        if product is None:
            raise ProductNotFoundError("Product not found.", details={"product_id": product_id})

        return self.repo.set_product_active(db, product=product, is_active=False)

    def delete_product(self, db: Session, *, product_id: int) -> Product:
        product = self.repo.get_product_by_id(db, product_id=product_id, include_images=False)
        if product is None:
            raise ProductNotFoundError("Product not found.", details={"product_id": product_id})

        return self.repo.soft_delete_product(db, product=product)
