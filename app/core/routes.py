from fastapi import APIRouter
from app.api.v1.transactions.routes import wallet_router
from app.api.v1.transactions.routes import transaction_router
from app.api.v1.complaints.routes import complaint_router
from app.api.v1.easybuy.routes import easybuy_product_router, easybuy_plan_router, easybuy_subcription_router,easybuy_product_review_router
from app.api.v1.notifications.routes import notification_router
from fastapi import APIRouter
from app.api.v1.auth.routes.oauth_routes import oauth_router
from app.api.v1.auth.routes.routes import auth_router
from app.api.v1.auth.routes.user_routes import user_router
from app.api.v1.auth.routes.two_factor_routes import twoFA_router
from app.core.templates import email_preview_router
from app.api.v1.files.routes import file_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["authentication"])
router.include_router(twoFA_router, prefix="/auth", tags=["authentication (2FA)"])
router.include_router(oauth_router, prefix="/auth", tags=["authentication (oauth)"])
router.include_router(user_router, prefix="/user", tags=["user"])


router.include_router(email_preview_router, prefix="/preview/email", tags=["email preview"])
router.include_router(wallet_router, prefix="/wallets", tags=["wallets"])
router.include_router(transaction_router,
                      prefix="/transactions", tags=["transactions"])
router.include_router(
    complaint_router, prefix="/complaints", tags=["complaints"])
router.include_router(easybuy_product_router, prefix="/easybuy/products",
                      tags=["easybuy products"])
router.include_router(easybuy_product_review_router,
                      prefix="/easybuy/product-reviews", tags=["easybuy product reviews"])

router.include_router(easybuy_plan_router,
                      prefix="/easybuy/plans", tags=["easybuy plans"])
router.include_router(easybuy_subcription_router, prefix="/easybuy/subscriptions",
                      tags=["easybuy subscriptions"])
router.include_router(
    notification_router, prefix="/notifications", tags=["notifications"])

router.include_router(file_router, prefix="/files", tags=["files"])
