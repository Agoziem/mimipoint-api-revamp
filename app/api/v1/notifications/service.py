from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException
from uuid import UUID
from typing import List
from .models import Notification, NotificationRecipient
from .schemas import NotificationCreate, NotificationOnlyResponse, NotificationResponse, NotificationUpdate, NotificationUserResponse
from sqlalchemy import update, desc


class NotificationService:
    async def store_notification(self, notification_data: NotificationCreate, user_ids: List[UUID], session: AsyncSession) -> Notification:
        """Create and store a new notification, and assign recipients."""
        notification = Notification(
            sender_id=notification_data.sender_id,
            title=notification_data.title,
            message=notification_data.message,
            link=notification_data.link,
            image=notification_data.image
        )

        session.add(notification)
        await session.commit()
        await session.refresh(notification)

        # Create NotificationRecipient records
        for user_id in user_ids:
            session.add(NotificationRecipient(
                notification_id=notification.id,
                user_id=user_id,
                is_read=False
            ))

        await session.commit()
        return notification

    async def get_unread_notifications(
        self,
        user_id: UUID,
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0
    ) -> List[NotificationOnlyResponse]:
        """Retrieve unread notifications for a user."""

        # Join NotificationRecipient and Notification to filter by is_read=False
        stmt = (
            select(Notification)
            .join(NotificationRecipient)
            .filter(
                NotificationRecipient.user_id == user_id,
                NotificationRecipient.is_read == False
            )
            .order_by(desc(Notification.created_at))
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(stmt)
        notifications = result.scalars().unique().all()

        return [
            NotificationOnlyResponse(
                id=notification.id,
                title=notification.title,
                message=notification.message,
                link=notification.link,
                image=notification.image,
                sender_id=notification.sender_id,
                created_at=notification.created_at,
            )
            for notification in notifications
        ]

    async def mark_notification_as_read(
        self,
        notification_id: UUID,
        user_id: UUID,
        session: AsyncSession
    ) -> bool:
        """Mark a notification as read for a specific user and return the updated notification."""

        # Step 1: Find the NotificationRecipient entry
        stmt = select(NotificationRecipient).filter(
            NotificationRecipient.notification_id == notification_id,
            NotificationRecipient.user_id == user_id
        )
        result = await session.execute(stmt)
        recipient_assoc = result.scalar_one_or_none()

        if not recipient_assoc:
            raise HTTPException(
                status_code=404, detail="Notification or User not found")

        # Step 2: Update is_read
        recipient_assoc.is_read = True
        await session.commit()

        # Step 3: Get the notification
        notification_stmt = select(Notification).filter(
            Notification.id == notification_id)
        notification_result = await session.execute(notification_stmt)
        notification = notification_result.scalar_one_or_none()

        if not notification:
            return False

        return True

    async def get_user_sent_notifications(
        self,
        user_id: UUID,
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0
    ) -> List[NotificationResponse]:
        """Retrieve notifications sent by a specific user."""
        try:
            statement = select(Notification).options(
                joinedload(Notification.recipient_associations)
                .joinedload(NotificationRecipient.user)
            ).where(Notification.sender_id == user_id).order_by(
                desc(Notification.created_at)
            ).limit(limit).offset(offset)

            result = await session.execute(statement)
            notifications = result.unique().scalars().all()

            responses = []
            for notification in notifications:
                recipient_schemas = [
                    NotificationUserResponse(
                        id=assoc.user.id,
                        first_name=assoc.user.first_name,
                        last_name=assoc.user.last_name or "",
                        image_url=assoc.user.avatar,
                        has_read=assoc.is_read
                    )
                    for assoc in notification.recipient_associations
                    if assoc.user  # Ensure user exists
                ]

                responses.append(NotificationResponse(
                    id=notification.id,
                    sender_id=notification.sender_id,
                    title=notification.title,
                    message=notification.message,
                    link=notification.link,
                    image=notification.image,
                    created_at=notification.created_at,
                    recipients=recipient_schemas
                ))

            return responses
        except Exception as e:
            # Log the error in a real application
            raise HTTPException(status_code=500, detail=f"Failed to retrieve sent notifications: {str(e)}")

    async def get_all_notifications(
        self,
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0
    ) -> List[NotificationResponse]:
        """Retrieve all notifications with recipient user details and read status."""
        statement = select(Notification).options(
            joinedload(Notification.recipient_associations).joinedload(
                NotificationRecipient.user)
        ).order_by(desc(Notification.created_at)).limit(limit).offset(offset)

        result = await session.execute(statement)
        notifications = result.unique().scalars().all()

        responses = []
        for notification in notifications:
            recipient_schemas = [
                NotificationUserResponse(
                    id=assoc.user.id,
                    first_name=assoc.user.first_name,
                    last_name=assoc.user.last_name or "",
                    image_url=assoc.user.avatar,
                    has_read=assoc.is_read
                )
                for assoc in notification.recipient_associations
            ]

            responses.append(NotificationResponse(
                id=notification.id,
                sender_id=notification.sender_id,
                title=notification.title,
                message=notification.message,
                link=notification.link,
                image=notification.image,
                created_at=notification.created_at,
                recipients=recipient_schemas
            ))

        return responses

    async def get_notification_by_id(
        self,
        notification_id: UUID,
        session: AsyncSession
    ) -> NotificationResponse | None:
        """Retrieve a notification by its ID with recipient read status."""
        statement = select(Notification).filter(
            Notification.id == notification_id
        ).options(joinedload(Notification.recipient_associations).joinedload(NotificationRecipient.user))

        result = await session.execute(statement)
        notification = result.scalar_one_or_none()

        if not notification:
            return None

        recipient_schemas = [
            NotificationUserResponse(
                id=assoc.user.id,
                first_name=assoc.user.first_name,
                last_name=assoc.user.last_name or "",
                image_url=assoc.user.avatar,
                has_read=assoc.is_read
            )
            for assoc in notification.recipient_associations
        ]

        return NotificationResponse(
            id=notification.id,
            sender_id=notification.sender_id,
            title=notification.title,
            message=notification.message,
            link=notification.link,
            created_at=notification.created_at,
            recipients=recipient_schemas
        )

    async def remove_user_from_notification(
        self,
        notification_id: UUID,
        user_id: UUID,
        session: AsyncSession
    ) -> bool:
        """Remove a user from a notification (via association table)."""

        stmt = select(NotificationRecipient).where(
            NotificationRecipient.notification_id == notification_id,
            NotificationRecipient.user_id == user_id
        )
        result = await session.execute(stmt)
        recipient_assoc = result.scalar_one_or_none()
        if not recipient_assoc:
            return False
        await session.delete(recipient_assoc)
        await session.commit()
        return True

    async def update_notification(
            self,
            notification_id: UUID,
            update_data: NotificationUpdate,
            session: AsyncSession
    ) -> NotificationUpdate | None:
        """Update an existing notification."""
        statement = select(Notification).filter(
            Notification.id == notification_id)
        result = await session.execute(statement)
        notification = result.scalar_one_or_none()

        if not notification:
            return None

        # Update the notification fields
        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(notification, key, value)

        await session.commit()
        await session.refresh(notification)

        # update user_ids if provided
        if update_data.user_ids:
            # Get existing recipient user_ids for this notification
            existing_recipients_stmt = select(NotificationRecipient.user_id).filter(
                NotificationRecipient.notification_id == notification_id
            )
            existing_result = await session.execute(existing_recipients_stmt)
            existing_user_ids = set(existing_result.scalars().all())
            
            # Find new user_ids that don't already exist
            new_user_ids = [user_id for user_id in update_data.user_ids if user_id not in existing_user_ids]
            
            # Only add new recipients that don't already exist
            if new_user_ids:
                for user_id in new_user_ids:
                    session.add(NotificationRecipient(
                        notification_id=notification.id,
                        user_id=user_id,
                        is_read=False
                    ))
                await session.commit()

        return NotificationUpdate(
            id=notification.id,
            title=notification.title,
            message=notification.message,
            link=notification.link,
            image=notification.image,
            sender_id=notification.sender_id
        )

    async def delete_notification(
            self,
            notification_id: UUID,
            session: AsyncSession
    ) -> bool:
        """Delete a notification by its ID."""
        statement = select(Notification).filter(
            Notification.id == notification_id)
        result = await session.execute(statement)
        notification = result.scalar_one_or_none()

        if not notification:
            return False

        await session.delete(notification)
        await session.commit()
        return True