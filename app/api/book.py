"""Booking API wrapper for internal use."""
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel
from app.services.booking_service import BookingService

_booking = BookingService()


class PassportRequest(BaseModel):
    number_token: str
    expiry: str
    nationality: str


class PassengerRequest(BaseModel):
    type: str
    title: Optional[str]
    first: str
    last: str
    dob: str
    passport: PassportRequest


class ContactsRequest(BaseModel):
    email: str
    phone: str


class BookRequest(BaseModel):
    offer_id: str
    passengers: List[PassengerRequest]
    contacts: ContactsRequest
    channel: str
    payment_method: Literal["card", "bank", "ussd"] = "card"
    offer: Optional[dict] = None  # Raw offer data with price info


async def book_flight(payload: BookRequest) -> Dict[str, Any]:
    """Create booking and payment link.

    Args:
        payload: Booking request parameters

    Returns:
        Dict with payment_url, reference, and quote_id
    """
    contacts = payload.contacts.model_dump()

    q = _booking.create_quote_and_payment_link(
        offer_id=payload.offer_id,
        contacts=contacts,
        raw_offer=payload.offer,
        channel=payload.channel,
        payment_method=payload.payment_method,
    )

    return {
        "payment_link": q["payment_url"],
        "reference": q["reference"],
        "quote_id": q["quote_id"],
        "pnr": q["reference"]  # Using reference as PNR for now
    }
