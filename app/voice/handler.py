"""Voice call handler for flight booking conversations."""
from typing import Dict, Any, Optional
import structlog
from twilio.twiml.voice_response import VoiceResponse, Gather
from app.voice.session import get_voice_session_manager, VoiceState
from app.voice.ai_voice import get_voice_ai
from app.voice.client import get_twilio_client
from app.api.search import search_flights, SearchRequest, SliceRequest
from app.api.book import book_flight, BookRequest, PassengerRequest, ContactsRequest, PassportRequest

logger = structlog.get_logger(__name__)


class VoiceCallHandler:
    """Handles voice call flow for flight booking."""

    def __init__(self):
        self.session_mgr = get_voice_session_manager()
        self.ai = get_voice_ai()
        self.client = get_twilio_client()

    async def handle_incoming_call(self, call_sid: str, caller_number: str) -> str:
        """Handle incoming call - greeting.

        Args:
            call_sid: Twilio call SID
            caller_number: Caller's phone number

        Returns:
            TwiML response string
        """
        session = await self.session_mgr.get_session(call_sid, caller_number)
        await self.session_mgr.update_state(call_sid, VoiceState.COLLECTING_ORIGIN)

        response = VoiceResponse()
        gather = Gather(
            input='speech',
            action=f'/webhooks/voice/collect-origin',
            method='POST',
            speech_timeout='auto',
            language='en-US'
        )
        gather.say(
            "Welcome to Sure Flights! "
            "I'll help you book a flight within Nigeria. "
            "Which city are you flying from? "
            "You can say Lagos, Abuja, Port Harcourt, Kano, or Enugu.",
            voice='alice'
        )
        response.append(gather)

        logger.info("call_started", call_sid=call_sid, caller=caller_number)
        return str(response)

    async def handle_origin(self, call_sid: str, speech_result: str) -> str:
        """Handle origin city collection.

        Args:
            call_sid: Twilio call SID
            speech_result: Transcribed speech

        Returns:
            TwiML response string
        """
        session = await self.session_mgr.get_session(call_sid)
        origin = await self.ai.extract_city(speech_result)

        response = VoiceResponse()

        if origin:
            session.origin = origin
            await self.session_mgr.update_state(call_sid, VoiceState.COLLECTING_DESTINATION)
            await self.session_mgr.save_session(session)

            gather = Gather(
                input='speech',
                action=f'/webhooks/voice/collect-destination',
                method='POST',
                speech_timeout='auto',
                language='en-US'
            )
            gather.say(
                f"Great! Flying from {self._city_name(origin)}. "
                f"Where would you like to fly to?",
                voice='alice'
            )
            response.append(gather)
        else:
            # Retry
            gather = Gather(
                input='speech',
                action=f'/webhooks/voice/collect-origin',
                method='POST',
                speech_timeout='auto',
                language='en-US'
            )
            gather.say(
                "I didn't catch that. Please say the city you're flying from. "
                "Lagos, Abuja, Port Harcourt, Kano, or Enugu.",
                voice='alice'
            )
            response.append(gather)

        return str(response)

    async def handle_destination(self, call_sid: str, speech_result: str) -> str:
        """Handle destination city collection."""
        session = await self.session_mgr.get_session(call_sid)
        destination = await self.ai.extract_city(speech_result)

        response = VoiceResponse()

        if destination and destination != session.origin:
            session.destination = destination
            await self.session_mgr.update_state(call_sid, VoiceState.COLLECTING_DATE)
            await self.session_mgr.save_session(session)

            gather = Gather(
                input='speech',
                action=f'/webhooks/voice/collect-date',
                method='POST',
                speech_timeout='auto',
                language='en-US'
            )
            gather.say(
                f"Perfect! {self._city_name(session.origin)} to {self._city_name(destination)}. "
                f"When would you like to travel? You can say tomorrow, or a specific date.",
                voice='alice'
            )
            response.append(gather)
        else:
            # Retry
            gather = Gather(
                input='speech',
                action=f'/webhooks/voice/collect-destination',
                method='POST',
                speech_timeout='auto',
                language='en-US'
            )
            gather.say(
                "Please say your destination city. Lagos, Abuja, Port Harcourt, Kano, or Enugu.",
                voice='alice'
            )
            response.append(gather)

        return str(response)

    async def handle_date(self, call_sid: str, speech_result: str) -> str:
        """Handle travel date collection and search flights."""
        session = await self.session_mgr.get_session(call_sid)
        travel_date = await self.ai.extract_date(speech_result)

        response = VoiceResponse()

        if travel_date:
            session.travel_date = travel_date
            await self.session_mgr.update_state(call_sid, VoiceState.SEARCHING)
            await self.session_mgr.save_session(session)

            # Search flights
            try:
                search_req = SearchRequest(
                    slices=[SliceRequest(
                        from_=session.origin,
                        to=session.destination,
                        date=travel_date
                    )],
                    adults=1
                )

                offers = await search_flights(search_req)

                if offers:
                    session.offers = offers[:5]  # Top 5
                    await self.session_mgr.update_state(call_sid, VoiceState.PRESENTING_OPTIONS)
                    await self.session_mgr.save_session(session)

                    # Present options
                    response.say("I found some flights for you. Here are the top options:", voice='alice')

                    for i, offer in enumerate(offers[:5], 1):
                        price_ngn = offer.get("price_ngn", 0)
                        slices = offer.get("slices", [{}])
                        segments = slices[0].get("segments", [{}]) if slices else [{}]
                        airline = segments[0].get("airline", "Unknown") if segments else "Unknown"

                        response.say(
                            f"Option {i}: {airline} for {price_ngn:.0f} naira.",
                            voice='alice'
                        )

                    gather = Gather(
                        input='speech',
                        action=f'/webhooks/voice/select-flight',
                        method='POST',
                        speech_timeout='auto',
                        language='en-US'
                    )
                    gather.say("Which option would you like? Say the number, 1 through 5.", voice='alice')
                    response.append(gather)
                else:
                    response.say(
                        "I'm sorry, no flights were found for those dates. "
                        "Please call back to search again. Goodbye!",
                        voice='alice'
                    )
                    response.hangup()

            except Exception as e:
                logger.error("flight_search_error", call_sid=call_sid, error=str(e))
                response.say("I encountered an error searching for flights. Please try again later. Goodbye!", voice='alice')
                response.hangup()
        else:
            # Retry
            gather = Gather(
                input='speech',
                action=f'/webhooks/voice/collect-date',
                method='POST',
                speech_timeout='auto',
                language='en-US'
            )
            gather.say(
                "I didn't understand the date. Please say when you'd like to travel, like tomorrow or November 15th.",
                voice='alice'
            )
            response.append(gather)

        return str(response)

    async def handle_flight_selection(self, call_sid: str, speech_result: str) -> str:
        """Handle flight selection."""
        session = await self.session_mgr.get_session(call_sid)
        selection = await self.ai.extract_selection(speech_result)

        response = VoiceResponse()

        if selection and 1 <= selection <= len(session.offers or []):
            selected_offer = session.offers[selection - 1]
            session.selected_offer_id = selected_offer["offer_id"]
            await self.session_mgr.update_state(call_sid, VoiceState.COLLECTING_PASSENGER)
            await self.session_mgr.save_session(session)

            gather = Gather(
                input='speech',
                action=f'/webhooks/voice/collect-passenger',
                method='POST',
                speech_timeout='auto',
                language='en-US'
            )
            gather.say(
                "Great choice! Now I need the passenger's full name. "
                "Please say the first name and last name.",
                voice='alice'
            )
            response.append(gather)
        else:
            # Retry
            gather = Gather(
                input='speech',
                action=f'/webhooks/voice/select-flight',
                method='POST',
                speech_timeout='auto',
                language='en-US'
            )
            gather.say("Please say a number from 1 to 5 to select your flight.", voice='alice')
            response.append(gather)

        return str(response)

    async def handle_passenger_name(self, call_sid: str, speech_result: str) -> str:
        """Handle passenger name collection and complete booking."""
        session = await self.session_mgr.get_session(call_sid)
        name = await self.ai.extract_passenger_name(speech_result)

        response = VoiceResponse()

        if name:
            session.passenger_name = f"{name['first']} {name['last']}"
            await self.session_mgr.update_state(call_sid, VoiceState.REVIEWING_BOOKING)
            await self.session_mgr.save_session(session)

            # Create booking
            try:
                book_req = BookRequest(
                    offer_id=session.selected_offer_id,
                    passengers=[
                        PassengerRequest(
                            type="adult",
                            title="Mr",
                            first=name['first'],
                            last=name['last'],
                            dob="1990-01-01",  # Would need to collect
                            passport=PassportRequest(
                                number_token="TEMP12345",
                                expiry="2030-01-01",
                                nationality="NG"
                            )
                        )
                    ],
                    contacts=ContactsRequest(
                        email=f"{session.caller_number.replace('+', '')}@sureflights.ng",
                        phone=session.caller_number
                    ),
                    channel="voice"
                )

                booking_result = await book_flight(book_req)

                session.booking_reference = booking_result.get("pnr", "N/A")
                session.payment_link = booking_result.get("payment_link")
                await self.session_mgr.update_state(call_sid, VoiceState.COMPLETED)
                await self.session_mgr.save_session(session)

                # Send SMS with booking details
                sms_message = (
                    f"SureFlights Booking Confirmed!\n"
                    f"Ref: {session.booking_reference}\n"
                    f"Route: {session.origin} to {session.destination}\n"
                    f"Date: {session.travel_date}\n"
                )
                if session.payment_link:
                    sms_message += f"Pay: {session.payment_link}"

                await self.client.send_sms(session.caller_number, sms_message)

                response.say(
                    f"Your booking is confirmed! Reference number {session.booking_reference}. "
                    f"I've sent the payment link and details to your phone via text message. "
                    f"Thank you for choosing Sure Flights. Goodbye!",
                    voice='alice'
                )
                response.hangup()

            except Exception as e:
                logger.error("booking_error", call_sid=call_sid, error=str(e))
                response.say("I encountered an error creating your booking. Please call back to try again. Goodbye!", voice='alice')
                response.hangup()
        else:
            # Retry
            gather = Gather(
                input='speech',
                action=f'/webhooks/voice/collect-passenger',
                method='POST',
                speech_timeout='auto',
                language='en-US'
            )
            gather.say("Please say the passenger's full name clearly.", voice='alice')
            response.append(gather)

        return str(response)

    def _city_name(self, code: str) -> str:
        """Convert airport code to city name."""
        city_map = {
            "LOS": "Lagos",
            "ABV": "Abuja",
            "PHC": "Port Harcourt",
            "KAN": "Kano",
            "ENU": "Enugu"
        }
        return city_map.get(code, code)


# Global handler instance
_handler: Optional[VoiceCallHandler] = None


def get_voice_handler() -> VoiceCallHandler:
    """Get or create voice call handler singleton."""
    global _handler
    if _handler is None:
        _handler = VoiceCallHandler()
    return _handler
