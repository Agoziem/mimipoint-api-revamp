from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Depends, status
from authlib.integrations.base_client import BaseApp
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.auth.errors import raise_invalid_credentials_exception, raise_user_not_found_exception
from app.api.v1.auth.services.token_service import TokenService
from app.core.database import async_get_db
from app.core.redis import add_oauth_code_to_blocklist, oauth_code_in_blocklist
from ..schemas.schemas import (
    GoogleUserCreateModel
)
from ..services.service import UserService
from ..utils import (
    create_auth_tokens,

)
from app.core.config import settings
from starlette.requests import Request
import uuid
from uuid import UUID
from fastapi.background import BackgroundTasks
from app.core.mail import EmailRawHTMLContent, EmailRecipient, send_html_email
from app.core.templates import templates

oauth_router = APIRouter()
user_service = UserService()
token_service = TokenService()

REFRESH_TOKEN_EXPIRY = settings.REFRESH_TOKEN_EXPIRY


oauth = OAuth()

oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
    }
)


# ------------------------------------------------
# OAuth Routes
# ------------------------------------------------

@oauth_router.get("/login/google")
async def login_via_google(request: Request):
    redirect_uri = settings.GOOGLE_REDIRECT_URL
    if oauth.google:
        return await oauth.google.authorize_redirect(request, redirect_uri)
    raise HTTPException(status_code=500, detail="Google OAuth is not configured")


@oauth_router.get("/callback/google")
async def auth_via_google(
    request: Request,
    session: AsyncSession = Depends(async_get_db)
):
    try:
        if not oauth.google:
            raise HTTPException(status_code=500, detail="Google OAuth is not configured")
        token = await oauth.google.authorize_access_token(request)
        user_info = token["userinfo"]
    except OAuthError:
        raise HTTPException(
            status_code=400,
            detail="OAuth flow failed. Try again."
        )

    user_data = GoogleUserCreateModel(**user_info)

    user = await user_service.get_user_by_email(user_data.email, session)

    if user:
        if user.login_provider == "email" and not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account exists already, but not verified",
            )
        elif user.login_provider == "email" and user.is_verified:
            user = await user_service.update_google_user(user, user_data, session)
        # elif user.login_provider == "google":
        #     user = await user_service.update_google_user(user, user_data, session)
    else:
        user = await user_service.create_google_user(user_data, session)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User creation failed",
            )

    code = str(uuid.uuid4())
    await add_oauth_code_to_blocklist(code, str(user.id))

    return RedirectResponse(
        url=f"{settings.DOMAIN}/oauth_success?code={code}"
    )


# ----------------------------------------------
# create access and refresh tokens
# ----------------------------------------------
@oauth_router.get("/oauth_token/{code}")
async def create_oauth_token(
    code: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(async_get_db)
):
    user_id = await oauth_code_in_blocklist(code)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code",
        )
    user = await user_service.get_user_by_id(UUID(user_id), session)

    if not user:
        raise raise_user_not_found_exception()

    if not user.is_verified:
        raise raise_invalid_credentials_exception()

    if not user.is_oauth:
        raise raise_invalid_credentials_exception()

    # Check if the user has 2FA enabled
    if user.two_factor_enabled:
        two_factor_token = await token_service.generate_two_factor_token(
            email=user.email, db=session
        )

        html = templates.get_template("auth/2fa_code.html").render(
            token=two_factor_token.token,
        )

        # Prepare email content
        recipients = [
            EmailRecipient(
                email=two_factor_token.email, name=two_factor_token.email.split('@')[0]
            )
        ]
        content = EmailRawHTMLContent(
            subject="2FA Code",
            html_content=html,
            sender_name="Mimipoint",
        )
        background_tasks.add_task(send_html_email, recipients, content)

        return {
                "message": "2FA code sent to your email",
                "two_factor_required": True,
                "user": {"email": user.email, "uid": str(user.id)},
            }

    access_token, refresh_token = create_auth_tokens(user)
    return {
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {"email": user.email, "id": str(user.id)},
        }
