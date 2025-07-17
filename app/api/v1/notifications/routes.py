from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
from uuid import UUID

from app.api.v1.auth.models import User
from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.auth.schemas.schemas import UserResponseModel as UserResponse
from app.api.v1.auth.services.service import ActivityService
from app.core.database import async_get_db
from app.core.firebase import send_batch_notification
from .schemas import NotificationCreate, NotificationResponse, NotificationUpdate, NotificationUserResponse, RemoveUpdate, NotificationOnlyResponse
from .service import NotificationService
from sqlalchemy import select
# from app.core.websocket import ConnectionManager
# manager = ConnectionManager()


notification_router = APIRouter()
notification_service = NotificationService()


@notification_router.get("/user/unread", response_model=List[NotificationOnlyResponse])
async def get_unread_notifications(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(async_get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Retrieve unread notifications for the current user."""
    return await notification_service.get_unread_notifications(user_id=current_user.id, session=db, limit=limit, offset=offset)


@notification_router.get("/{notification_id}/mark-as-read", response_model=bool)
async def mark_as_read(
    notification_id: UUID,
    db: AsyncSession = Depends(async_get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Mark a notification as read."""
    successful = await notification_service.mark_notification_as_read(notification_id=notification_id, user_id=current_user.id, session=db)
    if not successful:
        raise HTTPException(
            status_code=404, detail="Notification not found or already read.")
    return successful


@notification_router.get("/user_sent", response_model=List[NotificationResponse])
async def get_user_sent_notifications(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(async_get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Retrieve notifications sent by the current user."""
    return await notification_service.get_user_sent_notifications(
        user_id=current_user.id, session=db, limit=limit, offset=offset
    )


@notification_router.get("/all", response_model=List[NotificationResponse])
async def get_all_notifications(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(async_get_db),
    _: UserResponse = Depends(get_current_user)
):
    """Retrieve all notifications for the current user."""
    notifications = await notification_service.get_all_notifications(session=db, limit=limit, offset=offset)
    return notifications


@notification_router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(async_get_db),
    _: UserResponse = Depends(get_current_user)
):
    """Retrieve a specific notification by ID."""
    notification = await notification_service.get_notification_by_id(notification_id=notification_id, session=db)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return notification


@notification_router.patch("/update_and_resend/{notification_id}", response_model=NotificationUpdate)
async def update_notification(
    notification_id: UUID,
    notification: NotificationUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(async_get_db),
    _: UserResponse = Depends(get_current_user),
):  
    
    print(f"notification: {notification}")
    updated_notification = await notification_service.update_notification(
        notification_id=notification_id,
        update_data=notification,
        session=db
    )
    if not updated_notification:
        raise HTTPException(status_code=404, detail="Notification not found.")

    user_ids = updated_notification.user_ids
    stmt = select(User).where(User.id.in_(user_ids)) if user_ids else select(User)
    result = await db.execute(stmt)
    users = result.scalars().all()

    users_fcm_tokens = [user.fcm_token for user in users if user.fcm_token]
    message = {
        "tokens": users_fcm_tokens,
        "title": updated_notification.title or "New Notification",
        "body": updated_notification.message or "",
        "link": updated_notification.link
    }

    print(f"Resending notification to tokens: {users_fcm_tokens}")
    print(f"Notification message: {message}")

    background_tasks.add_task(send_batch_notification, **message)

    return NotificationUpdate.model_validate(updated_notification)




@notification_router.get("/{notification_id}/remove_user_from_notification", response_model=bool)
async def remove_user_from_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(async_get_db),
    User: UserResponse = Depends(get_current_user)
):
    """Remove a user from a notification."""
    result = await notification_service.remove_user_from_notification(
        notification_id=notification_id,
        user_id=User.id,
        session=db
    )
    if not result:
        raise HTTPException(status_code=404, detail="Notification or User not found.")
    return True

# @notification_router.websocket("/ws/notifications")
# async def websocket_endpoint(websocket: WebSocket, user_id: UUID ):
#     """WebSocket endpoint for real-time notifications."""
#     await manager.connect(user_id, websocket, "notifications")
#     try:
#         while True:
#             await websocket.receive_text()  # Keep the connection alive
#     except WebSocketDisconnect:
#         manager.disconnect(user_id, websocket, "notifications")


# async def broadcast_notification(notification: UnreadNotificationResponse):
#     """Broadcast a notification to all connected users."""
#     for user in notification.recipients:
#         await manager.send_notification(user.id, "notifications", notification.model_dump())


@notification_router.post("/send_notification", response_model=dict)
async def create_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(async_get_db),
    _: UserResponse = Depends(get_current_user)
):
    """Create a new notification and send it to specified users."""
    print(f"Received notification: {notification}")
    user_ids = notification.user_ids
    if not user_ids:
        statement = select(User)
        result = await db.execute(statement)
        users = list(result.scalars().all())
        user_ids = [user.id for user in users]
    else:
        # If user_ids are provided, fetch those users' info for the schema
        statement = select(User).where(User.id.in_(user_ids))
        result = await db.execute(statement)
        users = list(result.scalars().all())

    # Store the notification in the DB
    saved_notification = await notification_service.store_notification(
        notification_data=notification,
        user_ids=user_ids,
        session=db
    )

    users_fcm_tokens = [user.fcm_token for user in users if user.fcm_token]
    message = {
        "tokens": users_fcm_tokens,
        "title": saved_notification.title,
        "body": saved_notification.message,
        "link": saved_notification.link if saved_notification.link else None
    }

    print(f"Sending notification to tokens: {users_fcm_tokens}")
    print(f"Notification message: {message}")

    # Send notification in the background
    background_tasks.add_task(send_batch_notification, **message)
    return {"detail": "Notification sent successfully."}



@notification_router.delete("/{notification_id}/delete", response_model=bool)
async def remove_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(async_get_db),
    _: UserResponse = Depends(get_current_user)
):
    """Remove a notification by ID."""
    result = await notification_service.delete_notification(notification_id=notification_id, session=db)
    if not result:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return True

