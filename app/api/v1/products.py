from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.responses import ok
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repository import ProductsRepository
from app.modules.products.schemas import ProductsListOut, ProductOut, PageMeta
from app.modules.products.service import ProductsService

router = APIRouter(prefix="/products", tags=["products"])


def get_products_service() -> ProductsService:
    return ProductsService(repo=ProductsRepository())


@router.get("")
def list_products(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category: Optional[str] = Query(None),
    min_price: Optional[int] = Query(None, ge=0),
    max_price: Optional[int] = Query(None, ge=0),
    search: Optional[str] = Query(None),
):
    service = get_products_service()
    items, total = service.list_public_products(
        db,
        page=page,
        page_size=page_size,
        category=category,
        min_price=min_price,
        max_price=max_price,
        search=search,
    )

    payload = ProductsListOut(
        items=[ProductOut.model_validate(p) for p in items],
        meta=PageMeta(page=page, page_size=page_size, total=total),
    )

    return ok(payload, message="Products fetched")


@router.get("/{slug}")
def get_product(
    slug: str,
    db: Session = Depends(get_db),
):
    service = get_products_service()
    product = service.get_public_product_by_slug(db, slug=slug)
    payload = ProductOut.model_validate(product)
    return ok(payload, message="Product fetched")
