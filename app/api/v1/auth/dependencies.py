from typing import Any, List
from fastapi import Depends, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.auth.errors import raise_access_token_required_exception, raise_account_not_verified_exception, raise_insufficient_permission_exception, raise_invalid_token_exception, raise_refresh_token_required_exception
from app.core.database import async_get_db
from .models import User
from app.core.redis import token_in_blocklist
from .services.service import UserService
from .utils import decode_token
from uuid import UUID

user_service = UserService()


class TokenBearer(HTTPBearer):
    def __init__(self, auto_error=True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> dict | None:
        creds = await super().__call__(request)
        if not creds:
            return None
        token = creds.credentials
        token_data = decode_token(token)
        if not token_data:
            raise raise_invalid_token_exception()
        if not self.token_valid(token):
            raise raise_invalid_token_exception()
        if await token_in_blocklist(token_data["jti"]):
            raise raise_invalid_token_exception()
        self.verify_token_data(token_data)
        return token_data 

    def token_valid(self, token: str) -> bool:
        token_data = decode_token(token)
        return token_data is not None

    def verify_token_data(self, token_data):
        raise NotImplementedError(
            "Please Override this method in child classes")


class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and token_data["refresh"]:
            raise raise_access_token_required_exception()


class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and not token_data["refresh"]:
            raise raise_refresh_token_required_exception()


async def get_current_user(
    token_details: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(async_get_db),
):
    user_id = UUID(token_details["user"]["id"])  # Convert to UUID
    user = await user_service.get_user_by_id(user_id, session)
    return user


class RoleChecker:
    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> Any:
        if not current_user.is_verified:
            raise raise_account_not_verified_exception()
        if current_user.role in self.allowed_roles:
            return True

        raise raise_insufficient_permission_exception()


