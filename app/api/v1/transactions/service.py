from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.v1.transactions.Paystack import Paystack
from app.api.v1.transactions.schemas import TransactionCreate, WalletCreate
from .models import Transaction, TransactionStatus, Wallet
from sqlalchemy import desc


class WalletService:
    async def create_wallet(self, wallet_data: WalletCreate, session: AsyncSession) -> Wallet:
        wallet_data_dict = wallet_data.model_dump()
        new_wallet = Wallet(**wallet_data_dict)
        session.add(new_wallet)
        await session.commit()
        await session.refresh(new_wallet)
        return new_wallet

    async def get_wallets(self, user_id: UUID, session: AsyncSession) -> List[Wallet]:
        statement = select(Wallet).where(Wallet.user_id == user_id)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_wallet_by_type(self, user_id: UUID, wallet_type: str, session: AsyncSession) -> List[Wallet]:
        statement = select(Wallet).where(
            Wallet.user_id == user_id, Wallet.wallet_type == wallet_type)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_wallet_by_id(self, wallet_id: UUID, session: AsyncSession) -> Wallet:
        statement = select(Wallet).where(Wallet.id == wallet_id)
        result = await session.execute(statement)
        return result.scalars().first()

    async def withdraw(self, wallet_id: UUID, amount: float, session: AsyncSession) -> Optional[Wallet]:
        wallet = await self.get_wallet_by_id(wallet_id, session)
        if wallet and wallet.withdraw(amount):
            await session.commit()
            await session.refresh(wallet)
            return wallet
        return None

    async def deposit(self, wallet_id: UUID, amount: float, session: AsyncSession) -> Optional[Wallet]:
        wallet = await self.get_wallet_by_id(wallet_id, session)
        if wallet:
            wallet.deposit(amount)
            await session.commit()
            await session.refresh(wallet)
            return wallet
        return None

    async def delete_wallet(self, wallet_id: UUID, session: AsyncSession) -> bool:
        wallet = await self.get_wallet_by_id(wallet_id, session)
        if wallet:
            await session.delete(wallet)
            await session.commit()
            return True
        return False


class TransactionService:
    async def get_transaction_by_id(self, transaction_id: UUID, session: AsyncSession) -> Transaction:
        statement = select(Transaction).where(Transaction.id == transaction_id)
        result = await session.execute(statement)
        return result.scalars().first()

    async def get_transaction_by_reference(self, reference: str, session: AsyncSession) -> Transaction:
        statement = select(Transaction).where(
            Transaction.reference == reference)
        result = await session.execute(statement)
        return result.scalars().first()

    async def get_all_transactions(self, session: AsyncSession, limit: int = 100, offset: int = 0) -> List[Transaction]:
        statement = select(Transaction).order_by(desc(Transaction.created_at)).limit(limit).offset(offset)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_transactions(self, user_id: UUID, session: AsyncSession) -> List[Transaction]:
        statement = select(Transaction).where(Transaction.user_id == user_id).order_by(desc(Transaction.created_at))
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def create_transaction(self, transaction_data: TransactionCreate, session: AsyncSession) -> Transaction:
        transaction_data_dict = transaction_data.model_dump()
        new_transaction = Transaction(**transaction_data_dict)
        new_transaction.generate_payment_ref()
        session.add(new_transaction)
        await session.commit()
        await session.refresh(new_transaction)
        return new_transaction

    async def verify_transaction(self, reference: str, session: AsyncSession) -> Optional[Transaction]:
        paystack = Paystack()
        status, data = paystack.verify_payment(reference)
        if status:
            transaction = await self.get_transaction_by_reference(reference, session)
            if transaction:
                transaction.status = TransactionStatus.SUCCESS
                await session.commit()
                await session.refresh(transaction)
                return transaction
        return None

    async def delete_transaction(self, transaction_id: UUID, session: AsyncSession) -> bool:
        transaction = await self.get_transaction_by_id(transaction_id, session)
        if transaction:
            await session.delete(transaction)
            await session.commit()
            return True
        return False
