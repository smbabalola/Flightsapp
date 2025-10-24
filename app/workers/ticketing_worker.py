import asyncio
from typing import Dict, Any
from app.db.session import SessionLocal
from app.repositories.repos import QuoteRepository, PaymentRepository
from app.repositories.trips_repo import TripRepository
from app.notifications.service import get_notification_service
from sqlalchemy import text

class TicketingWorker:
    def issue_after_payment(self, *, quote_id: int, payment_reference: str) -> Dict[str, Any]:
        # Simulate supplier order creation and ticket numbers
        pnr = "PNR" + payment_reference[-5:]
        etickets = [f"ET{payment_reference[-10:]}1", f"ET{payment_reference[-10:]}2"]

        with SessionLocal() as db:
            # Fetch quote to get contact info
            quote = db.execute(
                text("SELECT email, phone FROM quotes WHERE id = :id"),
                {"id": quote_id}
            ).fetchone()

            email = quote.email if quote else None
            phone = quote.phone if quote else None

            # Create trip record
            tr = TripRepository(db)
            trip = tr.create_trip(
                quote_id=quote_id,
                supplier_order_id=f"ORDER_{payment_reference}",
                pnr=pnr,
                etickets_csv=",".join(etickets),
                etickets_json=etickets,
                email=email,
                phone=phone,
                raw_order={"mock": True},
            )

            # Update quote with PNR
            try:
                db.execute(
                    text("UPDATE quotes SET pnr=:pnr WHERE id=:id"),
                    {"pnr": pnr, "id": quote_id}
                )
            except Exception:
                pass

            db.commit()

            # Get raw_offer from quote for flight details
            quote_obj = db.execute(
                text("SELECT raw_offer FROM quotes WHERE id = :id"),
                {"id": quote_id}
            ).fetchone()
            raw_offer = quote_obj.raw_offer if quote_obj else None

            # Send notifications using new notification service
            notification_service = get_notification_service()
            try:
                # Send email notification
                asyncio.run(
                    notification_service.send_eticket(
                        email=email or "unknown@example.com",
                        phone=phone,
                        pnr=pnr,
                        etickets=etickets
                    )
                )
            except Exception as e:
                # Log but don't fail ticket issuance
                print(f"Failed to send e-ticket notification: {e}")

            # Send WhatsApp confirmation with itinerary
            if phone:
                try:
                    asyncio.run(
                        notification_service.send_whatsapp_booking_confirmation(
                            phone=phone,
                            pnr=pnr,
                            etickets=etickets,
                            flight_details=raw_offer
                        )
                    )
                except Exception as e:
                    # Log but don't fail ticket issuance
                    print(f"Failed to send WhatsApp confirmation: {e}")

            return {"trip_id": trip.id, "pnr": pnr, "etickets": etickets}



