from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.infrastructure.db.models import Product, ProductImage  # adjust if your names differ


@dataclass(frozen=True)
class Page:
    page: int = 1
    page_size: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page must be >= 1")
        if not (1 <= self.page_size <= 100):
            raise ValueError("page_size must be between 1 and 100")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class ProductsRepository:
    """
    DB access only.
    No business rules beyond:
      - public visibility filtering
      - soft delete filtering for public reads
    """

    # ---------- internal helpers ----------

    def _public_visibility_filter(self) -> list:
        return [
            Product.is_active.is_(True),
            Product.deleted_at.is_(None),
        ]

    def _apply_filters(
        self,
        stmt: Select,
        *,
        category: Optional[str],
        min_price: Optional[int],
        max_price: Optional[int],
        search: Optional[str],
    ) -> Select:
        if category:
            stmt = stmt.where(Product.category == category)

        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)

        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)

        if search:
            # basic v1 search: name contains (case-insensitive)
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(Product.name.ilike(pattern))

        return stmt

    # ---------- public reads ----------

    def list_public_products(
        self,
        session: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Tuple[Sequence[Product], int]:
        """
        Returns (items, total).
        Public rules:
          - is_active = true
          - deleted_at is null
        """
        paging = Page(page=page, page_size=page_size)

        base_stmt = (
            select(Product)
            .where(*self._public_visibility_filter())
            .order_by(Product.created_at.desc(), Product.id.desc())
        )

        base_stmt = self._apply_filters(
            base_stmt,
            category=category,
            min_price=min_price,
            max_price=max_price,
            search=search,
        )

        # Total count (same filters, but count(*))
        count_stmt = (
            select(func.count())
            .select_from(Product)
            .where(*self._public_visibility_filter())
        )
        count_stmt = self._apply_filters(
            count_stmt,
            category=category,
            min_price=min_price,
            max_price=max_price,
            search=search,
        )

        total: int = session.execute(count_stmt).scalar_one()

        items_stmt = base_stmt.limit(paging.page_size).offset(paging.offset)

        items = session.execute(items_stmt).scalars().all()
        return items, total

    def get_public_product_by_slug(
        self,
        session: Session,
        *,
        slug: str,
    ) -> Optional[Product]:
        """
        Public detail by slug.
        Applies public visibility rules and eagerly loads images.
        """
        stmt = (
            select(Product)
            .where(*self._public_visibility_filter())
            .where(Product.slug == slug)
            .options(selectinload(Product.images))  # adjust relationship name if needed
        )

        return session.execute(stmt).scalars().first()

    # ---------- admin reads ----------

    def get_product_by_id(
        self,
        session: Session,
        *,
        product_id: int,
        include_images: bool = True,
    ) -> Optional[Product]:
        """
        Admin fetch: returns product even if inactive or soft-deleted.
        """
        stmt = select(Product).where(Product.id == product_id)

        if include_images:
            stmt = stmt.options(selectinload(Product.images))  # adjust relationship name if needed

        return session.execute(stmt).scalars().first()
