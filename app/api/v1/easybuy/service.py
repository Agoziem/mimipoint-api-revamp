from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from .schemas import *
from .models import EasybuyPlan, EasybuySubscription, Product, ProductReview
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import desc
from sqlalchemy.orm import selectinload


class EasybuyService:
    async def get_plans(self, session: AsyncSession,  limit: int = 10, offset: int = 0) -> List[EasybuyPlan]:
        """Retrieve all Easybuy plans with pagination"""
        statement = select(EasybuyPlan).limit(limit).offset(offset)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_plan_by_id(self, plan_id: UUID, session: AsyncSession) -> Optional[EasybuyPlan]:
        """Retrieve an Easybuy plan by ID"""
        statement = select(EasybuyPlan).where(EasybuyPlan.id == plan_id)
        result = await session.execute(statement)
        return result.scalars().first()

    async def create_plan(self, plan_data: EasybuyPlanCreate, session: AsyncSession) -> EasybuyPlan:
        """Create a new Easybuy plan"""
        plan_data_dict = plan_data.model_dump()
        new_plan = EasybuyPlan(**plan_data_dict)
        session.add(new_plan)
        await session.commit()
        await session.refresh(new_plan)
        return new_plan

    async def update_plan(self, plan_id: UUID, plan_data: EasybuyPlanCreate, session: AsyncSession) -> Optional[EasybuyPlan]:
        """Update an existing Easybuy plan"""
        plan = await self.get_plan_by_id(plan_id, session)
        if plan:
            for key, value in plan_data.model_dump(exclude_unset=True).items():
                setattr(plan, key, value)
            await session.commit()
            await session.refresh(plan)
            return plan
        return None

    async def delete_plan(self, plan_id: UUID, session: AsyncSession) -> bool:
        """Delete an Easybuy plan by ID"""
        plan = await self.get_plan_by_id(plan_id, session)
        if plan:
            await session.delete(plan)
            await session.commit()
            return True
        return False


class EasybuySubscriptionService:
    def get_subscription_duration(self, plan: EasybuyPlan) -> float:
        """
        Returns the duration of the subscription plan in days based on the billing cycle.
        """
        if plan.billing_cycle == BillingCycleEnum.MONTHLY:
            return 30
        elif plan.billing_cycle == BillingCycleEnum.ANNUALLY:
            return 365
        else:
            raise ValueError("Invalid billing cycle")

    async def get_subscriptions(self, session: AsyncSession, limit: int = 50, offset: int = 0) -> List[EasybuySubscription]:
        """Retrieve all Easybuy subscriptions with pagination"""
        statement = select(EasybuySubscription).order_by(
            desc(EasybuySubscription.created_at)).limit(limit).offset(offset)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_subscription_by_id(self, subscription_id: UUID, session: AsyncSession) -> Optional[EasybuySubscription]:
        """Retrieve an Easybuy subscription by ID"""
        statement = select(EasybuySubscription).options(
            selectinload(EasybuySubscription.plan),
            selectinload(EasybuySubscription.user)).where(
                EasybuySubscription.id == subscription_id)
        result = await session.execute(statement)
        return result.scalars().first()

    async def get_subscription_by_user_id(self, user_id: UUID, session: AsyncSession) -> Optional[EasybuySubscription]:
        """Retrieve the subscription for a specific user"""
        statement = select(EasybuySubscription).options(
            selectinload(EasybuySubscription.plan),
            selectinload(EasybuySubscription.user)).where(
            EasybuySubscription.user_id == user_id)
        result = await session.execute(statement)
        return result.scalars().first()

    async def create_subscription(
            self, subscription_data: EasybuySubscriptionCreate,
            session: AsyncSession
    ) -> Optional[EasybuySubscription]:
        """Create a new subscription for a user"""
        existing = await self.get_subscription_by_user_id(subscription_data.user_id, session)
        if existing:
            await self.delete_subscription(existing.id, session)

        plan = await session.get(EasybuyPlan, subscription_data.plan_id)
        if not plan:
            raise HTTPException(
                status_code=404, detail="Subscription plan not found")

        start_date = datetime.now(timezone.utc)
        end_date = start_date + \
            timedelta(days=self.get_subscription_duration(plan))

        subscription = EasybuySubscription(
            user_id=subscription_data.user_id,
            plan_id=subscription_data.plan_id,
            status=subscription_data.status.value,
            start_date=start_date,
            end_date=end_date
        )

        session.add(subscription)
        await session.commit()
        new_subscription = await self.get_subscription_by_id(subscription.id, session)
        if not new_subscription:
            return None
        return new_subscription

    async def delete_subscription(self, subscription_id: UUID, session: AsyncSession) -> bool:
        """Delete a subscription"""
        subscription = await self.get_subscription_by_id(subscription_id, session)
        if not subscription:
            raise HTTPException(
                status_code=404, detail="Subscription not found")

        await session.delete(subscription)
        await session.commit()
        return True

    async def update_subscription_status(self, subscription_id: UUID, status: SubscriptionStatus, session: AsyncSession) -> EasybuySubscription:
        """Update the status of a subscription"""
        subscription = await self.get_subscription_by_id(subscription_id, session)
        if not subscription:
            raise HTTPException(
                status_code=404, detail="Subscription not found")

        subscription.status = status.value
        await session.commit()
        await session.refresh(subscription)
        return subscription

    async def update_subscription_plan(self, subscription_id: UUID, plan_id: UUID, session: AsyncSession) -> EasybuySubscription:
        """Update the plan of a subscription"""
        subscription = await self.get_subscription_by_id(subscription_id, session)
        if not subscription:
            raise HTTPException(
                status_code=404, detail="Subscription not found")

        plan = await session.get(EasybuyPlan, plan_id)
        if not plan:
            raise HTTPException(
                status_code=404, detail="Subscription plan not found")

        subscription.plan_id = plan_id
        subscription.start_date = datetime.now(timezone.utc)
        subscription.end_date = subscription.start_date + \
            timedelta(days=self.get_subscription_duration(plan))

        await session.commit()
        await session.refresh(subscription)
        return subscription

    async def renew_subscription(self, subscription_id: UUID, session: AsyncSession) -> EasybuySubscription:
        """Renew a subscription"""
        subscription = await self.get_subscription_by_id(subscription_id, session)
        if not subscription:
            raise HTTPException(
                status_code=404, detail="Subscription not found")

        plan = await session.get(EasybuyPlan, subscription.plan_id)
        if not plan:
            raise HTTPException(
                status_code=404, detail="Subscription plan not found")

        subscription.start_date = datetime.now(timezone.utc)
        subscription.end_date = datetime.now(
            timezone.utc) + timedelta(days=self.get_subscription_duration(plan))

        await session.commit()
        await session.refresh(subscription)
        return subscription


