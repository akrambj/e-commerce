from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from sqlalchemy import (
    DateTime,
    func,
    Integer,
    String,
    Text,
    Boolean,
    CheckConstraint,
    Index,
    ForeignKey,
    UniqueConstraint
)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )



class Product(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    slug: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    price: Mapped[int] = mapped_column(Integer, nullable=False)

    category: Mapped[str] = mapped_column(String(80), nullable=False, default="uncategorized")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_products_price_non_negative"),
        CheckConstraint("quantity >= 0", name="ck_products_quantity_non_negative"),
        Index("ix_products_category", "category"),
        Index("ix_products_price", "price"),
        Index("ix_products_is_active", "is_active"),
        Index("ix_products_deleted_at", "deleted_at"),    
        )


class ProductImage(Base, TimestampMixin):
    __tablename__= "product_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )

    url: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    product: Mapped[Product] = relationship(back_populates="images")

    __table_args__ = (
        UniqueConstraint("product_id", "url", name="uq_product_images_product_id_url"),
        Index("ix_product_images_product_id", "product_id")
    )

class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # status lifecycle (v1)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")

    # customer info (guest)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)

    # location + delivery
    wilaya: Mapped[str] = mapped_column(String(80), nullable=False)
    baladiya: Mapped[str] = mapped_column(String(120), nullable=False)
    delivery_mode: Mapped[str] = mapped_column(String(20), nullable=False)  # HOME | STOP_DESK
    address_line: Mapped[str | None] = mapped_column(Text, nullable=True)

    # totals (DZD integers)
    items_subtotal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delivery_fee: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # google sheets sync (v1 direct integration)
    sheets_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    sheets_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sheets_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("items_subtotal >= 0", name="ck_orders_items_subtotal_non_negative"),
        CheckConstraint("delivery_fee >= 0", name="ck_orders_delivery_fee_non_negative"),
        CheckConstraint("total_amount >= 0", name="ck_orders_total_amount_non_negative"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_created_at", "created_at"),
        Index("ix_orders_phone_number", "phone_number"),
    )


class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # snapshot fields
    product_slug: Mapped[str] = mapped_column(String(150), nullable=False)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)

    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")

    __table_args__ = (
        CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_non_negative"),
        CheckConstraint("quantity >= 1", name="ck_order_items_quantity_positive"),
        CheckConstraint("line_total >= 0", name="ck_order_items_line_total_non_negative"),
        Index("ix_order_items_order_id", "order_id"),
        Index("ix_order_items_product_id", "product_id"),
    )
