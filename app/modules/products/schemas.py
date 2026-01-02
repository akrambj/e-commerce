from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int


class ProductImageOut(BaseModel):
    url: str
    position: int

    model_config = {"from_attributes": True}


class ProductOut(BaseModel):
    id: int
    slug: str
    name: str
    description: Optional[str] = None
    price: int
    category: str
    quantity: int
    thumbnail_url: str
    is_active: bool
    images: List[ProductImageOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ProductsListOut(BaseModel):
    items: List[ProductOut]
    meta: PageMeta


# ---------- Admin inputs (v1) ----------

class ProductCreateIn(BaseModel):
    slug: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: int = Field(..., ge=0)
    category: str = Field(default="uncategorized", min_length=1)
    quantity: int = Field(default=0, ge=0)
    thumbnail_url: str = Field(..., min_length=1)
    is_active: bool = True
    images: List[str] = Field(default_factory=list)


class ProductUpdateIn(BaseModel):
    slug: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: int = Field(..., ge=0)
    category: str = Field(default="uncategorized", min_length=1)
    quantity: int = Field(default=0, ge=0)
    thumbnail_url: str = Field(..., min_length=1)
    is_active: bool = True
    images: List[str] = Field(default_factory=list)
