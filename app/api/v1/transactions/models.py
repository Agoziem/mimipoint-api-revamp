from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from enum import Enum
from datetime import datetime, timezone
import uuid

from sqlalchemy import String, Numeric, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
if TYPE_CHECKING:
    from app.api.v1.auth.models import User


# Enums
class TransactionType(str, Enum):
    AIRTIME = "airtime"
    DATA = "data"
    BILL = "bill"
    CABLE = "cable"
    TOPUP = "topup"
    SUBSCRIPTION = "subscription"
    EXCHANGE = "exchange"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class WalletType(str, Enum):
    DOLLAR = "dollar"
    NAIRA = "naira"
    EURO = "euro"


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    wallet_type: Mapped[str] = mapped_column(String(20), default=WalletType.NAIRA.value)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)

    user: Mapped["User"] = relationship("User", back_populates="wallets")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="wallet", passive_deletes=True)

    def deposit(self, amount: float):
        """Deposit an amount into the wallet."""
        self.balance += Decimal(amount)
        

    def withdraw(self, amount: float) -> bool:
        """Withdraw an amount from the wallet if sufficient balance exists."""
        if self.balance >= Decimal(amount):
            self.balance -= Decimal(amount)
            return True
        return False


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    wallet_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="SET NULL"))
    transaction_type: Mapped[str] = mapped_column(String(10))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(10), default=TransactionStatus.PENDING.value)
    reference: Mapped[str] = mapped_column(String(100), unique=True)
    provider_response: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="transactions", passive_deletes=True)
    wallet: Mapped[Optional["Wallet"]] = relationship("Wallet", back_populates="transactions", passive_deletes=True)

    def generate_payment_ref(self):
        self.reference = f"Payment--{uuid.uuid4().hex[:11]}"
        return self
