from fastapi import APIRouter

from .search import router as search_router
from .offers import router as offers_router
from .bookings import router as bookings_router
from .trips import router as trips_router
from .admin import router as admin_router
from .payments import router as payments_router
from .currency import router as currency_router
from .metadata import router as metadata_router

router = APIRouter()
router.include_router(search_router, tags=["search"])
router.include_router(offers_router, tags=["offers"])
router.include_router(bookings_router, tags=["booking"])
router.include_router(trips_router, tags=["trips"])
router.include_router(admin_router, tags=["admin"])
router.include_router(payments_router, tags=["payments"]) 
router.include_router(currency_router, tags=["currency"]) 
router.include_router(metadata_router, tags=["metadata"]) 
