from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Sequence, Tuple

from sqlalchemy import Select, delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.infrastructure.db.models import (
    Product,
    ProductImage,
    Order,
    OrderItem,
)


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
        stmt = (
            select(Product)
            .where(*self._public_visibility_filter())
            .where(Product.slug == slug)
            .options(selectinload(Product.images))
        )

        return session.execute(stmt).scalars().first()

    # ---------- admin reads ----------

    def list_admin_products(
        self,
        session: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False,
    ) -> Tuple[Sequence[Product], int]:
        paging = Page(page=page, page_size=page_size)

        base_stmt = select(Product).order_by(Product.created_at.desc(), Product.id.desc())

        if not include_deleted:
            base_stmt = base_stmt.where(Product.deleted_at.is_(None))

        if is_active is not None:
            base_stmt = base_stmt.where(Product.is_active.is_(is_active))

        base_stmt = self._apply_filters(
            base_stmt,
            category=category,
            min_price=min_price,
            max_price=max_price,
            search=search,
        )

        count_stmt = select(func.count()).select_from(Product)

        if not include_deleted:
            count_stmt = count_stmt.where(Product.deleted_at.is_(None))

        if is_active is not None:
            count_stmt = count_stmt.where(Product.is_active.is_(is_active))

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

    def get_product_by_id(
        self,
        session: Session,
        *,
        product_id: int,
        include_images: bool = True,
    ) -> Optional[Product]:
        stmt = select(Product).where(Product.id == product_id)

        if include_images:
            stmt = stmt.options(selectinload(Product.images))

        return session.execute(stmt).scalars().first()

    def get_product_by_slug_any(
        self,
        session: Session,
        *,
        slug: str,
    ) -> Optional[Product]:
        stmt = select(Product).where(Product.slug == slug)
        return session.execute(stmt).scalars().first()

    # ---------- admin writes ----------

    def create_product(
        self,
        session: Session,
        *,
        slug: str,
        name: str,
        description: Optional[str],
        price: int,
        category: str,
        quantity: int,
        thumbnail_url: str,
        is_active: bool,
        image_urls: Sequence[str],
    ) -> Product:
        product = Product(
            slug=slug,
            name=name,
            description=description,
            price=price,
            category=category,
            quantity=quantity,
            thumbnail_url=thumbnail_url,
            is_active=is_active,
        )
        session.add(product)
        session.flush()

        for idx, url in enumerate(image_urls):
            session.add(
                ProductImage(
                    product_id=product.id,
                    url=url,
                    position=idx,
                )
            )

        session.flush()
        return product

    def replace_product_images(
        self,
        session: Session,
        *,
        product_id: int,
        image_urls: Sequence[str],
    ) -> None:
        session.execute(delete(ProductImage).where(ProductImage.product_id == product_id))

        for idx, url in enumerate(image_urls):
            session.add(
                ProductImage(
                    product_id=product_id,
                    url=url,
                    position=idx,
                )
            )

        session.flush()

    def update_product(
        self,
        session: Session,
        *,
        product: Product,
        slug: str,
        name: str,
        description: Optional[str],
        price: int,
        category: str,
        quantity: int,
        thumbnail_url: str,
        is_active: bool,
        image_urls: Sequence[str],
    ) -> Product:
        product.slug = slug
        product.name = name
        product.description = description
        product.price = price
        product.category = category
        product.quantity = quantity
        product.thumbnail_url = thumbnail_url
        product.is_active = is_active

        session.add(product)
        session.flush()

        self.replace_product_images(session, product_id=product.id, image_urls=image_urls)
        return product

    def set_product_active(
        self,
        session: Session,
        *,
        product: Product,
        is_active: bool,
    ) -> Product:
        product.is_active = is_active
        session.add(product)
        session.flush()
        return product

    def soft_delete_product(
        self,
        session: Session,
        *,
        product: Product,
    ) -> Product:
        """
        Soft delete product by setting deleted_at.
        Idempotent: if already deleted, keep it.
        Does NOT commit.
        """
        if product.deleted_at is None:
            product.deleted_at = datetime.now(timezone.utc)
            session.add(product)
            session.flush()
        return product


class OrdersRepository:
    """
    DB access only for orders.
    - No FastAPI / HTTP
    - No unified responses
    - Session is injected
    """

    # ---------- helpers ----------

    def get_active_products_by_ids(
        self,
        session: Session,
        *,
        product_ids: Sequence[int],
    ) -> Sequence[Product]:
        """
        Returns purchasable products (active + not deleted) matching product_ids.
        NOTE: service layer will validate missing ids and quantities.
        """
        if not product_ids:
            return []

        stmt = (
            select(Product)
            .where(Product.id.in_(list(product_ids)))
            .where(Product.is_active.is_(True))
            .where(Product.deleted_at.is_(None))
        )
        return session.execute(stmt).scalars().all()

    # ---------- writes ----------

    def create_order(
        self,
        session: Session,
        *,
        order: Order,
        items: Sequence[OrderItem],
    ) -> Order:
        """
        Adds order + items to the session and flushes.
        Does NOT commit.
        """
        session.add(order)
        session.flush()  # ensures order.id is available

        for item in items:
            item.order_id = order.id
            session.add(item)

        session.flush()
        return order

    def update_order_status(
        self,
        session: Session,
        *,
        order: Order,
        status: str,
    ) -> Order:
        order.status = status
        session.add(order)
        session.flush()
        return order

    def set_sheets_sync_result(
        self,
        session: Session,
        *,
        order: Order,
        status: str,  # "SUCCESS" | "FAILED" | "PENDING"
        error: str | None = None,
    ) -> Order:
        """
        Updates sheets sync fields.
        IMPORTANT: does NOT commit (keeps repo contract). Flush only.
        """
        order.sheets_status = status

        if status == "SUCCESS":
            order.sheets_synced_at = datetime.now(timezone.utc)
            order.sheets_error = None
        elif status == "FAILED":
            order.sheets_synced_at = None
            order.sheets_error = (error or "Unknown sheets error")[:500]
        else:
            order.sheets_synced_at = None
            order.sheets_error = None

        session.add(order)
        session.flush()
        return order

    # ---------- reads ----------

    def get_order_by_id(
        self,
        session: Session,
        *,
        order_id: int,
        include_items: bool = True,
    ) -> Optional[Order]:
        stmt = select(Order).where(Order.id == order_id)

        if include_items:
            stmt = stmt.options(selectinload(Order.items))

        return session.execute(stmt).scalars().first()

    def list_orders(
        self,
        session: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        phone_number: Optional[str] = None,
    ) -> Tuple[Sequence[Order], int]:
        paging = Page(page=page, page_size=page_size)

        base_stmt = select(Order).order_by(Order.created_at.desc(), Order.id.desc())

        if status:
            base_stmt = base_stmt.where(Order.status == status)

        if phone_number:
            pattern = f"%{phone_number.strip()}%"
            base_stmt = base_stmt.where(Order.phone_number.ilike(pattern))

        count_stmt = select(func.count()).select_from(Order)

        if status:
            count_stmt = count_stmt.where(Order.status == status)

        if phone_number:
            pattern = f"%{phone_number.strip()}%"
            count_stmt = count_stmt.where(Order.phone_number.ilike(pattern))

        total: int = session.execute(count_stmt).scalar_one()

        items_stmt = base_stmt.limit(paging.page_size).offset(paging.offset)
        items = session.execute(items_stmt).scalars().all()
        return items, total
