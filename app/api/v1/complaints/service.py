from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.v1.complaints.models import Complaint
from app.api.v1.complaints.schemas import ComplaintCreate
from typing import Optional
from sqlalchemy import desc


class ComplaintService:
    async def create_complaint(self, complaint_data: ComplaintCreate, session: AsyncSession) -> Complaint:
        """Create a new complaint."""
        complaint_dict = complaint_data.model_dump()
        complaint = Complaint(**complaint_dict)
        session.add(complaint)
        await session.commit()
        await session.refresh(complaint)
        return complaint

    async def get_complaints(self, user_id: UUID, session: AsyncSession) -> List[Complaint]:
        """Get all complaints for a user."""
        result = await session.execute(select(Complaint).where(Complaint.user_id == user_id).order_by(desc(Complaint.created_at)))
        return list(result.scalars().all())

    async def get_complaint_by_id(self, complaint_id: UUID, session: AsyncSession) -> Optional[Complaint]:
        """Get a complaint by ID."""
        result = await session.execute(select(Complaint).where(Complaint.id == complaint_id))
        return result.scalars().first()

    async def delete_complaint(self, complaint_id: UUID, session: AsyncSession) -> bool:
        """Delete a complaint by ID."""
        complaint = await self.get_complaint_by_id(complaint_id, session)
        if not complaint:
            return False
        await session.delete(complaint)
        await session.commit()
        return True
