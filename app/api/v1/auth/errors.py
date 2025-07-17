from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


# Reusable HTTPException raisers
def raise_invalid_token_exception() -> HTTPException:
    """ Raises an HTTPException indicating that the token is invalid or expired. """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "message": "Token is invalid or expired",
            "error_code": "invalid_token",
            "resolution": "Please get a new token"
        }
    )

def raise_revoked_token_exception() -> HTTPException:
    """ Raises an HTTPException indicating that the token has been revoked. """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "message": "Token is invalid or has been revoked",
            "error_code": "token_revoked",
            "resolution": "Please get a new token"
        }
    )

def raise_access_token_required_exception() -> HTTPException:
    """ Raises an HTTPException indicating that an access token is required. """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "message": "Please provide a valid access token",
            "error_code": "access_token_required"
        }
    )

def raise_refresh_token_required_exception() -> HTTPException:
    """ Raises an HTTPException indicating that a refresh token is required. """
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "message": "Please provide a valid refresh token",
            "error_code": "refresh_token_required"
        }
    )

def raise_user_already_exists_exception() -> HTTPException:
    """ Raises an HTTPException indicating that a user with the given email already exists. """
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "message": "User with email already exists",
            "error_code": "user_exists"
        }
    )

def raise_invalid_credentials_exception() -> HTTPException:
    """ Raises an HTTPException indicating that the provided email or password is invalid. """
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "message": "Invalid Email Or Password",
            "error_code": "invalid_email_or_password"
        }
    )

def raise_insufficient_permission_exception() -> HTTPException:
    """ Raises an HTTPException indicating that the user does not have sufficient permissions. """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "message": "You do not have enough permissions",
            "error_code": "insufficient_permissions"
        }
    )

def raise_user_not_found_exception() -> HTTPException:
    """ Raises an HTTPException indicating that the user was not found in the database. """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "message": "User not found",
            "error_code": "user_not_found"
        }
    )


def raise_account_not_verified_exception() -> HTTPException:
    """ Raises an HTTPException indicating that the user's account has not been verified. """
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "message": "Account Not verified",
            "error_code": "account_not_verified",
            "resolution": "Please check your email for verification details"
        }
    )

def raise_is_oauth_user_exception() -> HTTPException:
    """ Raises an HTTPException indicating that the user is an OAuth user and cannot perform certain actions. """
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "message": "User is an oauth user",
            "error_code": "is_oauth_user",
            "resolution": "Please login via google"
        }
    )



def register_general_error_handlers(app: FastAPI):
    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(request: Request, exc: SQLAlchemyError):
        print(str(exc))  # optional: for debugging/logging
        return JSONResponse(
            content={
                "message": "Database error occurred",
                "error_code": "database_error"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @app.exception_handler(Exception)
    async def internal_server_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            content={
                "message": "Oops! Something went wrong",
                "error_code": "server_error"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

