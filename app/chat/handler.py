"""Web chat message handler."""
from typing import Dict, Any, Optional
import structlog
from app.chat.session import get_chat_session_manager, ChatState
from app.chat.ai_assistant import get_chat_ai_assistant
from app.api.search import search_flights, SearchRequest, SliceRequest
from app.api.book import book_flight, BookRequest, PassengerRequest, ContactsRequest, PassportRequest
import re

logger = structlog.get_logger(__name__)


class ChatMessageHandler:
    """Handles web chat messages and responses."""

    def __init__(self):
        self.session_mgr = get_chat_session_manager()
        self.ai = get_chat_ai_assistant()

    async def handle_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Process incoming chat message and return response.

        Args:
            session_id: Unique session identifier
            message: User's message

        Returns:
            Dict with response message and metadata
        """
        logger.info("chat_message_received", session_id=session_id, text=message[:100])

        session = await self.session_mgr.get_session(session_id)
        text_lower = message.lower().strip()

        # Handle commands
        if text_lower in ["start", "hi", "hello", "hey"]:
            return await self._handle_start(session_id, session)
        elif text_lower in ["help", "?"]:
            return await self._handle_help()
        elif text_lower == "cancel":
            return await self._handle_cancel(session_id, session)
        elif text_lower == "confirm" and session.state == ChatState.REVIEWING_BOOKING:
            return await self._handle_confirmation(session_id, session)
        else:
            return await self._handle_conversational(session_id, message, session)

    async def _handle_start(self, session_id: str, session: Any) -> Dict[str, Any]:
        """Handle start/greeting."""
        await self.session_mgr.update_state(session_id, ChatState.INITIAL)

        return {
            "message": "✈️ **Welcome to SureFlights!**\n\nI'll help you book flights across Nigeria.\n\n**To search for flights, tell me:**\n• Where you're flying from\n• Where you're going to\n• Your travel date\n\n*Example: \"Flight from Lagos to Abuja on 2025-11-15\"*\n\nType **help** anytime for assistance.",
            "type": "text"
        }

    async def _handle_help(self) -> Dict[str, Any]:
        """Handle help request."""
        return {
            "message": "🆘 **SureFlights Help**\n\n**How to search flights:**\n• \"Flight from Lagos to Abuja on Nov 15\"\n• \"LOS to ABV tomorrow\"\n\n**Commands:**\n• start - Start new booking\n• cancel - Cancel current booking\n• help - Show this help\n\n**Supported cities:**\nLagos (LOS), Abuja (ABV), Port Harcourt (PHC), Kano (KAN), Enugu (ENU)",
            "type": "text"
        }

    async def _handle_cancel(self, session_id: str, session: Any) -> Dict[str, Any]:
        """Handle cancellation."""
        await self.session_mgr.clear_session(session_id)
        return {
            "message": "❌ Booking cancelled. Type **start** to begin a new search.",
            "type": "text"
        }

    async def _handle_conversational(self, session_id: str, message: str, session: Any) -> Dict[str, Any]:
        """Handle conversational input based on state."""

        if session.state == ChatState.INITIAL:
            # Use AI to understand intent
            intent_data = await self.ai.understand_search_intent(message)
            intent = intent_data.get("intent")

            if intent == "search_flight":
                params = {
                    "from_": intent_data.get("from"),
                    "to": intent_data.get("to"),
                    "date": intent_data.get("date"),
                    "adults": intent_data.get("adults", 1)
                }
                return await self._handle_search(session_id, params, session)

            elif intent == "search_date_range":
                return await self._handle_date_range_search(session_id, intent_data, session)

            else:
                # Fallback to regex parsing
                params = self._parse_flight_search(message)
                if params:
                    return await self._handle_search(session_id, params, session)
                else:
                    return {
                        "message": "I'd love to help you find a flight! 🛫\n\nJust tell me:\n• Where you're flying from\n• Where you're going\n• When you want to travel\n\n*Example: \"I need a flight from Lagos to Abuja on November 15th\"*\n\nOr ask me to find the cheapest flights this week!",
                        "type": "text"
                    }

        elif session.state == ChatState.VIEWING_RESULTS:
            # Check if they're asking about the results
            message_lower = message.lower()

            if any(word in message_lower for word in ["cheap", "fast", "best", "recommend", "which", "compare", "show", "tell"]):
                # They're asking questions about the results
                analysis = await self.ai.analyze_flight_results(
                    session.offers,
                    message,
                    session.search_params
                )
                return {
                    "message": analysis + "\n\n*Type the number (1-5) when you're ready to book!*",
                    "type": "text"
                }

            # Try to parse selection
            try:
                selection = int(message.strip()) - 1
                if 0 <= selection < len(session.offers or []):
                    return await self._handle_selection(session_id, selection, session)
                else:
                    return {
                        "message": "Please choose a number between 1 and {}. Or ask me questions like 'which is cheapest?' 😊".format(len(session.offers)),
                        "type": "text"
                    }
            except ValueError:
                return {
                    "message": "You can:\n• Type a number (1-{}) to select a flight\n• Ask me 'which is cheapest?'\n• Ask 'which is fastest?'\n• Ask 'what do you recommend?'".format(len(session.offers or [])),
                    "type": "text"
                }

        elif session.state == ChatState.SELECTED_FLIGHT:
            # Try to parse passenger info
            passenger_data = self._parse_passenger_data(message)
            if passenger_data:
                return await self._handle_passenger(session_id, passenger_data, session)
            else:
                return {
                    "message": "I need your passenger details to complete the booking:\n\n• Full name\n• Email address\n• Phone number\n• Date of birth (YYYY-MM-DD)\n\n*Just send it all in one message!*\n\n*Example:*\n*Name: John Doe*\n*Email: john@example.com*\n*Phone: +2348012345678*\n*DOB: 1990-01-15*",
                    "type": "text"
                }

        return {"message": "I didn't quite get that. Type **help** if you need assistance! 😊", "type": "text"}

    def _parse_flight_search(self, text: str) -> Optional[Dict[str, Any]]:
        """Enhanced flight search parser with multiple date format support."""
        from datetime import datetime

        text_lower = text.lower()

        # Airport codes mapping
        airports = {
            "lagos": "LOS", "los": "LOS",
            "abuja": "ABV", "abv": "ABV",
            "port harcourt": "PHC", "phc": "PHC", "ph": "PHC",
            "kano": "KAN", "kan": "KAN",
            "enugu": "ENU", "enu": "ENU",
            "london": "LON", "lon": "LON"  # Added London for international
        }

        # Try to extract origin and destination
        origin = None
        destination = None

        for city, code in airports.items():
            if city in text_lower:
                if "from " + city in text_lower:
                    origin = code
                elif "to " + city in text_lower:
                    destination = code
                elif not origin:
                    origin = code
                elif not destination:
                    destination = code

        # Extract date - support multiple formats
        travel_date = None

        # Format 1: YYYY-MM-DD
        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
        if date_match:
            try:
                date_obj = datetime(int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3)))
                travel_date = date_obj.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # Format 2: DD-MM-YYYY or MM-DD-YYYY
        if not travel_date:
            dd_mm_yyyy = re.search(r'(\d{2})-(\d{2})-(\d{4})', text)
            if dd_mm_yyyy:
                # Try DD-MM-YYYY first
                try:
                    date_obj = datetime(int(dd_mm_yyyy.group(3)), int(dd_mm_yyyy.group(2)), int(dd_mm_yyyy.group(1)))
                    travel_date = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    # Try MM-DD-YYYY
                    try:
                        date_obj = datetime(int(dd_mm_yyyy.group(3)), int(dd_mm_yyyy.group(1)), int(dd_mm_yyyy.group(2)))
                        travel_date = date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        pass

        # Format 3: Natural language dates
        if not travel_date:
            month_names = {
                "january": 1, "jan": 1, "february": 2, "feb": 2,
                "march": 3, "mar": 3, "april": 4, "apr": 4,
                "may": 5, "june": 6, "jun": 6,
                "july": 7, "jul": 7, "august": 8, "aug": 8,
                "september": 9, "sep": 9, "sept": 9,
                "october": 10, "oct": 10, "november": 11, "nov": 11,
                "december": 12, "dec": 12
            }

            for month_name, month_num in month_names.items():
                pattern = rf'{month_name}\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:\s+(\d{{4}}))?'
                match = re.search(pattern, text_lower)
                if match:
                    day = int(match.group(1))
                    year = int(match.group(2)) if match.group(2) else datetime.now().year
                    try:
                        date_obj = datetime(year, month_num, day)
                        travel_date = date_obj.strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue

        if origin and destination and travel_date:
            return {
                "from_": origin,
                "to": destination,
                "date": travel_date,
                "adults": 1
            }

        return None

    def _parse_passenger_data(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse passenger information from message."""
        data = {}

        # Extract email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            data['email'] = email_match.group(0)

        # Extract phone
        phone_match = re.search(r'\+?\d{10,15}', text)
        if phone_match:
            data['phone'] = phone_match.group(0)

        # Extract DOB
        dob_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
        if dob_match:
            data['dob'] = dob_match.group(0)

        # Extract name (simple heuristic)
        name_match = re.search(r'name:?\s*([A-Za-z\s]+)', text, re.IGNORECASE)
        if name_match:
            full_name = name_match.group(1).strip().split()
            if len(full_name) >= 2:
                data['first'] = full_name[0]
                data['last'] = ' '.join(full_name[1:])

        if 'email' in data and 'first' in data:
            return data

        return None

    async def _handle_date_range_search(self, session_id: str, intent_data: Dict[str, Any], session: Any) -> Dict[str, Any]:
        """Handle date range search (find cheapest across multiple dates)."""
        from_city = intent_data.get("from")
        to_city = intent_data.get("to")
        start_date = intent_data.get("start_date")
        end_date = intent_data.get("end_date")

        try:
            from datetime import datetime, timedelta

            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            days_diff = (end - start).days

            if days_diff > 7:
                return {
                    "message": "I can search up to 7 days at a time. Let's search {} to {} first?".format(
                        start_date,
                        (start + timedelta(days=7)).strftime("%Y-%m-%d")
                    ),
                    "type": "text"
                }

            await self.client.send_json({
                "type": "bot",
                "message": f"🔍 Searching flights from {from_city} to {to_city} between {start_date} and {end_date}..."
            }) if hasattr(self, 'client') else None

            all_results = []
            date_results = {}

            # Search each date
            current_date = start
            while current_date <= end:
                date_str = current_date.strftime("%Y-%m-%d")

                search_req = SearchRequest(
                    slices=[SliceRequest(from_=from_city, to=to_city, date=date_str)],
                    adults=1
                )

                offers = await search_flights(search_req)
                if offers:
                    date_results[date_str] = offers[:3]  # Top 3 for each date
                    all_results.extend([(date_str, offer) for offer in offers[:3]])

                current_date += timedelta(days=1)

            if not all_results:
                return {
                    "message": "😔 No flights found in that date range. Try different dates?",
                    "type": "text"
                }

            # Find cheapest across all dates
            cheapest_date, cheapest_offer = min(
                all_results,
                key=lambda x: x[1].get("price_ngn", x[1].get("price", float('inf')))
            )

            cheapest_price = cheapest_offer.get("price_ngn") or cheapest_offer.get("price", 0)

            # Format response
            message = f"📊 **Price Comparison: {from_city} → {to_city}**\n\n"
            message += f"💰 **Cheapest: {cheapest_date}** at ₦{cheapest_price:,.0f}\n\n"
            message += "**Prices by date:**\n"

            for date_str in sorted(date_results.keys()):
                offers = date_results[date_str]
                min_price = min(o.get("price_ngn", o.get("price", 0)) for o in offers)
                message += f"• {date_str}: from ₦{min_price:,.0f}\n"

            message += f"\n*Would you like to see flights for {cheapest_date}? (yes/no)*"

            # Store the cheapest date for quick booking
            session.search_params = {
                "from_": from_city,
                "to": to_city,
                "date": cheapest_date,
                "adults": 1
            }
            session.offers = date_results.get(cheapest_date, [])
            await self.session_mgr.save_session(session)

            return {"message": message, "type": "text"}

        except Exception as e:
            logger.error("date_range_search_error", error=str(e))
            return {
                "message": "Had trouble searching that date range. Try a specific date like '2025-11-15'?",
                "type": "text"
            }

    async def _handle_search(self, session_id: str, params: Dict[str, Any], session: Any) -> Dict[str, Any]:
        """Handle flight search."""
        session.search_params = params
        await self.session_mgr.save_session(session)

        try:
            search_req = SearchRequest(
                slices=[SliceRequest(**params)],
                adults=params.get("adults", 1)
            )

            offers = await search_flights(search_req)

            if not offers:
                return {
                    "message": "😔 No flights found for your search. Try different dates?",
                    "type": "text"
                }

            session.offers = offers[:5]
            await self.session_mgr.update_state(session_id, ChatState.VIEWING_RESULTS)
            await self.session_mgr.save_session(session)

            # Format results
            route = f"{params['from_']} → {params['to']}"
            message = f"✈️ **Flights: {route}**\n📅 {params['date']}\n\n"

            for i, offer in enumerate(offers[:5], 1):
                price_ngn = offer.get("price_ngn") or offer.get("price", 0)
                slices = offer.get("slices", [{}])
                segments = slices[0].get("segments", [{}]) if slices else [{}]

                airline = segments[0].get("airline", "Unknown") if segments else "Unknown"
                departure = segments[0].get("departure_time", "")[:5] if segments and segments[0].get("departure_time") else "N/A"
                arrival = segments[0].get("arrival_time", "")[:5] if segments and segments[0].get("arrival_time") else "N/A"
                duration = slices[0].get("duration_minutes", 0) if slices else 0
                hours = duration // 60
                mins = duration % 60

                message += f"\n**{i}. {airline}**\n"
                message += f"   🕐 {departure} → {arrival} ({hours}h {mins}m)\n"
                message += f"   💰 ₦{price_ngn:,.0f}\n"

            message += "\n\n📱 **Reply with a number (1-5) to select a flight**"

            return {"message": message, "type": "text"}

        except Exception as e:
            logger.error("chat_search_error", session_id=session_id, error=str(e))
            return {
                "message": "⚠️ Search failed. Please try again later.",
                "type": "text"
            }

    async def _handle_selection(self, session_id: str, selection: int, session: Any) -> Dict[str, Any]:
        """Handle flight selection."""
        selected_offer = session.offers[selection]
        session.selected_offer_id = selected_offer["offer_id"]
        await self.session_mgr.update_state(session_id, ChatState.SELECTED_FLIGHT)
        await self.session_mgr.save_session(session)

        return {
            "message": "✅ Flight selected!\n\n👤 **Passenger Information Needed:**\n\nPlease provide:\n• Full name (as on passport)\n• Email address\n• Phone number\n• Date of birth (YYYY-MM-DD)\n\n*Example:*\n*Name: John Doe*\n*Email: john@example.com*\n*Phone: +2348012345678*\n*DOB: 1990-01-15*",
            "type": "text"
        }

    async def _handle_passenger(self, session_id: str, passenger_data: Dict[str, Any], session: Any) -> Dict[str, Any]:
        """Handle passenger data."""
        session.passengers = [passenger_data]
        session.user_email = passenger_data.get('email')
        await self.session_mgr.update_state(session_id, ChatState.REVIEWING_BOOKING)
        await self.session_mgr.save_session(session)

        offer = next((o for o in session.offers if o["offer_id"] == session.selected_offer_id), None)
        if not offer:
            return {"message": "Error: Offer not found. Please start over.", "type": "text"}

        price_ngn = offer.get("price_ngn") or offer.get("price", 0)
        params = session.search_params

        message = f"📋 **Booking Summary**\n\n"
        message += f"✈️ Route: {params['from_']} → {params['to']}\n"
        message += f"📅 Date: {params['date']}\n"
        message += f"👤 Passenger: {passenger_data.get('first', '')} {passenger_data.get('last', '')}\n"
        message += f"💰 Price: ₦{price_ngn:,.0f}\n\n"
        message += "**Reply 'confirm' to proceed with booking**\nor 'cancel' to abort"

        return {"message": message, "type": "text"}

    async def _handle_confirmation(self, session_id: str, session: Any) -> Dict[str, Any]:
        """Handle booking confirmation."""
        try:
            passenger = session.passengers[0]

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
                    email=passenger.get("email", f"{session_id}@sureflights.ng"),
                    phone=passenger.get("phone", "+2340000000000")
                ),
                channel="webchat"
            )

            booking_result = await book_flight(book_req)

            session.booking_reference = booking_result.get("pnr", "N/A")
            session.payment_link = booking_result.get("payment_link")
            await self.session_mgr.update_state(session_id, ChatState.AWAITING_PAYMENT)
            await self.session_mgr.save_session(session)

            message = f"✅ **Booking Confirmed!**\n\n"
            message += f"📋 Reference: {session.booking_reference}\n\n"

            if session.payment_link:
                message += f"💳 **Complete Payment:**\n{session.payment_link}\n\n"
                message += "Your e-ticket will be sent after payment."

            return {"message": message, "type": "text", "payment_link": session.payment_link}

        except Exception as e:
            logger.error("chat_booking_error", session_id=session_id, error=str(e))
            return {
                "message": "⚠️ Booking failed. Please try again or contact support.",
                "type": "text"
            }


# Global handler instance
_handler: Optional[ChatMessageHandler] = None


def get_chat_handler() -> ChatMessageHandler:
    """Get or create chat message handler singleton."""
    global _handler
    if _handler is None:
        _handler = ChatMessageHandler()
    return _handler
