from datetime import datetime
from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.auth.services.token_service import TokenService
from app.core.database import async_get_db
from app.core.mail import EmailRawHTMLContent, EmailRecipient, send_html_email
from app.core.redis import add_jti_to_blocklist
from app.core.templates import templates

from ..dependencies import (
    AccessTokenBearer,
    RefreshTokenBearer,
    RoleChecker,
    get_current_user,
)
from ..schemas.schemas import (
    BulkEmailData,
    PasswordResetModel,
    TokenRequestModel,
    UserCreateModel,
    UserLoginModel,
    UserModel,
    EmailModel,
    PasswordResetConfirmModel,
)
from ..services.service import UserService
from ..utils import (
    create_access_token,
    create_auth_tokens,
    verify_password,
    generate_passwd_hash,
)
from ..errors import (
    raise_invalid_credentials_exception,
    raise_invalid_token_exception,
    raise_is_oauth_user_exception,
    raise_user_already_exists_exception,
    raise_user_not_found_exception,
)
from app.core.config import settings
from typing import List

auth_router = APIRouter()
user_service = UserService()
token_service = TokenService()
role_checker = RoleChecker(["admin", "customer"])
admin_checker = RoleChecker(["admin"])


REFRESH_TOKEN_EXPIRY = settings.REFRESH_TOKEN_EXPIRY


@auth_router.post("/send_mail")
async def send_mail(emails: EmailModel,
                    data: BulkEmailData,
                    background_tasks: BackgroundTasks):
    emaillist = emails.addresses

    # Prepare email content
    recipients = [EmailRecipient(email=email,
                                 name=email.split('@')[0]
                                 ) for email in emaillist]
    content = EmailRawHTMLContent(
        subject=data.subject,
        html_content=data.html_content,
        sender_name="Mimipoint",
    )
    background_tasks.add_task(send_html_email, recipients, content)

    return {"message": "Email sent successfully"}


# -------------------------------------------------------------
# Sign up Route
# -------------------------------------------------------------

@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user_Account(
    user_data: UserCreateModel,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(async_get_db),
):
    """
    Create user account using email, username, first_name, last_name
    params:
        user_data: UserCreateModel
    """
    email = user_data.email

    user_exists = await user_service.user_exists(email, session)

    if user_exists:
        raise raise_user_already_exists_exception()
    new_user = await user_service.create_user(user_data, session)

    token_data = await token_service.generate_verification_token(
        email=email,
        db=session,
    )

    # Prepare email content
    recipients = [EmailRecipient(
        email=token_data.email,
        name=token_data.email.split('@')[0])
        ]
    content = EmailRawHTMLContent(
        subject="Verify Your email",
        html_content=templates.get_template("auth/email_verfication.html").render(
            token=token_data.token,
            user=new_user,
        ),
        sender_name="Mimipoint",
    )
    background_tasks.add_task(send_html_email, recipients, content)

    return JSONResponse(
        content={
            "message": "Account Created! Check email to verify your account",
            "user": UserModel.model_validate(new_user).model_dump(),
        },
        status_code=status.HTTP_201_CREATED
    )

# --------------------------------------------------------
# Resend Verification Email
# --------------------------------------------------------


@auth_router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification_email(
    email_data: TokenRequestModel,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(async_get_db),
):
    """
    Resend verification email to user
    params:
        user: UserModel
    """
    token_data = await token_service.generate_verification_token(
        email=email_data.email,
        db=session,
    )
    user_data = await user_service.get_user_by_email(
        email=email_data.email,
        session=session,
    )
    if not user_data:
        raise raise_user_not_found_exception()

    # Prepare email content
    recipients = [EmailRecipient(
        email=token_data.email,
        name=user_data.first_name or token_data.email.split('@')[0]
        )]
    content = EmailRawHTMLContent(
        subject="Verify Your email",
        html_content=templates.get_template("auth/email_verfication.html").render(
            token=token_data.token,
            user=user_data,
        ),
        sender_name="Mimipoint",
    )
    background_tasks.add_task(send_html_email, recipients, content)
    return JSONResponse(
        content={
            "message": "Verification email sent successfully",
        },
        status_code=status.HTTP_200_OK
    )


# --------------------------------------------------------
# Login Route
# --------------------------------------------------------
@auth_router.post("/login")
async def login_users(
    login_data: UserLoginModel,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(async_get_db),
):
    email = login_data.email
    password = login_data.password

    user = await user_service.get_user_by_email(email, session)
    if not user:
        raise raise_user_not_found_exception()
    if user.password_hash is None:
        raise raise_is_oauth_user_exception()

    if user and verify_password(password, user.password_hash):
        # check if user email is verified
        if not user.is_verified:
            token_data = await token_service.generate_verification_token(
                email=user.email,
                db=session,
            )

            # Prepare email content
            recipients = [EmailRecipient(
                email=token_data.email,
                name=user.first_name or token_data.email.split('@')[0]
                                                                    )]
            content = EmailRawHTMLContent(
                subject="Verify Your email",
                html_content=templates.get_template("auth/email_verfication.html").render(
                    token=token_data.token,
                    user=user,
                ),
                sender_name="Mimipoint",
            )
            background_tasks.add_task(send_html_email, recipients, content)

            return JSONResponse(
                content={
                    "message": "Verification email resent successfully",
                    "verification_needed": True,
                },
                status_code=status.HTTP_200_OK
            )

        # Check if user is 2FA enabled
        if user.two_factor_enabled:
            two_factor_token = await token_service.generate_two_factor_token(
                email=user.email, db=session
            )

            # Prepare email content
            recipients = [EmailRecipient(
                email=two_factor_token.email,
                name=two_factor_token.email.split('@')[0] 
                )]
            content = EmailRawHTMLContent(
                subject="2FA Code",
                html_content=templates.get_template("auth/2fa_code.html").render(
                    token=two_factor_token.token,
                ),
                sender_name="Mimipoint",
            )
            background_tasks.add_task(send_html_email, recipients, content)

            return JSONResponse(
                content={
                    "message": "2FA code sent to your email",
                    "two_factor_required": True,
                    "user": {"email": user.email, "uid": str(user.id)},
                },
                status_code=status.HTTP_202_ACCEPTED
            )

        access_token, refresh_token = create_auth_tokens(user)

        return JSONResponse(
            content={
                "message": "Login successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {"email": user.email, "id": str(user.id)},
            },
            status_code=status.HTTP_200_OK
        )

    raise raise_invalid_credentials_exception()

