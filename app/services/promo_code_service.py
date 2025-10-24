from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import PromoCode, PromoCodeUsage
from typing import Dict, Optional


class PromoCodeService:
    """Service for managing promo codes and discounts"""

    @staticmethod
    def validate_promo_code(db: Session, code: str, amount: float, currency: str = 'NGN') -> Dict:
        """
        Validate a promo code and calculate discount.

        Args:
            db: Database session
            code: Promo code to validate
            amount: Original booking amount
            currency: Currency of the booking

        Returns:
            Dictionary with validation result and discount details
        """
        # Find promo code
        promo = db.query(PromoCode).filter(
            PromoCode.code == code.upper(),
            PromoCode.is_active == True
        ).first()

        if not promo:
            return {
                "valid": False,
                "error": "Invalid promo code"
            }

        # Check if promo code is expired
        now = datetime.utcnow()
        if promo.valid_until and promo.valid_until < now:
            return {
                "valid": False,
                "error": "Promo code has expired"
            }

        if promo.valid_from > now:
            return {
                "valid": False,
                "error": "Promo code is not yet valid"
            }

        # Check max uses
        if promo.max_uses and promo.times_used >= promo.max_uses:
            return {
                "valid": False,
                "error": "Promo code has reached maximum usage limit"
            }

        # Check minimum purchase amount
        if promo.min_purchase_amount and amount < promo.min_purchase_amount:
            min_display = f"₦{int(promo.min_purchase_amount):,}" if currency == 'NGN' else f"{currency} {promo.min_purchase_amount:.2f}"
            return {
                "valid": False,
                "error": f"Minimum purchase amount of {min_display} required"
            }

        # Calculate discount
        if promo.discount_type == 'percentage':
            discount_amount = amount * (promo.discount_value / 100)
        elif promo.discount_type == 'fixed':
            # For fixed discounts, ensure currency matches
            if promo.currency and promo.currency != currency:
                return {
                    "valid": False,
                    "error": f"Promo code is only valid for {promo.currency} transactions"
                }
            discount_amount = promo.discount_value
        else:
            return {
                "valid": False,
                "error": "Invalid promo code configuration"
            }

        # Ensure discount doesn't exceed total amount
        discount_amount = min(discount_amount, amount)
        final_amount = amount - discount_amount

        return {
            "valid": True,
            "promo_code_id": promo.id,
            "code": promo.code,
            "description": promo.description,
            "discount_type": promo.discount_type,
            "discount_value": promo.discount_value,
            "discount_amount": round(discount_amount, 2),
            "original_amount": round(amount, 2),
            "final_amount": round(final_amount, 2),
            "savings": round(discount_amount, 2)
        }

    @staticmethod
    def apply_promo_code(
        db: Session,
        promo_code_id: int,
        user_id: Optional[int],
        trip_id: Optional[int],
        original_amount: float,
        discount_amount: float,
        final_amount: float
    ) -> PromoCodeUsage:
        """
        Record promo code usage and increment usage counter.

        Args:
            db: Database session
            promo_code_id: ID of the promo code
            user_id: ID of the user (optional)
            trip_id: ID of the trip (optional)
            original_amount: Original booking amount
            discount_amount: Discount applied
            final_amount: Final amount after discount

        Returns:
            PromoCodeUsage record
        """
        # Create usage record
        usage = PromoCodeUsage(
            promo_code_id=promo_code_id,
            user_id=user_id,
            trip_id=trip_id,
            original_amount=original_amount,
            discount_amount=discount_amount,
            final_amount=final_amount
        )
        db.add(usage)

        # Increment usage counter
        promo = db.query(PromoCode).filter(PromoCode.id == promo_code_id).first()
        if promo:
            promo.times_used += 1

        db.commit()
        db.refresh(usage)

        return usage

    @staticmethod
    def create_promo_code(
        db: Session,
        code: str,
        discount_type: str,
        discount_value: float,
        description: Optional[str] = None,
        currency: Optional[str] = None,
        max_uses: Optional[int] = None,
        min_purchase_amount: Optional[float] = None,
        valid_until: Optional[datetime] = None,
        created_by: Optional[str] = None
    ) -> PromoCode:
        """
        Create a new promo code.

        Args:
            db: Database session
            code: Promo code (will be uppercased)
            discount_type: 'percentage' or 'fixed'
            discount_value: Percentage (e.g., 10 for 10%) or fixed amount
            description: Description of the promo
            currency: Currency for fixed discounts
            max_uses: Maximum number of uses (None = unlimited)
            min_purchase_amount: Minimum purchase required
            valid_until: Expiry date (None = no expiry)
            created_by: User who created the promo

        Returns:
            Created PromoCode
        """
        promo = PromoCode(
            code=code.upper(),
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            currency=currency,
            max_uses=max_uses,
            min_purchase_amount=min_purchase_amount,
            valid_until=valid_until,
            created_by=created_by
        )

        db.add(promo)
        db.commit()
        db.refresh(promo)

        return promo

    @staticmethod
    def get_active_promo_codes(db: Session) -> list[PromoCode]:
        """Get all active promo codes"""
        return db.query(PromoCode).filter(
            PromoCode.is_active == True,
            PromoCode.valid_until >= datetime.utcnow()
        ).all()

    @staticmethod
    def deactivate_promo_code(db: Session, code: str) -> bool:
        """Deactivate a promo code"""
        promo = db.query(PromoCode).filter(PromoCode.code == code.upper()).first()
        if not promo:
            return False

        promo.is_active = False
        db.commit()
        return True
