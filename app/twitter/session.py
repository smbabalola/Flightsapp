"""Twitter conversation session management."""
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger(__name__)


class ConversationState(str, Enum):
    """Twitter conversation states."""
    INITIAL = "initial"
    VIEWING_RESULTS = "viewing_results"
    SELECTED_FLIGHT = "selected_flight"
    REVIEWING_BOOKING = "reviewing_booking"
    AWAITING_PAYMENT = "awaiting_payment"
    ERROR = "error"


@dataclass
class TwitterSession:
    """Twitter conversation session data."""
    user_id: str
    state: ConversationState = ConversationState.INITIAL
    search_params: Optional[Dict[str, Any]] = None
    offers: Optional[List[Dict[str, Any]]] = None
    selected_offer_id: Optional[str] = None
    passengers: Optional[List[Dict[str, Any]]] = None
    booking_reference: Optional[str] = None
    payment_link: Optional[str] = None


class TwitterSessionManager:
    """Manages Twitter conversation sessions in memory."""

    def __init__(self):
        self._sessions: Dict[str, TwitterSession] = {}

    async def get_session(self, user_id: str) -> TwitterSession:
        """Get or create session for user.

        Args:
            user_id: Twitter user ID

        Returns:
            TwitterSession instance
        """
        if user_id not in self._sessions:
            self._sessions[user_id] = TwitterSession(user_id=user_id)
            logger.info("session_created", user_id=user_id)
        return self._sessions[user_id]

    async def update_state(self, user_id: str, state: ConversationState) -> None:
        """Update session state.

        Args:
            user_id: Twitter user ID
            state: New conversation state
        """
        session = await self.get_session(user_id)
        session.state = state
        logger.info("state_updated", user_id=user_id, state=state.value)

    async def save_session(self, session: TwitterSession) -> None:
        """Save session data.

        Args:
            session: Session to save
        """
        self._sessions[session.user_id] = session
        logger.debug("session_saved", user_id=session.user_id)

    async def clear_session(self, user_id: str) -> None:
        """Clear user session.

        Args:
            user_id: Twitter user ID
        """
        if user_id in self._sessions:
            del self._sessions[user_id]
            logger.info("session_cleared", user_id=user_id)


# Global session manager
_session_manager: Optional[TwitterSessionManager] = None


def get_session_manager() -> TwitterSessionManager:
    """Get or create session manager singleton."""
    global _session_manager
    if _session_manager is None:
        _session_manager = TwitterSessionManager()
    return _session_manager
