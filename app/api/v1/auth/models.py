from enum import Enum
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base
if TYPE_CHECKING:
    from app.api.v1.notifications.models import Notification, NotificationRecipient


class Role(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"


class ActivityType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[Optional[str]]
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]]
    address: Mapped[Optional[str]]
    state: Mapped[Optional[str]]
    country: Mapped[Optional[str]]
    password_hash: Mapped[Optional[str]]
    avatar: Mapped[Optional[str]]
    bio: Mapped[Optional[str]]
    gender: Mapped[Optional[str]]
    role: Mapped[str] = mapped_column(default=Role.CUSTOMER.value)
    fcm_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    two_factor_enabled: Mapped[bool] = mapped_column(default=False)
    is_oauth: Mapped[bool] = mapped_column(default=False)
    login_provider: Mapped[Optional[str]] = mapped_column(default="email")
    profile_completed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    activities: Mapped[List["Activity"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    two_factor_confirmation: Mapped[Optional["TwoFactorConfirmation"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    sent_notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="sender", passive_deletes=True
    )
    notification_associations: Mapped[List["NotificationRecipient"]] = relationship(
        "NotificationRecipient", back_populates="user", cascade="all, delete-orphan"
    )
    wallets = relationship("Wallet", back_populates="user", passive_deletes=True)
    transactions = relationship("Transaction", back_populates="user", passive_deletes=True)
    subscription = relationship("EasybuySubscription", back_populates="user", uselist=False, passive_deletes=True)
    products = relationship("Product", back_populates="owner", passive_deletes=True)
    complaints = relationship("Complaint", back_populates="user", passive_deletes=True)
    reviews = relationship("ProductReview", back_populates="user", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<User {self.first_name} {self.last_name}>"


class VerificationToken(Base):
    __tablename__ = "verification_token"
    __table_args__ = (UniqueConstraint("email", "token", name="uq_verification_email_token"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    expires: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PasswordResetToken(Base):
    __tablename__ = "password_reset_token"
    __table_args__ = (UniqueConstraint("email", "token", name="uq_password_email_token"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    expires: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TwoFactorToken(Base):
    __tablename__ = "two_factor_token"
    __table_args__ = (UniqueConstraint("email", "token", name="uq_2fa_email_token"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    expires: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TwoFactorConfirmation(Base):
    __tablename__ = "two_factor_confirmation"
    __table_args__ = (UniqueConstraint("user_id", name="uq_2fa_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="two_factor_confirmation")


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description: Mapped[str] = mapped_column(String, nullable=False)
    activity_type: Mapped[str] = mapped_column(default=ActivityType.CREATE.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="activities")
