"""
Cancellation API Routes

Customer-facing endpoints for requesting and checking cancellations.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import structlog

from app.db.session import SessionLocal
from app.services.cancellation_service import get_cancellation_service

logger = structlog.get_logger(__name__)
router = APIRouter()


class CancellationRequest(BaseModel):
    """Request to cancel a booking."""
    trip_id: int = Field(..., description="Trip ID to cancel")
    reason: Optional[str] = Field(None, description="Reason for cancellation")


class CancellationResponse(BaseModel):
    """Cancellation response."""
    cancellation_id: int
    trip_id: int
    pnr: str
    status: str
    refund_amount: Optional[float] = None
    refund_currency: Optional[str] = None


def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/v1/cancellations", response_model=CancellationResponse)
async def request_cancellation(
    request: CancellationRequest,
    db = Depends(get_db)
):
    """
    Request cancellation for a booking.

    This creates a pending cancellation request that will be processed by the admin team.

    **Request Body:**
    - `trip_id`: ID of the trip to cancel
    - `reason`: Optional reason for cancellation

    **Response:**
    - `cancellation_id`: ID of the cancellation request
    - `status`: Current status (pending, confirmed, failed)
    - `refund_amount`: Refund amount (if confirmed)
    - `refund_currency`: Refund currency (if confirmed)
    """
    try:
        service = get_cancellation_service(db)
        result = service.request_cancellation(
            trip_id=request.trip_id,
            reason=request.reason,
            cancelled_by="customer"
        )

        return CancellationResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("cancellation_request_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process cancellation request")


@router.get("/v1/cancellations/{cancellation_id}", response_model=CancellationResponse)
async def get_cancellation_status(
    cancellation_id: int,
    db = Depends(get_db)
):
    """
    Get status of a cancellation request.

    **Path Parameters:**
    - `cancellation_id`: ID of the cancellation request

    **Response:**
    - `cancellation_id`: ID of the cancellation request
    - `trip_id`: Trip ID
    - `pnr`: Booking reference
    - `status`: Current status (pending, confirmed, failed)
    - `refund_amount`: Refund amount (if confirmed)
    - `refund_currency`: Refund currency (if confirmed)
    """
    try:
        service = get_cancellation_service(db)
        result = service.get_cancellation_status(cancellation_id)

        return CancellationResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("get_cancellation_status_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve cancellation status")
