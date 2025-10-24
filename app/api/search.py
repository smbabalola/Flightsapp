"""Search API wrapper for internal use."""
from typing import List, Dict, Any
from app.services.search_service import SearchService
from pydantic import BaseModel
from typing import List, Optional

_service = SearchService()


class SliceRequest(BaseModel):
    from_: str
    to: str
    date: str
    time_window: Optional[str] = None


class SearchRequest(BaseModel):
    slices: List[SliceRequest]
    adults: int = 1
    children: int = 0
    infants: int = 0
    cabin: Optional[str] = None
    max_stops: Optional[int] = None
    bags_included: Optional[bool] = True


async def search_flights(payload: SearchRequest) -> List[Dict[str, Any]]:
    """Search for flights.

    Args:
        payload: Search request parameters

    Returns:
        List of flight offers
    """
    data = _service.search(payload.model_dump())
    return data
