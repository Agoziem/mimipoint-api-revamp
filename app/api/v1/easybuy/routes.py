from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.auth.schemas.schemas import UserResponseModel as UserResponse
from app.api.v1.auth.services.service import ActivityService, UserService
from app.api.v1.easybuy.models import ProductCategoryEnum
from app.core.database import async_get_db
from typing import List
from uuid import UUID
from app.api.v1.easybuy.schemas import EasybuyChangeSubscriptionPlan, EasybuyChangeSubscriptionStatus, EasybuyPlanCreate, EasybuyPlanResponse, EasybuySubscriptionCreate, EasybuySubscriptionResponse, ProductCreate, ProductResponse, ProductReviewCreate, ProductReviewResponse
from app.api.v1.easybuy.service import EasybuyService, EasybuySubscriptionService, ProductService
from app.core.config import settings
from app.core.firebase import send_single_notification


easybuy_product_router = APIRouter()
easybuy_product_review_router = APIRouter()
easybuy_plan_router = APIRouter()
easybuy_subcription_router = APIRouter()
easybuy_service = EasybuyService()
easybuy_subscription_service = EasybuySubscriptionService()
product_service = ProductService()
activity_service = ActivityService()
user_service = UserService()

# -------------------------------------------------------
# products routes
# -------------------------------------------------------


@easybuy_product_router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, session: AsyncSession = Depends(async_get_db), current_user: UserResponse = Depends(get_current_user)):
    """Create a new product"""
    new_product = await product_service.create_product(product, session)
    if not new_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Product creation failed")
    await activity_service.create_user_activity(
        user_id=current_user.id,
        activity_type="create",
        description=f"Created product with ID: {new_product.id}",
        session=session,
    )
    return new_product


@easybuy_product_router.get("/", response_model=List[ProductResponse])
async def get_products(limit: int = 50, offset: int = 0, session: AsyncSession = Depends(async_get_db), _: UserResponse = Depends(get_current_user)):
    """Get all products with pagination"""
    products = await product_service.get_products(session, limit, offset)
    return products


@easybuy_product_router.get("/user", response_model=List[ProductResponse])
async def get_user_products(limit: int = 50, offset: int = 0, session: AsyncSession = Depends(async_get_db), current_user: UserResponse = Depends(get_current_user)):
    """Get all products for a specific user with pagination"""
    products = await product_service.get_user_products(current_user.id, session, limit, offset)
    return products


@easybuy_product_router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: UUID, product: ProductCreate, session: AsyncSession = Depends(async_get_db), _: UserResponse = Depends(get_current_user)):
    """Update an existing product"""
    updated_product = await product_service.update_product(product_id, product, session)
    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    await activity_service.create_user_activity(
        user_id=_.id,
        activity_type="update",
        description=f"Updated product with ID: {product_id}",
        session=session,
    )
    return updated_product