# ------------------------------------------------------
# Account Verification Route
# ------------------------------------------------------


@auth_router.get("/verify/{token}")
async def verify_user_account(token: str, session: AsyncSession = Depends(async_get_db)):
    """
    Verify user account using token
    params:
        token: str
    """
    token_data = await token_service.get_verification_token_by_token(token, session)
    if not token_data:
        raise raise_invalid_token_exception()
    user_email = token_data.email
    if user_email:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise raise_user_not_found_exception()

        await user_service.update_user(user, {"is_verified": True}, session)

        access_token, refresh_token = create_auth_tokens(user)

        return JSONResponse(
            content={
                "message": "Account verified successfully",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {"email": user.email, "id": str(user.id)},
            },
            status_code=status.HTTP_200_OK
        )

    return JSONResponse(
        content={"message": "Error occured during verification"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

# -----------------------------------------------------------
# Get New Access Token Route
# -----------------------------------------------------------


@auth_router.get("/refresh_token")
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    expiry_timestamp = token_details["exp"]

    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token(user_data=token_details["user"])

        return JSONResponse(content={"access_token": new_access_token})

    raise raise_invalid_token_exception()

# ------------------------------------------------
# Logout Route
# ------------------------------------------------


@auth_router.get("/logout")
async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):
    """
    Revoke the access token and refresh token
    params:
        token_details: dict
    """
    jti = token_details["jti"]
    await add_jti_to_blocklist(jti)
    return JSONResponse(
        content={"message": "Logged Out Successfully"}, status_code=status.HTTP_200_OK
    )


# ------------------------------------------------
# Password Reset Request Route
# ------------------------------------------------
@auth_router.post("/password-reset-request")
async def password_reset_request(
    email_data: TokenRequestModel,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(async_get_db),
):
    email = email_data.email
    token_data = await token_service.generate_password_reset_token(email, session)
    if not token_data:
        raise HTTPException(
            detail="Invalid email address", status_code=status.HTTP_400_BAD_REQUEST
        )

    link = f"{settings.DOMAIN}/reset-password?token={token_data.token}"
    
    # Prepare email content
    recipients = [EmailRecipient(
        email=token_data.email,
        name=token_data.email.split('@')[0]
                                        )]
    content = EmailRawHTMLContent(
        subject="Reset Your Password",
        html_content=templates.get_template("auth/password_reset.html").render(
            reset_url=link,
        ),
        sender_name="Mimipoint",
    )
    background_tasks.add_task(send_html_email, recipients, content)

    return JSONResponse(
        content={
            "message": "Please check your email for instructions to reset your password",
        },
        status_code=status.HTTP_200_OK,
    )

# ------------------------------------------------
# Password Reset Confirm Route
# ------------------------------------------------


@auth_router.post("/password-reset-confirm/{token}")
async def reset_account_password(
    token: str,
    passwords: PasswordResetConfirmModel,
    session: AsyncSession = Depends(async_get_db),
):
    """
    Reset user password using token
    params:
        token: str
        passwords: PasswordResetConfirmModel
    """
    new_password = passwords.new_password
    confirm_password = passwords.confirm_new_password

    if new_password != confirm_password:
        raise HTTPException(
            detail="Passwords do not match", status_code=status.HTTP_400_BAD_REQUEST
        )

    token_data = await token_service.get_password_reset_token_by_token(token, session)
    if not token_data:
        raise raise_invalid_token_exception()
    user_email = token_data.email

    if user_email:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise raise_user_not_found_exception()

        passwd_hash = generate_passwd_hash(new_password)
        await user_service.update_user(user, {"password_hash": passwd_hash}, session)

        return JSONResponse(
            content={"message": "Password reset Successfully"},
            status_code=status.HTTP_200_OK,
        )

    return JSONResponse(
        content={"message": "Error occured during password reset."},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

# ------------------------------------------------
# Password Reset Route
# ------------------------------------------------


@auth_router.post("/password-reset", status_code=status.HTTP_200_OK)
async def password_reset(
    passwords: PasswordResetModel,
    user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db),
):
    """
    Reset user password using the old password
    params:
        passwords: PasswordResetModel
    """
    old_password = passwords.old_password
    new_password = passwords.new_password
    confirm_password = passwords.confirm_new_password
    if new_password != confirm_password:
        raise HTTPException(
            detail="Passwords do not match", status_code=status.HTTP_400_BAD_REQUEST
        )
    user = await user_service.get_user_by_email(
        user.email, session
    )
    if not user:
        raise raise_user_not_found_exception()
    if not user.password_hash:
        raise raise_is_oauth_user_exception()
    if user and verify_password(old_password, user.password_hash):
        passwd_hash = generate_passwd_hash(new_password)
        await user_service.update_user(user, {"password_hash": passwd_hash}, session)
        return JSONResponse(
            content={"message": "Password reset Successfully"},
            status_code=status.HTTP_200_OK,
        )
    raise raise_invalid_credentials_exception()
