from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.products import router as products_router
from app.api.v1.admin.products import router as admin_products_router
from app.api.v1.orders import router as orders_router
from app.api.v1.admin.orders import router as admin_orders_router
from app.api.v1.admin.auth import router as admin_auth_router

router = APIRouter(prefix="/api/v1")

router.include_router(products_router)
router.include_router(admin_products_router)
router.include_router(orders_router)
router.include_router(admin_orders_router)
router.include_router(admin_auth_router)