class ProductService:
    async def get_products(self, session: AsyncSession, limit: int = 50, offset: int = 0) -> List[Product]:
        """Retrieve all products with pagination"""
        statement = select(Product).options(
            selectinload(Product.owner)
        ).order_by(
            desc(Product.created_at)).limit(limit).offset(offset)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_user_products(self, user_id: UUID, session: AsyncSession, limit: int = 50, offset: int = 0) -> List[Product]:
        """Retrieve all products for a specific user with pagination"""
        statement = select(Product).where(
            Product.owner_id == user_id).order_by(desc(Product.created_at)).limit(limit).offset(offset)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_product_by_id(self, product_id: UUID, session: AsyncSession) -> Optional[Product]:
        """Retrieve a product by ID"""
        statement = select(Product).options(
            selectinload(Product.owner)
        ).where(Product.id == product_id)
        result = await session.execute(statement)
        return result.scalars().first()

    async def create_product(self, product_data: ProductCreate, session: AsyncSession) -> Product:
        """Create a new product"""
        product_data_dict = product_data.model_dump()
        new_product = Product(**product_data_dict)
        session.add(new_product)
        await session.commit()
        await session.refresh(new_product)
        return new_product

    async def update_product(self, product_id: UUID, product_data: ProductCreate, session: AsyncSession) -> Optional[Product]:
        """Update an existing product"""
        product = await self.get_product_by_id(product_id, session)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        for key, value in product_data.model_dump(exclude_unset=True).items():
            setattr(product, key, value)

        await session.commit()
        await session.refresh(product)
        return product

    async def delete_product(self, product_id: UUID, session: AsyncSession) -> bool:
        """Delete a product by ID"""
        product = await self.get_product_by_id(product_id, session)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        await session.delete(product)
        await session.commit()
        return True

    async def search_products(
            self,
            query: str,
            session: AsyncSession,
            limit: int = 50,
            offset: int = 0
    ) -> List[Product]:
        """Search for products by name or description"""
        if not query:
            return []

        # Use a case-insensitive search
        statement = select(Product).where(
            (Product.name.ilike(f"%{query}%")) | (
                Product.description.ilike(f"%{query}%"))
        ).order_by(desc(Product.created_at)).limit(limit).offset(offset)

        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_products_by_category(
            self,
            category: ProductCategoryEnum,
            session: AsyncSession,
            limit: int = 50,
            offset: int = 0
    ) -> List[Product]:
        """Retrieve products by category with pagination"""
        statement = select(Product).where(
            Product.category == category
        ).order_by(desc(Product.created_at)).limit(limit).offset(offset)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_product_reviews(
            self, product_id: UUID,
            session: AsyncSession,
            limit: int = 50,
            offset: int = 0
    ) -> List[ProductReview]:
        """Retrieve all reviews for a specific product with pagination"""
        statement = select(ProductReview).options(
            selectinload(ProductReview.user)).where(
            ProductReview.product_id == product_id
        ).order_by(desc(ProductReview.created_at)).limit(limit).offset(offset)
        result = await session.execute(statement)
        return list(result.scalars().all())
    
    async def get_product_review_by_id(
            self,
            review_id: UUID,
            session: AsyncSession
    ) -> Optional[ProductReview]:
        """Retrieve a product review by ID"""
        statement = select(ProductReview).options(
            selectinload(ProductReview.user)).where(
            ProductReview.id == review_id)
        result = await session.execute(statement)
        return result.scalars().first()

    async def create_product_review(
            self,
            review_data: ProductReviewCreate,
            session: AsyncSession
    ) -> ProductReview:
        """Create a new product review"""
        product = await self.get_product_by_id(review_data.product_id, session)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        review_data_dict = review_data.model_dump()
        new_review = ProductReview(**review_data_dict)
        print("Creating product review:", new_review)
        session.add(new_review)
        await session.commit()
        await session.refresh(new_review)
        return await self.get_product_review_by_id(new_review.id, session)

    async def update_product_review(
            self,
            review_id: UUID,
            review_data: ProductReviewCreate,
            session: AsyncSession
    ) -> Optional[ProductReview]:
        """Update an existing product review"""
        review = await session.get(ProductReview, review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        for key, value in review_data.model_dump(exclude_unset=True).items():
            setattr(review, key, value)

        await session.commit()
        await session.refresh(review)
        return await self.get_product_review_by_id(review.id, session)

    async def delete_product_review(
            self,
            review_id: UUID,
            session: AsyncSession
    ) -> bool:
        """Delete a product review by ID"""
        review = await session.get(ProductReview, review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        await session.delete(review)
        await session.commit()
        return True
