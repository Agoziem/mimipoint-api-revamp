import re
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from enum import Enum
import uuid
from annotated_types import T
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Text, Numeric, Integer, DateTime, ForeignKey, JSON,Enum as SQLEnum

from app.core.database import Base
if TYPE_CHECKING:
    from app.api.v1.auth.models import User  # Avoid circular import


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"

class BillingCycleEnum(str, Enum):
    MONTHLY = "monthly"
    ANNUALLY = "annually"

class BillingCategoryEnum(str, Enum):
    STANDARD = "standard"
    PREMIUM = "premium"

class ProductCategoryEnum(str, Enum):
    ELECTRONICS = "electronics"
    FASHION = "fashion"
    HOME_APPLIANCES = "home_appliances"
    BOOKS = "books"
    BEAUTY = "beauty"
    SPORTS = "sports"
    GROCERIES = "groceries"
    TOYS = "toys"
    AUTOMOTIVE = "automotive"
    HEALTH = "health"
    PET_SUPPLIES = "pet_supplies"
    BABY_PRODUCTS = "baby_products"
    FURNITURE = "furniture"
    STATIONERY = "stationery"
    GAMING = "gaming"
    MUSICAL_INSTRUMENTS = "musical_instruments"
    SOFTWARE = "software"


class EasybuyPlan(Base):
    __tablename__ = "easybuy_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    no_of_products: Mapped[int] = mapped_column(Integer)
    billing_cycle: Mapped[BillingCycleEnum] = mapped_column(SQLEnum(BillingCycleEnum), default=BillingCycleEnum.MONTHLY, nullable=False)
    billing_category: Mapped[BillingCategoryEnum] = mapped_column(SQLEnum(BillingCategoryEnum), nullable=False, default=BillingCategoryEnum.STANDARD)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    subscriptions: Mapped[List["EasybuySubscription"]] = relationship(
        "EasybuySubscription",
        back_populates="plan", cascade="all, delete-orphan", passive_deletes=True
    )


class EasybuySubscription(Base):
    __tablename__ = "easybuy_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("easybuy_plans.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(50), default=SubscriptionStatus.ACTIVE.value)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="subscription", passive_deletes=True)
    plan: Mapped["EasybuyPlan"] = relationship("EasybuyPlan", back_populates="subscriptions", passive_deletes=True)
 

class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(Integer)
    image: Mapped[str] = mapped_column(String)  # URL to image
    category: Mapped[ProductCategoryEnum] = mapped_column(SQLEnum(ProductCategoryEnum), nullable=True)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    redirect_link: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    owner: Mapped["User"] = relationship("User", back_populates="products", passive_deletes=True)
    reviews: Mapped[List["ProductReview"]] = relationship(
        "ProductReview",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class ProductReview(Base):
    __tablename__ = "product_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    product: Mapped["Product"] = relationship("Product", back_populates="reviews", passive_deletes=True)
    user: Mapped["User"] = relationship("User", back_populates="reviews", passive_deletes=True)
