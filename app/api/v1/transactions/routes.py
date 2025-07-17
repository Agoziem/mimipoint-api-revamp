from hmac import new
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.auth.schemas.schemas import UserResponseModel as UserResponse
from app.api.v1.auth.services.service import ActivityService
from app.api.v1.transactions.schemas import TransactionCreate, TransactionResponse, WalletCreate, WalletResponse, WalletUpdate
from app.api.v1.transactions.service import WalletService, TransactionService
from app.core.database import async_get_db
from typing import List, Optional
from uuid import UUID

wallet_router = APIRouter()
wallet_service = WalletService()
transaction_router = APIRouter()
transaction_service = TransactionService()
activity_service = ActivityService()

# ------- Wallet Routes ------


@wallet_router.get("/", response_model=List[WalletResponse], status_code=status.HTTP_200_OK)
async def get_wallets(
    wallet_type: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db)
):
    """Get all wallets for a user"""
    if wallet_type:
        wallets = await wallet_service.get_wallet_by_type(user_id=current_user.id, wallet_type=wallet_type, session=session)
    else:
        wallets = await wallet_service.get_wallets(user_id=current_user.id, session=session)

    if not wallets:
        wallet_data = WalletCreate(user_id=current_user.id)
        new_wallet = await wallet_service.create_wallet(wallet_data=wallet_data, session=session)
        if not new_wallet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet creation failed")
        await activity_service.create_user_activity(
            user_id=current_user.id,
            activity_type="create",
            description=f"Created wallet with ID: {new_wallet.id}",
            session=session
        )
        return [new_wallet]
    return wallets


@wallet_router.get("/{wallet_id}", response_model=WalletResponse, status_code=status.HTTP_200_OK)
async def get_wallet(
    wallet_id: UUID,
    _: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db)
):
    """Get a single wallet by ID"""
    wallet = await wallet_service.get_wallet_by_id(wallet_id=wallet_id, session=session)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    return wallet


@wallet_router.delete("/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wallet(
    wallet_id: UUID,
    _: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db)
):
    """Delete a wallet by ID"""
    deleted = await wallet_service.delete_wallet(wallet_id=wallet_id, session=session)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    await activity_service.create_user_activity(
        user_id=_.id,
        activity_type="delete",
        description=f"Deleted wallet with ID: {wallet_id}",
        session=session
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@wallet_router.post("/", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(
    wallet_data: WalletCreate,
    _: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db)
):
    """Create a new wallet"""
    new_wallet = await wallet_service.create_wallet(wallet_data=wallet_data, session=session)
    if not new_wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet creation failed")
    await activity_service.create_user_activity(
        user_id=_.id,
        activity_type="create",
        description=f"Created wallet with ID: {new_wallet.id}",
        session=session
    )
    return new_wallet

@wallet_router.put("/deposit", response_model=WalletResponse, status_code=status.HTTP_200_OK)
async def deposit_to_wallet(
    wallet_data: WalletUpdate,
    _: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db)
):
    """Deposit an amount to a wallet"""
    if not wallet_data.amount or wallet_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be greater than zero")
    
    wallet = await wallet_service.deposit(wallet_id=wallet_data.id, amount=wallet_data.amount, session=session)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet deposit failed")
    
    await activity_service.create_user_activity(
        user_id=_.id,
        activity_type="create",
        description=f"Deposited {wallet_data.amount} to wallet ID: {wallet.id}",
        session=session
    )
    return wallet

@wallet_router.put("/withdraw", response_model=WalletResponse, status_code=status.HTTP_200_OK)
async def withdraw_from_wallet(
    wallet_data: WalletUpdate,
    _: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db)
):
    """Withdraw an amount from a wallet"""
    if not wallet_data.amount or wallet_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be greater than zero")
    
    wallet = await wallet_service.withdraw(wallet_id=wallet_data.id, amount=wallet_data.amount, session=session)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds")
    
    await activity_service.create_user_activity(
        user_id=_.id,
        activity_type="update",
        description=f"Withdrew {wallet_data.amount} from wallet ID: {wallet.id}",
        session=session
    )
    return wallet



# ------- Transaction Routes ------

@transaction_router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    _: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db)
):
    """Create a new transaction"""
    transaction = await transaction_service.create_transaction(transaction_data=transaction_data, session=session)

    if not transaction:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Transaction creation failed")

    # Withdraw or deposit based on transaction type
    if transaction.transaction_type in ["airtime", "data", "bill", "cable"]:
        if not transaction.wallet_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet ID is required for this transaction type")
        wallet = await wallet_service.withdraw(wallet_id=transaction.wallet_id, amount=transaction.amount, session=session)
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds")
        await activity_service.create_user_activity(
            user_id=_.id,
            activity_type="update",
            description=f"Withdrew {transaction.amount} from wallet ID: {transaction.wallet_id}",
            session=session
        )
    return transaction

# get all the transactions for the admin


@transaction_router.get("/admin", response_model=List[TransactionResponse], status_code=status.HTTP_200_OK)
async def get_all_transactions(
    session: AsyncSession = Depends(async_get_db),
    _: UserResponse = Depends(get_current_user),
    Limit: int = 100,
    Offset: int = 0
):
    """Get all transactions for admin"""
    transactions = await transaction_service.get_all_transactions(session=session, limit=Limit, offset=Offset)
    return transactions


@transaction_router.get("/", response_model=List[TransactionResponse], status_code=status.HTTP_200_OK)
async def get_transactions(
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db)
):
    """Get all transactions for a user"""
    transactions = await transaction_service.get_transactions(user_id=current_user.id, session=session)
    return transactions


@transaction_router.get("/{transaction_id}", response_model=TransactionResponse, status_code=status.HTTP_200_OK)
async def get_transaction(
    transaction_id: UUID,
    _: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db)
):
    """Get a single transaction by ID"""
    transaction = await transaction_service.get_transaction_by_id(transaction_id=transaction_id, session=session)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction


@transaction_router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: UUID,
    _: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db)
):
    """Delete a transaction by ID"""
    deleted = await transaction_service.delete_transaction(transaction_id=transaction_id, session=session)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    await activity_service.create_user_activity(
        user_id=_.id,
        activity_type="delete",
        description=f"Deleted transaction with ID: {transaction_id}",
        session=session
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@transaction_router.get("/verify/{transaction_ref}", response_model=TransactionResponse, status_code=status.HTTP_200_OK)
async def verify_transaction(
    transaction_ref: str,
    _: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db)
):
    """Verify a transaction by reference"""
    transaction = await transaction_service.verify_transaction(reference=transaction_ref, session=session)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if not transaction.wallet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet ID is required for this transaction type")
    if transaction.transaction_type == "topup":
        wallet = await wallet_service.deposit(wallet_id=transaction.wallet_id, amount=transaction.amount, session=session)
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet deposit failed")
        await activity_service.create_user_activity(
            user_id=_.id,
            activity_type="create",
            description=f"Deposited {transaction.amount} to wallet ID: {transaction.wallet_id}",
            session=session
        )
    elif transaction.transaction_type in ["subscription", "exchange"]:
        wallet = await wallet_service.withdraw(wallet_id=transaction.wallet_id, amount=transaction.amount, session=session)
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds")
        await activity_service.create_user_activity(
            user_id=_.id,
            activity_type="create",
            description=f"Withdrew {transaction.amount} from wallet ID: {transaction.wallet_id}",
            session=session
        )
    
    return transaction
