"""Web chat session management."""
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


class ChatState(str, Enum):
    """Web chat conversation states."""
    INITIAL = "initial"
    VIEWING_RESULTS = "viewing_results"
    SELECTED_FLIGHT = "selected_flight"
    REVIEWING_BOOKING = "reviewing_booking"
    AWAITING_PAYMENT = "awaiting_payment"
    ERROR = "error"


@dataclass
class ChatSession:
    """Web chat session data."""
    session_id: str
    state: ChatState = ChatState.INITIAL
    search_params: Optional[Dict[str, Any]] = None
    offers: Optional[List[Dict[str, Any]]] = None
    selected_offer_id: Optional[str] = None
    passengers: Optional[List[Dict[str, Any]]] = None
    booking_reference: Optional[str] = None
    payment_link: Optional[str] = None
    user_email: Optional[str] = None


class ChatSessionManager:
    """Manages web chat sessions in memory."""

    def __init__(self):
        self._sessions: Dict[str, ChatSession] = {}

    async def get_session(self, session_id: str) -> ChatSession:
        """Get or create session.

        Args:
            session_id: Unique session identifier

        Returns:
            ChatSession instance
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatSession(session_id=session_id)
            logger.info("chat_session_created", session_id=session_id)
        return self._sessions[session_id]

    async def update_state(self, session_id: str, state: ChatState) -> None:
        """Update session state.

        Args:
            session_id: Session identifier
            state: New chat state
        """
        session = await self.get_session(session_id)
        session.state = state
        logger.info("chat_state_updated", session_id=session_id, state=state.value)

    async def save_session(self, session: ChatSession) -> None:
        """Save session data.

        Args:
            session: Session to save
        """
        self._sessions[session.session_id] = session
        logger.debug("chat_session_saved", session_id=session.session_id)

    async def clear_session(self, session_id: str) -> None:
        """Clear session.

        Args:
            session_id: Session identifier
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("chat_session_cleared", session_id=session_id)


# Global session manager
_session_manager: Optional[ChatSessionManager] = None


def get_chat_session_manager() -> ChatSessionManager:
    """Get or create chat session manager singleton."""
    global _session_manager
    if _session_manager is None:
        _session_manager = ChatSessionManager()
    return _session_manager
