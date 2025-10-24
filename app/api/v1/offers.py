from fastapi import APIRouter, HTTPException, status
from app.core.errors import upstream_error
from app.services.search_service import SearchService

router = APIRouter()
_service = SearchService()

from pydantic import BaseModel
from typing import Optional


class PriceRequest(BaseModel):
    display_currency: Optional[str] = None


@router.post("/offers/{offer_id}/price")
async def price_offer(offer_id: str, payload: PriceRequest | None = None):
    try:
        return _service.price_offer(offer_id, display_currency=(payload.display_currency if payload else None))
    except RuntimeError as e:
        raise upstream_error("duffel", str(e))


