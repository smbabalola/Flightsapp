from fastapi import APIRouter, HTTPException, Depends
from app.core.errors import upstream_error
from pydantic import BaseModel
from typing import List, Optional, Literal
from app.auth.dependencies import get_current_active_user
from app.models.models import User
from app.services.booking_service import BookingService

router = APIRouter()
_booking = BookingService()

class Passport(BaseModel):
    number_token: str
    expiry: str
    nationality: str

class Passenger(BaseModel):
    type: str
    title: Optional[str]
    first: str
    last: str
    dob: str
    passport: Passport

class Contacts(BaseModel):
    email: str
    phone: str

class BookRequest(BaseModel):
    offer_id: str
    passengers: List[Passenger]
    contacts: Contacts
    channel: str
    payment_method: Literal["card", "bank", "ussd"] = "card"
    offer: Optional[dict] = None  # Raw offer data with price info

@router.post("/book")
async def book(payload: BookRequest, current_user: User = Depends(get_current_active_user)):
    contacts = payload.contacts.model_dump()
    if not contacts.get("email"):
        contacts["email"] = current_user.email
    try:
        q = _booking.create_quote_and_payment_link(
            offer_id=payload.offer_id,
            contacts=contacts,
            raw_offer=payload.offer,
            channel=payload.channel,
            payment_method=payload.payment_method,
        )
        return {"payment_url": q["payment_url"], "reference": q["reference"], "quote_id": q["quote_id"]}
    except RuntimeError as e:
        raise upstream_error("paystack", str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))