@easybuy_product_router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: UUID, session: AsyncSession = Depends(async_get_db), _: UserResponse = Depends(get_current_user)):
    """Get a product by ID"""
    product = await product_service.get_product_by_id(product_id, session)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@easybuy_product_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: UUID, session: AsyncSession = Depends(async_get_db), _: UserResponse = Depends(get_current_user)):
    """Delete a product"""
    deleted = await product_service.delete_product(product_id, session)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    await activity_service.create_user_activity(
        user_id=_.id,
        activity_type="delete",
        description=f"Deleted product with ID: {product_id}",
        session=session,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@easybuy_product_router.get("/search", response_model=List[ProductResponse])
async def search_products(query: str, limit: int = 50, offset: int = 0, session: AsyncSession = Depends(async_get_db), _: UserResponse = Depends(get_current_user)):
    """Search for products by name or description"""
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Query parameter is required")

    # Use regex to find products that match the query in name or description
    products = await product_service.search_products(query, session, limit, offset)

    return products


@easybuy_product_router.get("/products-by-cate", response_model=List[ProductResponse])
async def get_products_by_category(category: ProductCategoryEnum, limit: int = 50, offset: int = 0, session: AsyncSession = Depends(async_get_db), _: UserResponse = Depends(get_current_user)):
    """Get products by category with pagination"""
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Category parameter is required")

    # Validate category
    if not isinstance(category, ProductCategoryEnum):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category")

    # Fetch products by category
    products = await product_service.get_products_by_category(category, session, limit, offset)

    return products

# -------------------------------------------------------
# product reviews routes
# -------------------------------------------------------


@easybuy_product_review_router.post("/", response_model=ProductReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_product_review(
    review: ProductReviewCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(async_get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Create a new product review"""
    new_review = await product_service.create_product_review(review, session)
    if not new_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Review creation failed")
    user_token = user_service.get_users_fcmtoken_by_id(current_user.id, session)
    product = await product_service.get_product_by_id(new_review.product_id, session)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    message = {
        "token": user_token,
        "title": f"New Review for Product {product.name}",
        "body": f"{current_user.first_name} {current_user.last_name} just dropped a review for {product.name}",
        "link": f"{settings.DOMAIN}/easybuy/{new_review.product_id}"
    }
    background_tasks.add_task(send_single_notification, **message)
    await activity_service.create_user_activity(
        user_id=current_user.id,
        activity_type="create",
        description=f"Created review for product with ID: {new_review.product_id}",
        session=session,
    )
    return new_review


@easybuy_product_review_router.get("/{product_id}", response_model=List[ProductReviewResponse])
async def get_product_reviews(
    product_id: UUID,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(async_get_db),
    _: UserResponse = Depends(get_current_user)
):
    """Get all reviews for a specific product with pagination"""
    if not product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Product ID is required")

    reviews = await product_service.get_product_reviews(product_id, session, limit, offset)

    return reviews


@easybuy_product_review_router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_review(
    review_id: UUID,
    session: AsyncSession = Depends(async_get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a product review"""
    deleted = await product_service.delete_product_review(review_id, session)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    await activity_service.create_user_activity(
        user_id=current_user.id,
        activity_type="delete",
        description=f"Deleted review with ID: {review_id}",
        session=session,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@easybuy_product_review_router.put("/{review_id}", response_model=ProductReviewResponse)
async def update_product_review(
    review_id: UUID,
    review: ProductReviewCreate,
    session: AsyncSession = Depends(async_get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Update an existing product review"""
    updated_review = await product_service.update_product_review(review_id, review, session)
    if not updated_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    await activity_service.create_user_activity(
        user_id=current_user.id,
        activity_type="update",
        description=f"Updated review with ID: {review_id}",
        session=session,
    )
    return updated_review


# -------------------------------------------------------
# easybuy plans routes
# -------------------------------------------------------
@easybuy_plan_router.post("/", response_model=EasybuyPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(plan: EasybuyPlanCreate, session: AsyncSession = Depends(async_get_db), _: UserResponse = Depends(get_current_user)):
    """Create a new easybuy plan"""
    new_plan = await easybuy_service.create_plan(plan, session)
    if not new_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Plan creation failed")
    await activity_service.create_user_activity(
        user_id=_.id,
        activity_type="create",
        description=f"Created easybuy plan with ID: {new_plan.id}",
        session=session,
    )
    return new_plan


@easybuy_plan_router.put("/{plan_id}", response_model=EasybuyPlanResponse)
async def update_plan(plan_id: UUID, plan: EasybuyPlanCreate, session: AsyncSession = Depends(async_get_db), _: UserResponse = Depends(get_current_user)):
    """Update an existing easybuy plan"""
    updated_plan = await easybuy_service.update_plan(plan_id, plan, session)
    if not updated_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    await activity_service.create_user_activity(
        user_id=_.id,
        activity_type="update",
        description=f"Updated easybuy plan with ID: {plan_id}",
        session=session,
    )
    return updated_plan


@easybuy_plan_router.get("/{plan_id}", response_model=EasybuyPlanResponse)
async def get_plan(plan_id: UUID, session: AsyncSession = Depends(async_get_db)):
    """Get an easybuy plan by ID"""
    plan = await easybuy_service.get_plan_by_id(plan_id, session)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


@easybuy_plan_router.get("/", response_model=List[EasybuyPlanResponse])
async def get_plans(limit: int = 50, offset: int = 0, session: AsyncSession = Depends(async_get_db)):
    """Get all easybuy plans with pagination"""
    plans = await easybuy_service.get_plans(session, limit, offset)
    return plans


@easybuy_plan_router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(plan_id: UUID, session: AsyncSession = Depends(async_get_db), _: UserResponse = Depends(get_current_user)):
    """Delete an easybuy plan"""
    deleted = await easybuy_service.delete_plan(plan_id, session)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    await activity_service.create_user_activity(
        user_id=_.id,
        activity_type="delete",
        description=f"Deleted easybuy plan with ID: {plan_id}",
        session=session,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# -------------------------------------------------------
# easybuy subscriptions routes
# -------------------------------------------------------


@easybuy_subcription_router.post("/", response_model=EasybuySubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
        subscription: EasybuySubscriptionCreate,
        session: AsyncSession = Depends(async_get_db),
        _: UserResponse = Depends(get_current_user)):
    """Create a new easybuy subscription"""
    new_subscription = await easybuy_subscription_service.create_subscription(subscription, session)
    if not new_subscription:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Subscription creation failed")
    await activity_service.create_user_activity(
        user_id=_.id,
        activity_type="create",
        description=f"Created easybuy subscription with ID: {new_subscription.id}",
        session=session,
    )
    return new_subscription


@easybuy_subcription_router.get("/", response_model=List[EasybuySubscriptionResponse])
async def get_subscriptions(limit: int = 50, offset: int = 0, session: AsyncSession = Depends(async_get_db), _: UserResponse = Depends(get_current_user)):
    """Get all easybuy subscriptions with pagination"""
    subscriptions = await easybuy_subscription_service.get_subscriptions(session, limit, offset)
    return subscriptions


@easybuy_subcription_router.get("/my-subscription", response_model=EasybuySubscriptionResponse | None)
async def get_my_subscription(
    session: AsyncSession = Depends(async_get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get the current user's easybuy subscription"""
    subscription = await easybuy_subscription_service.get_subscription_by_user_id(current_user.id, session)
    if not subscription:
        return None
    return subscription


@easybuy_subcription_router.get("/renew_subcription/{subscription_id}", response_model=EasybuySubscriptionResponse)
async def renew_subscription(subscription_id: UUID, session: AsyncSession = Depends(async_get_db), _: UserResponse = Depends(get_current_user)):
    """Renew an existing easybuy subscription"""
    renewed_subscription = await easybuy_subscription_service.renew_subscription(subscription_id, session)
    if not renewed_subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Subscription not found")
    await activity_service.create_user_activity(
        user_id=_.id,
        activity_type="update",
        description=f"you have renewed your subscription with ID: {subscription_id}",
        session=session,
    )
    return renewed_subscription


@easybuy_subcription_router.post("/update_plan", response_model=EasybuySubscriptionResponse)
async def update_subscription_plan(plan: EasybuyChangeSubscriptionPlan, session: AsyncSession = Depends(async_get_db), _: UserResponse = Depends(get_current_user)):
    """Update the plan of an existing easybuy subscription"""
    updated_subscription = await easybuy_subscription_service.update_subscription_plan(plan.subscription_id, plan.plan_id, session)
    if not updated_subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Subscription not found")
    await activity_service.create_user_activity(
        user_id=_.id,
        activity_type="update",
        description=f"Updated subscription with ID: {plan.subscription_id} to plan ID: {plan.plan_id}",
        session=session,
    )
    return updated_subscription


@easybuy_subcription_router.post("/update_status", response_model=EasybuySubscriptionResponse)
async def update_subscription_status(subscription: EasybuyChangeSubscriptionStatus, session: AsyncSession = Depends(async_get_db), _: UserResponse = Depends(get_current_user)):
    """Update the status of an existing easybuy subscription"""
    updated_subscription = await easybuy_subscription_service.update_subscription_status(subscription.subscription_id, subscription.status, session)
    if not updated_subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Subscription not found")
    await activity_service.create_user_activity(
        user_id=_.id,
        activity_type="update",
        description=f"Updated subscription with ID: {subscription.subscription_id} to status: {subscription.status}",
        session=session,
    )
    return updated_subscription


@easybuy_subcription_router.get("/{subscription_id}", response_model=EasybuySubscriptionResponse)
async def get_subscription(subscription_id: UUID, session: AsyncSession = Depends(async_get_db), _: UserResponse = Depends(get_current_user)):
    """Get an easybuy subscription by ID"""
    subscription = await easybuy_subscription_service.get_subscription_by_id(subscription_id, session)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Subscription not found")
    return subscription


@easybuy_subcription_router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(subscription_id: UUID, session: AsyncSession = Depends(async_get_db), _: UserResponse = Depends(get_current_user)):
    """Delete an easybuy subscription"""
    deleted = await easybuy_subscription_service.delete_subscription(subscription_id, session)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Subscription not found")
    await activity_service.create_user_activity(
        user_id=_.id,
        activity_type="delete",
        description=f"Deleted easybuy subscription with ID: {subscription_id}",
        session=session,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
