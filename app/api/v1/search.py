from fastapi import APIRouter, Request, HTTPException, status, Query
from app.core.errors import upstream_error
from pydantic import BaseModel
from typing import List, Optional
from app.services.search_service import SearchService
from app.utils.ratelimit import limiter_search

router = APIRouter()
_service = SearchService()

class Slice(BaseModel):
    from_: str
    to: str
    date: str
    time_window: Optional[str] = None

class SearchRequest(BaseModel):
    slices: List[Slice]
    adults: int
    children: int = 0
    infants: int = 0
    cabin: Optional[str] = None
    max_stops: Optional[int] = None
    bags_included: Optional[bool] = True
    display_currency: Optional[str] = None

@router.post("/search")
async def search_flights(payload: SearchRequest, request: Request, page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100)):
    key = f"search:{request.client.host}"
    if not limiter_search.allow(key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    try:
        data = _service.search(payload.model_dump())
        total = len(data)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = data[start:end]
        return {"offers": page_items, "total": total, "page": page, "page_size": page_size}
    except RuntimeError as e:
        raise upstream_error("duffel", str(e))




