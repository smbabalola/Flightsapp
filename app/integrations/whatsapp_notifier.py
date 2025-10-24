"""
WhatsApp notification helper.

DEPRECATED: Use app.notifications.service.NotificationService.send_whatsapp_booking_confirmation instead.
"""
from typing import List
import asyncio
from app.core.logging import logger
from app.notifications.service import get_notification_service

def send_whatsapp_confirmation(phone: str | None, pnr: str | None, etickets: List[str] | None, flight_details: dict | None = None) -> None:
    """Send WhatsApp booking confirmation (DEPRECATED - use NotificationService directly).

    Args:
        phone: Customer phone number
        pnr: Booking reference
        etickets: List of e-ticket numbers
        flight_details: Optional flight details from raw_offer
    """
    if not phone or not pnr or not etickets:
        logger.info("whatsapp_send_skipped", extra={"phone": phone or "unknown", "pnr": pnr or "", "tickets_count": len(etickets or [])})
        return

    try:
        notification_service = get_notification_service()
        asyncio.run(
            notification_service.send_whatsapp_booking_confirmation(
                phone=phone,
                pnr=pnr,
                etickets=etickets,
                flight_details=flight_details
            )
        )
    except Exception as e:
        logger.error("whatsapp_send_error", extra={"error": str(e), "pnr": pnr})
