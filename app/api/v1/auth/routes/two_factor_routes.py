from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.auth.errors import raise_user_not_found_exception
from app.api.v1.auth.models import User
from app.api.v1.auth.services.token_service import TokenService
from app.core.database import async_get_db
from app.core.mail import EmailRawHTMLContent, EmailRecipient, send_html_email
from app.core.templates import templates

from ..dependencies import (
    RoleChecker,
    get_current_user,
)
from ..schemas.schemas import (
    TokenRequestModel,
    UserModel,

)
from ..services.service import UserService
from ..utils import (
    create_access_token,
    create_auth_tokens,
)


twoFA_router = APIRouter()
user_service = UserService()
token_service = TokenService()
role_checker = RoleChecker(["admin", "user"])
admin_checker = RoleChecker(["admin"])


# --------------------------------------------------------------------
# Enable 2FA for user
# --------------------------------------------------------------------
@twoFA_router.get("/enable-2FA")
async def enable_2fa(
    user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db)
):
    """
    Enable 2FA for user
    params:
        user: UserModel
    """
    user_2fa = await token_service.enable_two_factor_for_user(str(user.id), session)
    if not user_2fa:
        raise HTTPException(
            detail="Error enabling 2FA", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    await user_service.update_user(user, {"two_factor_enabled": True}, session)
    return {
        "message": "2FA enabled successfully",
    }

# --------------------------------------------------------------------
# Generate 2FA token
# --------------------------------------------------------------------


@twoFA_router.get("/verify-2FA-code/{token}", status_code=status.HTTP_200_OK)
async def verify_2fa_code(
    token: str,
    session: AsyncSession = Depends(async_get_db)
):
    """
    Verify the 2FA token and enable 2FA for the user.
    """
    token_obj = await token_service.get_two_factor_token_by_token(token, session)

    if not token_obj:
        raise HTTPException(
            detail="Invalid or expired token.",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    user = await user_service.get_user_by_email(token_obj.email, session)
    if not user:
        raise raise_user_not_found_exception()

    access_token, refresh_token = create_auth_tokens(user)

    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {"email": user.email, "id": str(user.id)},
    }
# --------------------------------------------------------------------
# Resend 2FA code
# --------------------------------------------------------------------


@twoFA_router.post("/resend-2FA-code")
async def resend_2fa_code(
    email_data: TokenRequestModel,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(async_get_db)
):
    """
    Resend the 2FA code to the user's email.
    params:
        user: UserModel
    """
    token_obj = await token_service.generate_two_factor_token(
        email=email_data.email, db=session
    )
    if not token_obj:
        raise HTTPException(
            detail="Error generating 2FA token",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    # Prepare email content
    recipients = [EmailRecipient(
        email=token_obj.email, name=token_obj.email.split('@')[0])]
    content = EmailRawHTMLContent(
        subject="2FA Code",
        html_content=templates.get_template("auth/2fa_code.html").render(
                token=token_obj.token,
        ),
        sender_name="Mimipoint",
    )
    background_tasks.add_task(send_html_email, recipients, content)
    return {
        "message": "2FA code resent to your email",
    }

# --------------------------------------------------------------------
# Disable 2FA for user
# --------------------------------------------------------------------


@twoFA_router.get("/disable-2FA")
async def disable_2fa(
    user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db)
):
    """
    Disable 2FA for user
    params:
        user: UserModel
    """
    disabled = await token_service.disable_two_factor_for_user(str(user.id), session)
    if not disabled:
        raise HTTPException(
            detail="Error disabling 2FA", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    await user_service.update_user(user, {"two_factor_enabled": False}, session)
    # Invalidate the 2FA token
    token_obj = await token_service.get_two_factor_token_by_email(user.email, session)
    if token_obj:
        await session.delete(token_obj)
        await session.commit()
        await session.refresh(token_obj)

    return {"message": "2FA disabled successfully"}
