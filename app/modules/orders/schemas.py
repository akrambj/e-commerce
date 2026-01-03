from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------
# Input (public)
# ---------------------------

class OrderItemCreateIn(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class OrderCreateIn(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone_number: str = Field(..., min_length=1, max_length=30)

    wilaya: str = Field(..., min_length=1, max_length=80)
    baladiya: str = Field(..., min_length=1, max_length=120)

    delivery_mode: str = Field(..., min_length=1, max_length=20)  # HOME | STOP_DESK
    address_line: Optional[str] = None

    delivery_fee: int = Field(..., ge=0)

    items: List[OrderItemCreateIn] = Field(..., min_length=1)


# ---------------------------
# Output
# ---------------------------

class OrderItemOut(BaseModel):
    product_id: int
    product_slug: str
    product_name: str
    unit_price: int
    quantity: int
    line_total: int

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    status: str

    first_name: str
    last_name: str
    phone_number: str

    wilaya: str
    baladiya: str
    delivery_mode: str
    address_line: Optional[str]

    items_subtotal: int
    delivery_fee: int
    total_amount: int

    sheets_status: str

    items: List[OrderItemOut]

    class Config:
        from_attributes = True


# ---------------------------
# Output (admin list)
# ---------------------------

class OrdersListOut(BaseModel):
    items: List[OrderOut]
    total: int
    page: int
    page_size: int
