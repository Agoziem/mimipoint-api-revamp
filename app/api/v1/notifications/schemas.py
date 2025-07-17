from pydantic import BaseModel, UUID4, field_serializer
from datetime import datetime
from typing import List, Optional
from uuid import UUID


# -----------------------------
# 🔹 Base Notification Schemas
# -----------------------------

class NotificationBase(BaseModel):
    sender_id: UUID4 | None = None
    title: str
    message: str
    link: str | None = None
    image: Optional[str] = None

    @field_serializer("sender_id")
    def serialize_sender_id(self, value: UUID4 | None) -> str | None:
        return str(value) if value else None

    @field_serializer("link")
    def serialize_link(self, value: str | None) -> str | None:
        return value if value else None


# -----------------------------
# 🔹 Input Schemas
# -----------------------------

class NotificationCreate(NotificationBase):
    user_ids: List[UUID] = []

    @field_serializer("user_ids")
    def serialize_user_ids(self, value: List[UUID]) -> List[str]:
        return [str(user_id) for user_id in value]


class NotificationUpdate(BaseModel):
    id: UUID4
    sender_id: UUID4 | None = None
    title: str | None = None
    message: str | None = None
    link: str | None = None
    image: Optional[str] = None

    user_ids: List[UUID] = []

    @field_serializer("id")
    def serialize_id(self, value: UUID4) -> str:
        return str(value)


class NotificationReadUpdate(BaseModel):
    notification_id: UUID4
    user_id: UUID4
    is_read: bool

    @field_serializer("notification_id")
    def serialize_notification_id(self, value: UUID4) -> str:
        return str(value)

    @field_serializer("user_id")
    def serialize_user_id(self, value: UUID4) -> str:
        return str(value)


class RemoveUpdate(BaseModel):
    notification_id: UUID4
    user_id: UUID4

    @field_serializer("notification_id")
    def serialize_notification_id(self, value: UUID4) -> str:
        return str(value)

    @field_serializer("user_id")
    def serialize_user_id(self, value: UUID4) -> str:
        return str(value)


# -----------------------------
# 🔹 Output Schemas (with is_read via association)
# -----------------------------

class NotificationUserResponse(BaseModel):
    """User info in the context of a notification + read status"""
    id: UUID4
    first_name: str
    last_name: str
    image_url: str | None
    has_read: bool  # From NotificationRecipient.is_read

    @field_serializer("id")
    def serialize_id(self, value: UUID4) -> str:
        return str(value)
    

class NotificationOnlyResponse(NotificationBase):
    """Notification without recipient details"""
    id: UUID4
    created_at: datetime

    @field_serializer("id")
    def serialize_id(self, value: UUID4) -> str:
        return str(value)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()


class NotificationResponse(NotificationBase):
    id: UUID4
    created_at: datetime
    recipients: List[NotificationUserResponse]

    @field_serializer("id")
    def serialize_id(self, value: UUID4) -> str:
        return str(value)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()

