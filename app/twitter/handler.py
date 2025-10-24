"""Main conversational flow handler for Twitter DM booking."""
from typing import Dict, Any, Optional
import structlog
from app.twitter.client import get_twitter_client
from app.twitter.session import get_session_manager, ConversationState
from app.twitter.ai_assistant import get_ai_assistant
from app.api.search import search_flights, SearchRequest, SliceRequest
from app.api.book import book_flight, BookRequest, PassengerRequest, ContactsRequest, PassportRequest
from app.utils.fx import ngn_equivalent

logger = structlog.get_logger(__name__)


class TwitterConversationHandler:
    """Handles Twitter DM conversation flow and state transitions."""

    def __init__(self):
        self.client = get_twitter_client()
        self.session_mgr = get_session_manager()
        self.ai = get_ai_assistant()

    async def handle_dm(self, sender_id: str, message_text: str) -> None:
        """Process incoming Twitter DM and respond.

        Args:
            sender_id: Twitter user ID
            message_text: Message content
        """
        logger.info("dm_received", sender_id=sender_id, text=message_text[:100])

        # Get session
        session = await self.session_mgr.get_session(sender_id)

        # Parse message text for commands
        text_lower = message_text.lower().strip()

        # Handle commands
        if text_lower in ["start", "hi", "hello", "hey"]:
            await self._handle_start(sender_id, session)
        elif text_lower in ["help", "?"]:
            await self._handle_help(sender_id)
        elif text_lower == "cancel":
            await self._handle_cancel(sender_id, session)
        elif text_lower == "status":
            await self._handle_status(sender_id, session)
        elif text_lower == "confirm" and session.state == ConversationState.REVIEWING_BOOKING:
            await self._handle_confirmation(sender_id, session)
        else:
            # Use AI to determine intent based on state
            await self._handle_conversational(sender_id, message_text, session)

    async def _handle_start(self, sender_id: str, session: Any) -> None:
        """Handle start/greeting."""
        welcome = (
            "✈️ Welcome to SureFlights!\n\n"
            "I'll help you book flights across Nigeria.\n\n"
            "Just tell me where you're flying from, where to, and when!\n\n"
            "Example: 'Flight from Lagos to Abuja on Nov 15'"
        )
        await self.client.send_dm(sender_id, welcome)
        await self.session_mgr.update_state(sender_id, ConversationState.INITIAL)

    async def _handle_help(self, sender_id: str) -> None:
        """Handle help request."""
        help_text = (
            "🆘 SureFlights Help\n\n"
            "Commands:\n"
            "• start - New booking\n"
            "• status - Check booking\n"
            "• cancel - Cancel booking\n"
            "• help - This message\n\n"
            "Cities: Lagos, Abuja, Port Harcourt, Kano, Enugu"
        )
        await self.client.send_dm(sender_id, help_text)

    async def _handle_cancel(self, sender_id: str, session: Any) -> None:
        """Handle cancellation."""
        await self.session_mgr.clear_session(sender_id)
        await self.client.send_dm(sender_id, "❌ Booking cancelled. Send 'start' for new search.")

    async def _handle_status(self, sender_id: str, session: Any) -> None:
        """Handle status check."""
        if session.booking_reference:
            status_text = f"📋 Booking: {session.booking_reference}"
            if session.payment_link:
                status_text += f"\n💳 Pay: {session.payment_link}"
            await self.client.send_dm(sender_id, status_text)
        else:
            await self.client.send_dm(sender_id, "No active booking. Send 'start' to begin.")

    async def _handle_conversational(self, sender_id: str, message: str, session: Any) -> None:
        """Handle conversational input based on current state."""

        if session.state == ConversationState.INITIAL:
            # Try to parse flight search
            params = await self.ai.parse_flight_search(message)
            if params:
                await self._handle_search(sender_id, params, session)
            else:
                response = await self.ai.generate_response(
                    message,
                    "User is trying to search for flights. Ask them to provide origin, destination, and date."
                )
                await self.client.send_dm(sender_id, response)

        elif session.state == ConversationState.VIEWING_RESULTS:
            # Try to parse selection (number)
            try:
                selection = int(message.strip()) - 1
                if 0 <= selection < len(session.offers or []):
                    await self._handle_selection(sender_id, selection, session)
                else:
                    await self.client.send_dm(sender_id, "Invalid choice. Pick 1-5.")
            except ValueError:
                await self.client.send_dm(sender_id, "Reply with a number (1-5).")

        elif session.state == ConversationState.SELECTED_FLIGHT:
            # Try to parse passenger info
            passenger_data = await self.ai.parse_passenger_info(message)
            if passenger_data:
                await self._handle_passenger(sender_id, passenger_data, session)
            else:
                await self.client.send_dm(
                    sender_id,
                    "Please provide:\n• Full name\n• Email\n• Phone\n• Date of birth (YYYY-MM-DD)"
                )

        else:
            response = await self.ai.generate_response(message)
            await self.client.send_dm(sender_id, response)

    async def _handle_search(self, sender_id: str, params: Dict[str, Any], session: Any) -> None:
        """Handle flight search."""
        session.search_params = params
        await self.session_mgr.save_session(session)

        await self.client.send_dm(sender_id, "🔍 Searching flights...")

        try:
            # Create search request
            search_req = SearchRequest(
                slices=[SliceRequest(**params)],
                adults=params.get("adults", 1)
            )

            # Search flights
            offers = await search_flights(search_req)

            if not offers:
                await self.client.send_dm(sender_id, "😔 No flights found. Try different dates?")
                return

            # Store offers
            session.offers = offers
            await self.session_mgr.update_state(sender_id, ConversationState.VIEWING_RESULTS)

            # Send results
            await self._send_flight_results(sender_id, offers, params)

        except Exception as e:
            logger.error("search_error", sender_id=sender_id, error=str(e))
            await self.client.send_dm(sender_id, "⚠️ Search failed. Try again later.")

    async def _send_flight_results(self, sender_id: str, offers: list, params: Dict[str, Any]) -> None:
        """Format and send flight results."""
        route = f"{params['from_']} → {params['to']}"

        # Send header
        header = f"✈️ {route} | {params['date']}\n"
        await self.client.send_dm(sender_id, header)

        # Show top 5 offers
        for i, offer in enumerate(offers[:5], 1):
            price_ngn = offer.get("price_ngn") or offer.get("price", 0)

            slices = offer.get("slices", [{}])
            first_slice = slices[0] if slices else {}
            segments = first_slice.get("segments", [{}])
            first_seg = segments[0] if segments else {}

            airline = first_seg.get("airline", "Unknown")
            departure = first_seg.get("departure_time", "")[:5] if first_seg.get("departure_time") else "N/A"
            arrival = first_seg.get("arrival_time", "")[:5] if first_seg.get("arrival_time") else "N/A"
            duration = first_slice.get("duration_minutes", 0)
            hours = duration // 60
            mins = duration % 60

            flight_text = (
                f"{i}. {airline}\n"
                f"🕐 {departure}→{arrival} ({hours}h{mins}m)\n"
                f"💰 ₦{price_ngn:,.0f}"
            )
            await self.client.send_dm(sender_id, flight_text)

        # Ask for selection
        await self.client.send_dm(sender_id, "Reply 1-5 to select")

    async def _handle_selection(self, sender_id: str, selection: int, session: Any) -> None:
        """Handle flight selection."""
        selected_offer = session.offers[selection]
        session.selected_offer_id = selected_offer["offer_id"]
        await self.session_mgr.update_state(sender_id, ConversationState.SELECTED_FLIGHT)

        await self.client.send_dm(
            sender_id,
            "✅ Flight selected!\n\n"
            "👤 Passenger Info:\n"
            "• Full name\n"
            "• Email\n"
            "• Phone\n"
            "• DOB (YYYY-MM-DD)\n\n"
            "Example:\nJohn Doe\njohn@email.com\n+2348012345678\n1990-01-15"
        )

    async def _handle_passenger(self, sender_id: str, passenger_data: Dict[str, Any], session: Any) -> None:
        """Handle passenger data."""
        session.passengers = [passenger_data]
        await self.session_mgr.update_state(sender_id, ConversationState.REVIEWING_BOOKING)

        offer = next((o for o in session.offers if o["offer_id"] == session.selected_offer_id), None)
        if not offer:
            await self.client.send_dm(sender_id, "Error: Offer not found.")
            return

        price_ngn = offer.get("price_ngn") or offer.get("price", 0)
        params = session.search_params

        summary = (
            f"📋 Booking Summary\n\n"
            f"✈️ {params['from_']} → {params['to']}\n"
            f"📅 {params['date']}\n"
            f"👤 {passenger_data.get('first', '')} {passenger_data.get('last', '')}\n"
            f"💰 ₦{price_ngn:,.0f}\n\n"
            "Reply 'confirm' to book"
        )

        await self.client.send_dm(sender_id, summary)

    async def _handle_confirmation(self, sender_id: str, session: Any) -> None:
        """Handle booking confirmation."""
        await self.client.send_dm(sender_id, "⏳ Processing booking...")

        try:
            passenger = session.passengers[0]

            # Create booking
            book_req = BookRequest(
                offer_id=session.selected_offer_id,
                passengers=[
                    PassengerRequest(
                        type="adult",
                        title="Mr",
                        first=passenger.get("first", "Unknown"),
                        last=passenger.get("last", "Unknown"),
                        dob=passenger.get("dob", "1990-01-01"),
                        passport=PassportRequest(
                            number_token="TEMP12345",
                            expiry="2030-01-01",
                            nationality="NG"
                        )
                    )
                ],
                contacts=ContactsRequest(
                    email=passenger.get("email", f"{sender_id}@sureflights.ng"),
                    phone=passenger.get("phone", "+2340000000000")
                ),
                channel="twitter"
            )

            booking_result = await create_booking(book_req)

            session.booking_reference = booking_result.get("pnr", "N/A")
            session.payment_link = booking_result.get("payment_link")
            await self.session_mgr.update_state(sender_id, ConversationState.AWAITING_PAYMENT)

            confirmation = f"✅ Booking Confirmed!\n\n📋 Ref: {session.booking_reference}"

            if session.payment_link:
                confirmation += f"\n\n💳 Pay: {session.payment_link}"

            await self.client.send_dm(sender_id, confirmation)

        except Exception as e:
            logger.error("booking_error", sender_id=sender_id, error=str(e))
            await self.client.send_dm(sender_id, "⚠️ Booking failed. Try again.")
            await self.session_mgr.update_state(sender_id, ConversationState.ERROR)


# Global handler instance
_handler: Optional[TwitterConversationHandler] = None


def get_twitter_handler() -> TwitterConversationHandler:
    """Get or create Twitter conversation handler singleton."""
    global _handler
    if _handler is None:
        _handler = TwitterConversationHandler()
    return _handler
