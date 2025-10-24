"""Voice call session management."""
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


class VoiceState(str, Enum):
    """Voice conversation states."""
    GREETING = "greeting"
    COLLECTING_ORIGIN = "collecting_origin"
    COLLECTING_DESTINATION = "collecting_destination"
    COLLECTING_DATE = "collecting_date"
    SEARCHING = "searching"
    PRESENTING_OPTIONS = "presenting_options"
    CONFIRMING_SELECTION = "confirming_selection"
    COLLECTING_PASSENGER = "collecting_passenger"
    REVIEWING_BOOKING = "reviewing_booking"
    PROCESSING_PAYMENT = "processing_payment"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class VoiceSession:
    """Voice call session data."""
    call_sid: str
    caller_number: str
    state: VoiceState = VoiceState.GREETING
    origin: Optional[str] = None
    destination: Optional[str] = None
    travel_date: Optional[str] = None
    offers: Optional[List[Dict[str, Any]]] = None
    selected_offer_id: Optional[str] = None
    passenger_name: Optional[str] = None
    passenger_email: Optional[str] = None
    booking_reference: Optional[str] = None
    payment_link: Optional[str] = None


class VoiceSessionManager:
    """Manages voice call sessions in memory."""

    def __init__(self):
        self._sessions: Dict[str, VoiceSession] = {}

    async def get_session(self, call_sid: str, caller_number: str = None) -> VoiceSession:
        """Get or create session for call.

        Args:
            call_sid: Twilio call SID
            caller_number: Caller's phone number

        Returns:
            VoiceSession instance
        """
        if call_sid not in self._sessions:
            self._sessions[call_sid] = VoiceSession(
                call_sid=call_sid,
                caller_number=caller_number or "unknown"
            )
            logger.info("voice_session_created", call_sid=call_sid)
        return self._sessions[call_sid]

    async def update_state(self, call_sid: str, state: VoiceState) -> None:
        """Update session state.

        Args:
            call_sid: Twilio call SID
            state: New voice state
        """
        if call_sid in self._sessions:
            self._sessions[call_sid].state = state
            logger.info("voice_state_updated", call_sid=call_sid, state=state.value)

    async def save_session(self, session: VoiceSession) -> None:
        """Save session data.

        Args:
            session: Session to save
        """
        self._sessions[session.call_sid] = session
        logger.debug("voice_session_saved", call_sid=session.call_sid)

    async def clear_session(self, call_sid: str) -> None:
        """Clear call session.

        Args:
            call_sid: Twilio call SID
        """
        if call_sid in self._sessions:
            del self._sessions[call_sid]
            logger.info("voice_session_cleared", call_sid=call_sid)


# Global session manager
_session_manager: Optional[VoiceSessionManager] = None


def get_voice_session_manager() -> VoiceSessionManager:
    """Get or create voice session manager singleton."""
    global _session_manager
    if _session_manager is None:
        _session_manager = VoiceSessionManager()
    return _session_manager
