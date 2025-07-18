from app.api.v1.auth.models import User
from app.core.config import settings
from passlib.context import CryptContext
import logging
import uuid
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer
import jwt as pyjwt


passwd_context = CryptContext(schemes=["bcrypt"])

ACCESS_TOKEN_EXPIRY = settings.ACCESS_TOKEN_EXPIRY
REFRESH_TOKEN_EXPIRY = settings.REFRESH_TOKEN_EXPIRY


def generate_passwd_hash(password: str) -> str:
    hash = passwd_context.hash(password)
    return hash


def verify_password(password: str, hash: str) -> bool:
    return passwd_context.verify(password, hash)


def create_access_token(
    user_data: dict, expiry: timedelta = timedelta(seconds=ACCESS_TOKEN_EXPIRY), refresh: bool = False
):
    payload = {}

    payload["user"] = user_data
    payload["exp"] = datetime.now() + (
        expiry if expiry is not None else timedelta(
            seconds=ACCESS_TOKEN_EXPIRY)
    )
    payload["jti"] = str(uuid.uuid4())

    payload["refresh"] = refresh

    token = pyjwt.encode(
        payload=payload, key=settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )

    return token


def decode_token(token: str) -> dict | None:
    try:
        token_data = pyjwt.decode(
            jwt=token, key=settings.JWT_SECRET, algorithms=[
                settings.JWT_ALGORITHM]
        )

        return token_data

    except pyjwt.PyJWTError as e:
        logging.exception(e)
        return None


serializer = URLSafeTimedSerializer(
    secret_key=settings.JWT_SECRET, salt="email-configuration"
)


def create_url_safe_token(data: dict):

    token = serializer.dumps(data)

    return token


def decode_url_safe_token(token: str):
    try:
        token_data = serializer.loads(token)

        return token_data

    except Exception as e:
        logging.error(str(e))


def create_auth_tokens(user: User):
    access_token = create_access_token({
        "email": user.email,
        "id": str(user.id),
        "role": user.role,
    })

    refresh_token = create_access_token(
        {"email": user.email, "id": str(user.id)},
        refresh=True,
        expiry=timedelta(days=REFRESH_TOKEN_EXPIRY),
    )

    return access_token, refresh_token
