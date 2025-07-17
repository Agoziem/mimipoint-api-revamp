from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.auth.schemas.schemas import UserResponseModel as UserResponse
from app.api.v1.auth.services.service import ActivityService
from app.core.database import async_get_db
from typing import List, Optional
from uuid import UUID
from fastapi.responses import JSONResponse
from app.api.v1.complaints.schemas import ComplaintCreate, ComplaintResponse
from app.api.v1.complaints.service import ComplaintService


complaint_router = APIRouter()
complaint_service = ComplaintService()
activity_service = ActivityService()
# get all complaints for a user


@complaint_router.get("/", response_model=List[ComplaintResponse], status_code=status.HTTP_200_OK)
async def get_complaints(db: AsyncSession = Depends(async_get_db), current_user: UserResponse = Depends(get_current_user)):
    """Get all complaints for a user"""
    complaints = await complaint_service.get_complaints(user_id=current_user.id, session=db)
    return complaints

# get a single complaint by id


@complaint_router.get("/{complaint_id}", response_model=ComplaintResponse, status_code=status.HTTP_200_OK)
async def get_complaint(complaint_id: UUID, db: AsyncSession = Depends(async_get_db), _: UserResponse = Depends(get_current_user)):
    """Get a single complaint by ID"""
    complaint = await complaint_service.get_complaint_by_id(complaint_id=complaint_id, session=db)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    return complaint

# delete a complaint by id


@complaint_router.delete("/{complaint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_complaint(complaint_id: UUID, db: AsyncSession = Depends(async_get_db), current_user: UserResponse = Depends(get_current_user)):
    """Delete a complaint by ID"""
    deleted = await complaint_service.delete_complaint(complaint_id=complaint_id, session=db)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    await activity_service.create_user_activity(
        user_id=current_user.id,
        activity_type="delete",
        description=f"Deleted complaint with ID: {complaint_id}",
        session=db
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# create a new complaint


@complaint_router.post("/", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint(complaint_data: ComplaintCreate, db: AsyncSession = Depends(async_get_db), current_user: UserResponse = Depends(get_current_user)):
    """Create a new complaint"""
    complaint = await complaint_service.create_complaint(complaint_data=complaint_data, session=db)
    await activity_service.create_user_activity(
        user_id=current_user.id,
        activity_type="create",
        description=f"Created complaint with ID: {complaint.id}",
        session=db
    )
    return complaint
