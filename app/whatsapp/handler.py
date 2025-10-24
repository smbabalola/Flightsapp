"""
Main conversational flow handler for WhatsApp booking.

Orchestrates the complete booking flow from search to payment.
"""
from typing import Dict, Any, Optional
import structlog
from app.whatsapp.client import get_whatsapp_client
from app.whatsapp.session import get_session_manager, ConversationState
from app.whatsapp.parser import MessageParser, Intent, extract_message_text
from app.api.search import search_flights
from app.api.book import book_flight
from app.models.search import SearchRequest, SliceRequest
from app.models.book import BookRequest, PassengerRequest, ContactsRequest, PassportRequest
from app.utils.fx import ngn_equivalent

logger = structlog.get_logger(__name__)


class ConversationHandler:
    """Handles WhatsApp conversation flow and state transitions."""

    def __init__(self):
        self.client = get_whatsapp_client()
        self.session_mgr = get_session_manager()
        self.parser = MessageParser()

    async def handle_message(self, webhook_data: Dict[str, Any]) -> None:
        """Process incoming WhatsApp message and respond.

        Args:
            webhook_data: WhatsApp webhook payload
        """
        # Extract message text and sender
        result = extract_message_text(webhook_data)
        if not result:
            logger.warning("no_message_found", data=webhook_data)
            return

        phone, text = result
        logger.info("message_received", phone=phone, text=text[:100])

        # Get session
        session = await self.session_mgr.get_session(phone)

        # Parse intent
        intent = self.parser.parse_intent(text, session.state.value)
        logger.info("intent_detected", phone=phone, intent=intent.value, state=session.state.value)

        # Route to appropriate handler
        if intent == Intent.START:
            await self._handle_start(phone, session)
        elif intent == Intent.HELP:
            await self._handle_help(phone)
        elif intent == Intent.CANCEL:
            await self._handle_cancel(phone, session)
        elif intent == Intent.STATUS:
            await self._handle_status(phone, session)
        elif intent == Intent.SEARCH_FLIGHT:
            await self._handle_search(phone, text, session)
        elif intent == Intent.SELECT_OPTION:
            await self._handle_selection(phone, text, session)
        elif intent == Intent.PROVIDE_PASSENGER:
            await self._handle_passenger(phone, text, session)
        elif intent == Intent.CONFIRM_BOOKING:
            await self._handle_confirmation(phone, session)
        else:
            await self._handle_unknown(phone, session)

    async def _handle_start(self, phone: str, session: Any) -> None:
        """Handle start/greeting."""
        welcome = (
            "✈️ Welcome to SureFlights!\n\n"
            "I'll help you book flights across Nigeria.\n\n"
            "*To search for flights, just tell me:*\n"
            "• Where you're flying from\n"
            "• Where you're going to\n"
            "• Your travel date\n\n"
            "_Example: \"Flight from Lagos to Abuja on 2025-11-15\"_\n\n"
            "Type *help* anytime for assistance."
        )
        await self.client.send_text(phone, welcome)
        await self.session_mgr.update_state(phone, ConversationState.INITIAL)

    async def _handle_help(self, phone: str) -> None:
        """Handle help request."""
        help_text = (
            "🆘 *SureFlights Help*\n\n"
            "*How to search flights:*\n"
            '• "Flight from Lagos to Abuja on Nov 15"\n'
            '• "LOS to ABV tomorrow"\n\n'
            "*Commands:*\n"
            "• start - Start new booking\n"
            "• status - Check booking status\n"
            "• cancel - Cancel current booking\n"
            "• help - Show this help\n\n"
            "*Supported cities:*\n"
            "Lagos (LOS), Abuja (ABV), Port Harcourt (PHC), "
            "Kano (KAN), Enugu (ENU), and more"
        )
        await self.client.send_text(phone, help_text)

    async def _handle_cancel(self, phone: str, session: Any) -> None:
        """Handle cancellation."""
        await self.session_mgr.clear_session(phone)
        await self.client.send_text(
            phone,
            "❌ Booking cancelled. Type *start* to begin a new search."
        )

    async def _handle_status(self, phone: str, session: Any) -> None:
        """Handle status check."""
        if session.booking_reference:
            status_text = (
                f"📋 *Your Booking*\n\n"
                f"Reference: {session.booking_reference}\n"
            )
            if session.payment_link:
                status_text += f"\n💳 Payment: {session.payment_link}"
            await self.client.send_text(phone, status_text)
        else:
            await self.client.send_text(
                phone,
                "No active booking found. Type *start* to begin."
            )

    async def _handle_search(self, phone: str, text: str, session: Any) -> None:
        """Handle flight search."""
        # Parse search parameters
        params = self.parser.parse_flight_search(text)

        if not params:
            await self.client.send_text(
                phone,
                "❓ I couldn't understand your search. Please include:\n"
                "• Origin city\n"
                "• Destination city\n"
                "• Travel date\n\n"
                '_Example: "Lagos to Abuja on 2025-11-15"_'
            )
            return

        # Save search params
        session.search_params = params
        await self.session_mgr.save_session(session)

        # Perform search
        await self.client.send_text(phone, "🔍 Searching for flights...")

        try:
            search_req = SearchRequest(
                slices=[SliceRequest(**params)],
                adults=params.get("adults", 1)
            )
            offers = await search_flights(search_req)

            if not offers:
                await self.client.send_text(
                    phone,
                    "😔 No flights found for your search. Try different dates?"
                )
                return

            # Store offers and show results
            session.offers = offers
            await self.session_mgr.update_state(phone, ConversationState.VIEWING_RESULTS)

            # Format and send results
            await self._send_flight_results(phone, offers, params)

        except Exception as e:
            logger.error("search_error", phone=phone, error=str(e))
            await self.client.send_text(
                phone,
                "⚠️ Search failed. Please try again later."
            )

    async def _send_flight_results(self, phone: str, offers: list, params: Dict[str, Any]) -> None:
        """Format and send flight results."""
        route = f"{params['from_']} → {params['to']}"
        date = params['date']

        header = f"✈️ *Flights: {route}*\n📅 {date}\n"

        # Show top 5 offers
        results_text = header + "\n"
        for i, offer in enumerate(offers[:5], 1):
            price_ngn = offer.get("price_ngn") or offer.get("price", 0)
            currency = offer.get("currency", "NGN")

            # Format price
            if currency == "NGN":
                price_display = f"₦{price_ngn:,.0f}"
            else:
                price_display = f"{currency} {offer['price']:,.2f}"

            # Extract flight details
            slices = offer.get("slices", [{}])
            first_slice = slices[0] if slices else {}
            segments = first_slice.get("segments", [{}])
            first_seg = segments[0] if segments else {}

            airline = first_seg.get("airline", "Unknown")
            departure_time = first_seg.get("departure_time", "")[:5] if first_seg.get("departure_time") else "N/A"
            arrival_time = first_seg.get("arrival_time", "")[:5] if first_seg.get("arrival_time") else "N/A"
            duration = first_slice.get("duration_minutes", 0)
            hours = duration // 60
            mins = duration % 60

            results_text += (
                f"\n*{i}. {airline}*\n"
                f"   🕐 {departure_time} → {arrival_time} ({hours}h {mins}m)\n"
                f"   💰 {price_display}\n"
            )

        results_text += "\n\n📱 *Reply with a number (1-5) to select a flight*"

        await self.client.send_text(phone, results_text)

    async def _handle_selection(self, phone: str, text: str, session: Any) -> None:
        """Handle flight selection."""
        if session.state != ConversationState.VIEWING_RESULTS:
            await self.client.send_text(phone, "Please search for flights first.")
            return

        try:
            selection = int(text.strip()) - 1
            if 0 <= selection < len(session.offers or []):
                selected_offer = session.offers[selection]
                session.selected_offer_id = selected_offer["offer_id"]
                await self.session_mgr.update_state(phone, ConversationState.SELECTED_FLIGHT)

                # Request passenger details
                await self.client.send_text(
                    phone,
                    "✅ Flight selected!\n\n"
                    "👤 *Passenger Information Needed:*\n\n"
                    "Please provide:\n"
                    "• Full name (as on passport)\n"
                    "• Email address\n"
                    "• Phone number\n"
                    "• Date of birth (YYYY-MM-DD)\n\n"
                    "_Example:_\n"
                    "_Name: John Doe_\n"
                    "_Email: john@example.com_\n"
                    "_Phone: +2348012345678_\n"
                    "_DOB: 1990-01-15_"
                )
            else:
                await self.client.send_text(phone, "Invalid selection. Please choose 1-5.")

        except ValueError:
            await self.client.send_text(phone, "Please reply with a number (1-5).")

    async def _handle_passenger(self, phone: str, text: str, session: Any) -> None:
        """Handle passenger data collection."""
        if session.state != ConversationState.SELECTED_FLIGHT:
            await self.client.send_text(phone, "Please select a flight first.")
            return

        # Parse passenger data
        passenger_data = self.parser.parse_passenger_data(text)

        if not passenger_data:
            await self.client.send_text(
                phone,
                "❓ I couldn't extract passenger details. Please include:\n"
                "• Full name\n"
                "• Email\n"
                "• Phone\n"
                "• Date of birth"
            )
            return

        # Store passenger data
        session.passengers = [passenger_data]
        await self.session_mgr.update_state(phone, ConversationState.REVIEWING_BOOKING)

        # Show booking summary
        offer = next((o for o in session.offers if o["offer_id"] == session.selected_offer_id), None)
        if not offer:
            await self.client.send_text(phone, "Error: Offer not found. Please start over.")
            return

        price_ngn = offer.get("price_ngn") or offer.get("price", 0)
        params = session.search_params

        summary = (
            "📋 *Booking Summary*\n\n"
            f"✈️ Route: {params['from_']} → {params['to']}\n"
            f"📅 Date: {params['date']}\n"
            f"👤 Passenger: {passenger_data.get('first', '')} {passenger_data.get('last', '')}\n"
            f"💰 Price: ₦{price_ngn:,.0f}\n\n"
            "*Reply 'confirm' to proceed with booking*\n"
            "or 'cancel' to abort"
        )

        await self.client.send_text(phone, summary)

    async def _handle_confirmation(self, phone: str, session: Any) -> None:
        """Handle booking confirmation."""
        if session.state != ConversationState.REVIEWING_BOOKING:
            await self.client.send_text(phone, "Nothing to confirm. Start a new search?")
            return

        await self.client.send_text(phone, "⏳ Processing your booking...")

        try:
            # Prepare booking request
            passenger = session.passengers[0]
            book_req = BookRequest(
                offer_id=session.selected_offer_id,
                passengers=[
                    PassengerRequest(
                        type="adult",
                        title="Mr" if "mr" in passenger.get("first", "").lower() else "Ms",
                        first=passenger.get("first", "Unknown"),
                        last=passenger.get("last", "Unknown"),
                        dob=passenger.get("dob", "1990-01-01"),
                        passport=PassportRequest(
                            number_token="TEMP12345",  # Would need to collect
                            expiry="2030-01-01",
                            nationality="NG"
                        )
                    )
                ],
                contacts=ContactsRequest(
                    email=passenger.get("email", f"{phone}@sureflights.ng"),
                    phone=passenger.get("phone", phone)
                ),
                channel="whatsapp"
            )

            # Book flight
            booking_result = await book_flight(book_req)

            session.booking_reference = booking_result.get("pnr", "N/A")
            session.payment_link = booking_result.get("payment_link")
            await self.session_mgr.update_state(phone, ConversationState.AWAITING_PAYMENT)

            # Send confirmation with payment link
            confirmation = (
                "✅ *Booking Confirmed!*\n\n"
                f"📋 Reference: {session.booking_reference}\n\n"
            )

            if session.payment_link:
                confirmation += (
                    f"💳 *Complete Payment:*\n{session.payment_link}\n\n"
                    "Your e-ticket will be sent after payment."
                )

            await self.client.send_text(phone, confirmation)

        except Exception as e:
            logger.error("booking_error", phone=phone, error=str(e))
            await self.client.send_text(
                phone,
                "⚠️ Booking failed. Please try again or contact support."
            )
            await self.session_mgr.update_state(phone, ConversationState.ERROR)

    async def _handle_unknown(self, phone: str, session: Any) -> None:
        """Handle unknown intent."""
        if session.state == ConversationState.INITIAL:
            help_text = (
                "I didn't understand that. 🤔\n\n"
                "Try: \"Flight from Lagos to Abuja on Nov 15\"\n"
                "or type *help* for more info."
            )
        else:
            help_text = (
                "I didn't understand that. 🤔\n\n"
                "Type *help* for assistance or *cancel* to start over."
            )

        await self.client.send_text(phone, help_text)


# Global handler instance
_handler: Optional[ConversationHandler] = None


def get_conversation_handler() -> ConversationHandler:
    """Get or create conversation handler singleton."""
    global _handler
    if _handler is None:
        _handler = ConversationHandler()
    return _handler
