"""
Cancellation Service

Handles booking cancellations, refunds, and notifications.
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
import structlog

from app.models.models import Cancellation
from app.integrations.duffel_client import DuffelClient
from app.notifications.service import get_notification_service

logger = structlog.get_logger(__name__)


class CancellationService:
    """Service for handling booking cancellations."""

    def __init__(self, db: Session):
        self.db = db
        self.duffel_client = DuffelClient()
        self.notification_service = get_notification_service()

    def request_cancellation(
        self,
        trip_id: int,
        reason: Optional[str] = None,
        cancelled_by: str = "customer"
    ) -> Dict[str, Any]:
        """
        Request cancellation for a trip.

        Args:
            trip_id: Trip ID to cancel
            reason: Cancellation reason
            cancelled_by: Who initiated (customer, admin, system)

        Returns:
            Cancellation details
        """
        # Get trip details
        trip = self.db.execute(
            text("""
                SELECT
                    t.id, t.quote_id, t.supplier_order_id, t.pnr,
                    t.email, t.phone, t.status,
                    q.currency, q.price_minor
                FROM trips t
                JOIN quotes q ON t.quote_id = q.id
                WHERE t.id = :trip_id
            """),
            {"trip_id": trip_id}
        ).fetchone()

        if not trip:
            raise ValueError(f"Trip {trip_id} not found")

        if trip.status == "cancelled":
            raise ValueError(f"Trip {trip_id} is already cancelled")

        # Create cancellation record
        cancellation = Cancellation(
            trip_id=trip_id,
            quote_id=trip.quote_id,
            reason=reason,
            status="pending",
            cancelled_by=cancelled_by,
        )
        self.db.add(cancellation)
        self.db.flush()

        # Send pending notification
        try:
            asyncio.run(
                self.notification_service.send_cancellation_pending(
                    email=trip.email or "unknown@example.com",
                    phone=trip.phone,
                    pnr=trip.pnr or f"TRIP{trip_id}"
                )
            )
        except Exception as e:
            logger.error("cancellation_notification_failed", error=str(e))

        self.db.commit()

        logger.info(
            "cancellation_requested",
            trip_id=trip_id,
            cancellation_id=cancellation.id,
            cancelled_by=cancelled_by
        )

        return {
            "cancellation_id": cancellation.id,
            "trip_id": trip_id,
            "status": "pending",
            "pnr": trip.pnr,
        }

    def process_cancellation(
        self,
        cancellation_id: int,
        admin_user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a pending cancellation.

        Args:
            cancellation_id: Cancellation ID to process
            admin_user: Admin processing the cancellation

        Returns:
            Processed cancellation details
        """
        # Get cancellation details
        result = self.db.execute(
            text("""
                SELECT
                    c.id, c.trip_id, c.quote_id, c.status,
                    t.supplier_order_id, t.pnr, t.email, t.phone,
                    q.currency, q.price_minor
                FROM cancellations c
                JOIN trips t ON c.trip_id = t.id
                JOIN quotes q ON c.quote_id = q.id
                WHERE c.id = :cancellation_id
            """),
            {"cancellation_id": cancellation_id}
        ).fetchone()

        if not result:
            raise ValueError(f"Cancellation {cancellation_id} not found")

        if result.status != "pending":
            raise ValueError(f"Cancellation {cancellation_id} is not pending")

        # Cancel with supplier (Duffel)
        try:
            duffel_cancellation = self.duffel_client.cancel_order(
                result.supplier_order_id or "mock_order"
            )

            # Parse refund amount
            refund_amount = float(duffel_cancellation.get("refund_amount", "0"))
            refund_currency = duffel_cancellation.get("refund_currency", result.currency)

            # Convert to minor units
            refund_amount_minor = int(refund_amount * 100)

            # Update cancellation record
            self.db.execute(
                text("""
                    UPDATE cancellations
                    SET
                        status = :status,
                        refund_amount_minor = :refund_minor,
                        refund_currency = :refund_currency,
                        supplier_cancellation_id = :supplier_id,
                        raw_cancellation = :raw,
                        completed_at = :completed_at
                    WHERE id = :id
                """),
                {
                    "id": cancellation_id,
                    "status": "confirmed",
                    "refund_minor": refund_amount_minor,
                    "refund_currency": refund_currency,
                    "supplier_id": duffel_cancellation.get("id"),
                    "raw": duffel_cancellation,
                    "completed_at": datetime.utcnow(),
                }
            )

            # Update trip status
            self.db.execute(
                text("UPDATE trips SET status = :status WHERE id = :id"),
                {"status": "cancelled", "id": result.trip_id}
            )

            # Update quote status
            self.db.execute(
                text("UPDATE quotes SET status = :status WHERE id = :id"),
                {"status": "cancelled", "id": result.quote_id}
            )

            self.db.commit()

            # Send confirmation notification
            try:
                asyncio.run(
                    self.notification_service.send_cancellation_confirmed(
                        email=result.email or "unknown@example.com",
                        phone=result.phone,
                        pnr=result.pnr or f"TRIP{result.trip_id}",
                        refund_amount=refund_amount,
                        currency=refund_currency
                    )
                )
            except Exception as e:
                logger.error("cancellation_confirmation_notification_failed", error=str(e))

            logger.info(
                "cancellation_processed",
                cancellation_id=cancellation_id,
                trip_id=result.trip_id,
                refund_amount=refund_amount,
                refund_currency=refund_currency
            )

            return {
                "cancellation_id": cancellation_id,
                "trip_id": result.trip_id,
                "status": "confirmed",
                "refund_amount": refund_amount,
                "refund_currency": refund_currency,
                "pnr": result.pnr,
            }

        except Exception as e:
            # Mark cancellation as failed
            self.db.execute(
                text("""
                    UPDATE cancellations
                    SET status = :status
                    WHERE id = :id
                """),
                {"id": cancellation_id, "status": "failed"}
            )
            self.db.commit()

            logger.error(
                "cancellation_processing_failed",
                cancellation_id=cancellation_id,
                error=str(e)
            )
            raise

    def get_cancellation_status(self, cancellation_id: int) -> Dict[str, Any]:
        """Get status of a cancellation request."""
        result = self.db.execute(
            text("""
                SELECT
                    c.id, c.trip_id, c.status, c.refund_amount_minor,
                    c.refund_currency, c.created_at, c.completed_at,
                    t.pnr
                FROM cancellations c
                JOIN trips t ON c.trip_id = t.id
                WHERE c.id = :cancellation_id
            """),
            {"cancellation_id": cancellation_id}
        ).fetchone()

        if not result:
            raise ValueError(f"Cancellation {cancellation_id} not found")

        refund_amount = None
        if result.refund_amount_minor:
            refund_amount = result.refund_amount_minor / 100

        return {
            "cancellation_id": result.id,
            "trip_id": result.trip_id,
            "pnr": result.pnr,
            "status": result.status,
            "refund_amount": refund_amount,
            "refund_currency": result.refund_currency,
            "created_at": result.created_at,
            "completed_at": result.completed_at,
        }


# Singleton instance getter
_cancellation_service: Optional[CancellationService] = None


def get_cancellation_service(db: Session) -> CancellationService:
    """Get cancellation service instance."""
    return CancellationService(db)
