from typing import List, Optional, TYPE_CHECKING
import uuid
from datetime import datetime, timezone
from sqlalchemy import Table, Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
if TYPE_CHECKING:
    from app.api.v1.auth.models import User  # Avoid circular import


class NotificationRecipient(Base):
    __tablename__ = "notification_recipients"

    notification_id:Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    notification : Mapped["Notification"] = relationship("Notification", back_populates="recipient_associations")
    user: Mapped["User"] = relationship("User", back_populates="notification_associations")



class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    link: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Optional link for the notification
    image: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Optional image for the notification
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    sender: Mapped[Optional["User"]] = relationship("User", back_populates="sent_notifications", passive_deletes=True)
    recipient_associations: Mapped[List["NotificationRecipient"]] = relationship(
        "NotificationRecipient", back_populates="notification", cascade="all, delete-orphan"
    )
