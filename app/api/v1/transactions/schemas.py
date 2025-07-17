from pydantic import BaseModel, UUID4, Field,field_serializer
from datetime import datetime
from typing import Optional
from .models import TransactionType, WalletType

class WalletBase(BaseModel):
    """Base schema for Wallet model"""
    user_id: UUID4
    balance: float = 0.00
    wallet_type: WalletType = WalletType.NAIRA

class WalletCreate(WalletBase):
    """Schema for creating a new Wallet"""

    @field_serializer("wallet_type")
    def serialize_wallet_type(self, value: str) -> str:
        return value.lower()
    
class WalletUpdate(BaseModel):
    """Schema for updating an existing Wallet"""
    id: UUID4
    amount: Optional[float] = Field(None, gt=0)

    @field_serializer("amount")
    def serialize_balance(self, value: Optional[float]) -> Optional[float]:
        return value if value is not None else None
    
    @field_serializer("id")
    def serialize_uuid(self, value: UUID4) -> str:
        return str(value)
    

class WalletResponse(WalletBase):
    """Schema for returning Wallet details"""
    id: UUID4

    class Config:
        from_attributes = True

    @field_serializer("id")
    def serialize_uuid(self, value: UUID4) -> str:
        return str(value)
    

# Transaction schemas

class TransactionBase(BaseModel):
    """Base schema for Transaction model"""
    user_id: UUID4
    wallet_id: Optional[UUID4] = None
    transaction_type: TransactionType = TransactionType.TOPUP
    amount: float
    status: str = "pending"
    provider_response: Optional[dict] = None

    @field_serializer("wallet_id")
    def serialize_wallet_id(self, value: Optional[UUID4]) -> Optional[str]:
        return str(value) if value else None
    
class TransactionCreate(TransactionBase):
    """Schema for creating a new Transaction"""

    @field_serializer("transaction_type")
    def serialize_transaction_type(self, value: str) -> str:
        return value.lower()
    

class TransactionResponse(TransactionBase):
    """Schema for returning Transaction details"""
    id: UUID4
    reference: str
    created_at: datetime

    class Config:
        from_attributes = True

    @field_serializer("id")
    def serialize_uuid(self, value: UUID4) -> str:
        return str(value)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()
