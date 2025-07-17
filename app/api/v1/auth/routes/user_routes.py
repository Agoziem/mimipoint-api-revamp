from uuid import UUID

from fastapi import APIRouter, Depends, status, Query
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_get_db

from ..dependencies import (
    RoleChecker,
    get_current_user as get_current_user_dep,
)
from ..schemas.schemas import (
    ActivityResponse,
    ChangeRoleModel,
    UserModel,
    UserResponseModel,
    UserUpdateModel,
)
from ..services.service import ActivityService, UserService
from typing import List

user_router = APIRouter()
user_service = UserService()
activity_service = ActivityService()
role_checker = RoleChecker(["admin", "customer"])
admin_checker = RoleChecker(["admin"])

# --------------------------------------------------------------------
# Fetch all users
# --------------------------------------------------------------------


@user_router.get("/all", response_model=List[UserResponseModel])
async def fetch_users(
    role: str = Query("All", enum=["All", "admin", "customer"]),
    limit: int = Query(10, gt=0),
    offset: int = Query(0, ge=0),
    _: bool = Depends(admin_checker),
    session: AsyncSession = Depends(async_get_db)
):
    users = await user_service.get_users(role, limit, offset, session)
    return users

# --------------------------------------------------------------------
# Fetch user by ID
# --------------------------------------------------------------------


@user_router.get("/profile", response_model=UserModel | None)
async def get_current_user(
    user: UserModel = Depends(get_current_user_dep)
):
    return user


# --------------------------------------------------------------------
# Update user information
# --------------------------------------------------------------------

@user_router.put("/update-user")
async def update_user(
    user_data: UserUpdateModel,
    user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db)
):

    updated_user = await user_service.update_user(
        user,
        user_data.model_dump(exclude_unset=True),
        session
    )

    return JSONResponse(
        content={"message": "User information updated successfully",
                 "user": UserUpdateModel.model_validate(updated_user).model_dump()
                 },
        status_code=status.HTTP_200_OK
    )

# --------------------------------------------------------------------
# Delete user
# --------------------------------------------------------------------


@user_router.delete("/delete_user/{user_id}")
async def delete_user(
        user_id: UUID,
        _: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(async_get_db),
):
    deleted = await user_service.delete_user(user_id, session)

    if deleted:
        return JSONResponse(content={"message": "User deleted successfully"}, status_code=status.HTTP_200_OK)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found")

# --------------------------------------------------------------------
# change user role
# --------------------------------------------------------------------


@user_router.post("/change-role")
async def change_user_role(
    details: ChangeRoleModel,
    # _: UserModel = Depends(admin_checker),
    session: AsyncSession = Depends(async_get_db)
):
    """
    Change the role of a user.
    """
    user_id = details.user_id
    new_role = details.new_role
    update_user = await user_service.change_user_role(user_id, new_role, session)
    if not update_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return JSONResponse(
        content={"message": "User role updated successfully",
                 "user": UserUpdateModel.model_validate(update_user).model_dump()
                 },
        status_code=status.HTTP_200_OK
    )

# -----------------------------------------------------------------------
# User activity
# -----------------------------------------------------------------------


@user_router.get("/activity", status_code=status.HTTP_200_OK, response_model=List[ActivityResponse])
async def get_user_activity(
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db)
):
    """
    Retrieve current user's activity history.
    """
    activities = await activity_service.get_user_activity(current_user.id, session=session)
    return activities
