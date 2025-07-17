from pydantic import BaseModel, UUID4, Field, HttpUrl, field_serializer
from datetime import datetime
from typing import List, Optional
from app.api.v1.auth.schemas.schemas import UserModel, UserResponseModel
from app.api.v1.easybuy.models import BillingCategoryEnum, BillingCycleEnum, ProductCategoryEnum, SubscriptionStatus
from enum import Enum


class EasybuyPlanBase(BaseModel):
    """Base schema for EasybuyPlan model"""
    name: str
    description: str
    price: float
    no_of_products: int
    billing_cycle: BillingCycleEnum = BillingCycleEnum.MONTHLY
    billing_category: BillingCategoryEnum = BillingCategoryEnum.STANDARD


class EasybuyPlanCreate(EasybuyPlanBase):
    """Schema for creating a new EasybuyPlan"""
    pass


class EasybuyPlanResponse(EasybuyPlanBase):
    """Schema for returning EasybuyPlan details"""
    id: UUID4
    created_at: datetime

    @field_serializer("id")
    def serialize_uuid(self, value: UUID4) -> str:
        return str(value)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()

    class Config:
        from_attributes = True


class EasybuySubscriptionBase(BaseModel):
    """Base schema for EasybuySubscription model"""
    user_id: UUID4
    plan_id: UUID4
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE

    @field_serializer("user_id")
    def serialize_user_id(self, value: UUID4) -> str:
        return str(value)

    @field_serializer("plan_id")
    def serialize_plan_id(self, value: UUID4) -> str:
        return str(value)


class EasybuySubscriptionCreate(EasybuySubscriptionBase):
    """Schema for creating a new EasybuySubscription"""
    pass


class EasybuySubscriptionResponse(EasybuySubscriptionBase):
    """Schema for returning EasybuySubscription details"""
    id: UUID4
    start_date: datetime
    end_date: datetime

    plan: Optional[EasybuyPlanResponse] = None
    user: Optional[UserResponseModel] = None

    @field_serializer("id")
    def serialize_uuid(self, value: UUID4) -> str:
        return str(value)

    @field_serializer("start_date")
    def serialize_start_date(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer("end_date")
    def serialize_end_date(self, value: datetime) -> str:
        return value.isoformat()

    class Config:
        from_attributes = True


class EasybuyChangeSubscriptionStatus(BaseModel):
    """Schema for changing the status of an EasybuySubscription"""
    subscription_id: UUID4
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE

    @field_serializer("status")
    def serialize_status(self, value: SubscriptionStatus) -> str:
        return value.value

    @field_serializer("subscription_id")
    def serialize_subscription_id(self, value: UUID4) -> str:
        return str(value)


class EasybuyChangeSubscriptionPlan(BaseModel):
    """Schema for changing the plan of an EasybuySubscription"""
    plan_id: UUID4
    subscription_id: UUID4

    @field_serializer("plan_id")
    def serialize_uuids(self, value: UUID4):
        return str(value)

    @field_serializer("subscription_id")
    def serialize_subscription_id(self, value: UUID4) -> str:
        return str(value)


class ProductBase(BaseModel):
    """Base schema for Product model"""
    owner_id: UUID4
    name: str
    description: str
    price: float
    quantity: int
    image: str
    category: Optional[ProductCategoryEnum] = None
    tags: List[str] = Field(default=[])
    redirect_link: HttpUrl

    @field_serializer("owner_id")
    def serialize_owner_id(self, value: UUID4) -> str:
        return str(value)

    @field_serializer("redirect_link")
    def serialize_redirect_link(self, value: HttpUrl) -> str:
        return str(value)


class ProductCreate(ProductBase):
    """Schema for creating a new Product"""
    pass


class ProductResponse(ProductBase):
    """Schema for returning Product details"""
    id: UUID4
    created_at: datetime
    updated_at: datetime

    average_rating: Optional[float] = None
    review_count: Optional[int] = None

    owner: Optional[UserResponseModel] = None

    @field_serializer("id")
    def serialize_uuid(self, value: UUID4) -> str:
        return str(value)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer("updated_at")
    def serialize_updated_at(self, value: datetime) -> str:
        return value.isoformat()

    class Config:
        from_attributes = True


class ProductReviewBase(BaseModel):
    """Base schema for ProductReview model"""
    product_id: UUID4
    user_id: UUID4
    rating: int
    comment: Optional[str] = None

    @field_serializer("product_id")
    def serialize_product_id(self, value: UUID4) -> str:
        return str(value)

    @field_serializer("user_id")
    def serialize_user_id(self, value: UUID4) -> str:
        return str(value)


class ProductReviewCreate(ProductReviewBase):
    """Schema for creating a new ProductReview"""
    pass


class ProductReviewResponse(ProductReviewBase):
    """Schema for returning ProductReview details"""
    id: UUID4
    created_at: datetime

    user: Optional[UserResponseModel] = None

    @field_serializer("id")
    def serialize_uuid(self, value: UUID4) -> str:
        return str(value)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()

    class Config:
        from_attributes = True
