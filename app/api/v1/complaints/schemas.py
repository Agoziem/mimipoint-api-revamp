from pydantic import BaseModel, UUID4,field_serializer
from typing import Optional
from datetime import datetime


class ComplaintBase(BaseModel):
    """Base schema for Complaint model"""
    user_id: UUID4
    transaction_id: Optional[str] = None
    complaint: Optional[str] = None

class ComplaintCreate(ComplaintBase):
    """Schema for creating a new Complaint"""
    pass

class ComplaintResponse(ComplaintBase):
    """Schema for returning Complaint details"""
    id: UUID4
    created_at: datetime

    @field_serializer("id")
    def serialize_uuid(self, value: UUID4) -> str:
        return str(value)
    
    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()

    class Config:
        from_attributes = True
