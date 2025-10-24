"""
Promo Code API Routes

Endpoints for validating and applying promo codes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import structlog

from app.db.session import SessionLocal
from app.services.promo_code_service import PromoCodeService
from app.auth.dependencies import get_current_user
from app.auth.permissions import User

logger = structlog.get_logger(__name__)
router = APIRouter()


def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ValidatePromoRequest(BaseModel):
    """Request to validate a promo code."""
    code: str = Field(..., description="Promo code to validate")
    amount: float = Field(..., description="Booking amount", gt=0)
    currency: str = Field(default="NGN", description="Currency code")


class PromoCodeResponse(BaseModel):
    """Promo code validation response."""
    valid: bool
    code: str | None = None
    description: str | None = None
    discount_type: str | None = None
    discount_value: float | None = None
    discount_amount: float | None = None
    original_amount: float | None = None
    final_amount: float | None = None
    savings: float | None = None
    error: str | None = None


@router.post("/v1/promo-codes/validate", response_model=PromoCodeResponse)
async def validate_promo_code(
    request: ValidatePromoRequest,
    db: Session = Depends(get_db)
):
    """
    Validate a promo code and calculate discount.

    **Request Body:**
    - `code`: Promo code to validate
    - `amount`: Original booking amount
    - `currency`: Currency code (default: NGN)

    **Response:**
    - `valid`: Whether the promo code is valid
    - `discount_amount`: Amount of discount
    - `final_amount`: Final amount after discount
    - `error`: Error message if invalid
    """
    try:
        result = PromoCodeService.validate_promo_code(
            db=db,
            code=request.code,
            amount=request.amount,
            currency=request.currency
        )

        return PromoCodeResponse(**result)

    except Exception as e:
        logger.error("promo_code_validation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate promo code"
        )


@router.get("/v1/promo-codes/active")
async def get_active_promo_codes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of currently active promo codes.

    **Authorization:** Requires admin role

    **Response:**
    List of active promo codes with details
    """
    # Only allow admins to see all active promos
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view all promo codes"
        )

    try:
        promos = PromoCodeService.get_active_promo_codes(db)

        return [
            {
                "id": p.id,
                "code": p.code,
                "description": p.description,
                "discount_type": p.discount_type,
                "discount_value": p.discount_value,
                "currency": p.currency,
                "max_uses": p.max_uses,
                "times_used": p.times_used,
                "min_purchase_amount": p.min_purchase_amount,
                "valid_until": p.valid_until.isoformat() if p.valid_until else None,
                "is_active": p.is_active
            }
            for p in promos
        ]

    except Exception as e:
        logger.error("get_promo_codes_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve promo codes"
        )
