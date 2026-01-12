from __future__ import annotations

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.dependencies.admin_auth import require_admin
from app.core.exceptions import ValidationError
from app.core.responses import ok
from app.infrastructure.db.repository import ProductsRepository
from app.infrastructure.db.session import get_db
from app.infrastructure.integrations.cloudinary.uploader import (
    upload_product_image,
    upload_product_thumbnail,
)
from app.modules.products.schemas import (
    PageMeta,
    ProductCreateIn,
    ProductOut,
    ProductsListOut,
    ProductUpdateIn,
)
from app.modules.products.service import ProductsService

router = APIRouter(
    prefix="/admin/products",
    tags=["admin-products"],
    dependencies=[Depends(require_admin)],
)


def get_products_service() -> ProductsService:
    return ProductsService(repo=ProductsRepository())


@router.get("")
def list_admin_products(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category: Optional[str] = Query(None),
    min_price: Optional[int] = Query(None, ge=0),
    max_price: Optional[int] = Query(None, ge=0),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    include_deleted: bool = Query(False),
):
    service = get_products_service()

    items, total = service.list_admin_products(
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

    out_items = [ProductOut.model_validate(p) for p in items]
    meta = PageMeta(page=page, page_size=page_size, total=total)
    data = ProductsListOut(items=out_items, meta=meta)

    return ok(data, message="Admin products fetched")


@router.get("/{product_id}")
def get_admin_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    service = get_products_service()
    product = service.get_product_by_id(db, product_id=product_id)

    data = ProductOut.model_validate(product)
    return ok(data, message="Admin product fetched")


@router.post("")
def create_admin_product(
    payload: ProductCreateIn,
    db: Session = Depends(get_db),
):
    service = get_products_service()

    try:
        product = service.create_product(db, payload=payload)
        db.commit()
    except Exception:
        db.rollback()
        raise

    product = service.get_product_by_id(db, product_id=product.id)
    data = ProductOut.model_validate(product)
    return ok(data, message="Product created")


@router.put("/{product_id}")
def update_admin_product(
    product_id: int,
    payload: ProductUpdateIn,
    db: Session = Depends(get_db),
):
    service = get_products_service()

    try:
        product = service.update_product(db, product_id=product_id, payload=payload)
        db.commit()
    except Exception:
        db.rollback()
        raise

    product = service.get_product_by_id(db, product_id=product.id)
    data = ProductOut.model_validate(product)
    return ok(data, message="Product updated")


@router.patch("/{product_id}/activate")
def activate_admin_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    service = get_products_service()

    try:
        service.activate_product(db, product_id=product_id)
        db.commit()
    except Exception:
        db.rollback()
        raise

    product = service.get_product_by_id(db, product_id=product_id)
    data = ProductOut.model_validate(product)
    return ok(data, message="Product activated")


@router.patch("/{product_id}/deactivate")
def deactivate_admin_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    service = get_products_service()

    try:
        service.deactivate_product(db, product_id=product_id)
        db.commit()
    except Exception:
        db.rollback()
        raise

    product = service.get_product_by_id(db, product_id=product_id)
    data = ProductOut.model_validate(product)
    return ok(data, message="Product deactivated")


@router.delete("/{product_id}")
def delete_admin_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    service = get_products_service()

    try:
        service.delete_product(db, product_id=product_id)
        db.commit()
    except Exception:
        db.rollback()
        raise

    # Return the deleted product (admin can still view it)
    product = service.get_product_by_id(db, product_id=product_id)
    data = ProductOut.model_validate(product)
    return ok(data, message="Product deleted")


# ---------------------------
# Admin uploads (Cloudinary V1)
# ---------------------------

@router.post("/{product_id}/thumbnail")
async def upload_admin_product_thumbnail(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    service = get_products_service()

    # Ensure product exists
    product = service.get_product_by_id(db, product_id=product_id)

    public_id = f"product_{product.id}/thumbnail"
    url = await upload_product_thumbnail(file=file, public_id=public_id)

    try:
        service.set_product_thumbnail_url(db, product_id=product_id, thumbnail_url=url)
        db.commit()
    except Exception:
        db.rollback()
        raise

    product = service.get_product_by_id(db, product_id=product_id)
    data = ProductOut.model_validate(product)
    return ok(data, message="Thumbnail uploaded")


@router.post("/{product_id}/images")
async def upload_admin_product_images(
    product_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    if not files:
        raise ValidationError("No files uploaded.", details={"files": 0})

    # V1 guardrail
    if len(files) > 10:
        raise ValidationError("Too many images. Max is 10.", details={"max": 10, "got": len(files)})

    service = get_products_service()

    # Ensure product exists
    product = service.get_product_by_id(db, product_id=product_id)

    uploaded_urls: list[str] = []
    for f in files:
        public_id = f"product_{product.id}/img_{uuid4().hex}"
        url = await upload_product_image(file=f, public_id=public_id)
        uploaded_urls.append(url)

    try:
        service.append_product_images(db, product_id=product_id, new_image_urls=uploaded_urls)
        db.commit()
    except Exception:
        db.rollback()
        raise

    product = service.get_product_by_id(db, product_id=product_id)
    data = ProductOut.model_validate(product)
    return ok(data, message="Images uploaded")
