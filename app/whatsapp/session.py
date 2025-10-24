"""
Session and state management for WhatsApp conversations.

Tracks user conversation state, collected data, and flow progress.
Uses Redis for distributed session storage with TTL.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
import json
import structlog
from app.core.config import get_settings
from app.integrations.redis_client import get_redis_client

logger = structlog.get_logger(__name__)


class ConversationState(str, Enum):
    """Possible states in the booking conversation flow."""
    INITIAL = "initial"
    SEARCHING = "searching"
    VIEWING_RESULTS = "viewing_results"
    SELECTED_FLIGHT = "selected_flight"
    COLLECTING_PASSENGERS = "collecting_passengers"
    REVIEWING_BOOKING = "reviewing_booking"
    AWAITING_PAYMENT = "awaiting_payment"
    BOOKING_CONFIRMED = "booking_confirmed"
    ERROR = "error"


class SessionData:
    """User session data model."""

    def __init__(
        self,
        phone: str,
        state: ConversationState = ConversationState.INITIAL,
        data: Optional[Dict[str, Any]] = None
    ):
        self.phone = phone
        self.state = state
        self.data = data or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @property
    def search_params(self) -> Optional[Dict[str, Any]]:
        """Get search parameters from session data."""
        return self.data.get("search_params")

    @search_params.setter
    def search_params(self, value: Dict[str, Any]):
        """Set search parameters."""
        self.data["search_params"] = value

    @property
    def offers(self) -> Optional[List[Dict[str, Any]]]:
        """Get flight offers from session data."""
        return self.data.get("offers")

    @offers.setter
    def offers(self, value: List[Dict[str, Any]]):
        """Set flight offers."""
        self.data["offers"] = value

    @property
    def selected_offer_id(self) -> Optional[str]:
        """Get selected offer ID."""
        return self.data.get("selected_offer_id")

    @selected_offer_id.setter
    def selected_offer_id(self, value: str):
        """Set selected offer ID."""
        self.data["selected_offer_id"] = value

    @property
    def passengers(self) -> List[Dict[str, Any]]:
        """Get passenger data."""
        return self.data.get("passengers", [])

    @passengers.setter
    def passengers(self, value: List[Dict[str, Any]]):
        """Set passenger data."""
        self.data["passengers"] = value

    @property
    def booking_reference(self) -> Optional[str]:
        """Get booking reference (PNR)."""
        return self.data.get("booking_reference")

    @booking_reference.setter
    def booking_reference(self, value: str):
        """Set booking reference."""
        self.data["booking_reference"] = value

    @property
    def payment_link(self) -> Optional[str]:
        """Get payment link."""
        return self.data.get("payment_link")

    @payment_link.setter
    def payment_link(self, value: str):
        """Set payment link."""
        self.data["payment_link"] = value

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session to dict for Redis storage."""
        return {
            "phone": self.phone,
            "state": self.state.value,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """Deserialize session from Redis dict."""
        session = cls(
            phone=data["phone"],
            state=ConversationState(data["state"]),
            data=data.get("data", {})
        )
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.updated_at = datetime.fromisoformat(data["updated_at"])
        return session


class SessionManager:
    """Manages WhatsApp conversation sessions in Redis."""

    def __init__(self, ttl_hours: int = 24):
        """Initialize session manager.

        Args:
            ttl_hours: Session TTL in hours (default: 24)
        """
        self.settings = get_settings()
        self.redis = get_redis_client() if self.settings.use_redis_idempotency else None
        self.ttl_seconds = ttl_hours * 3600
        self._in_memory_sessions: Dict[str, SessionData] = {}  # Fallback if Redis disabled

    def _get_key(self, phone: str) -> str:
        """Generate Redis key for phone number."""
        return f"whatsapp:session:{phone}"

    async def get_session(self, phone: str) -> SessionData:
        """Get or create session for phone number.

        Args:
            phone: User's phone number

        Returns:
            SessionData for this user
        """
        if not self.redis:
            # Fallback to in-memory if Redis disabled
            if phone not in self._in_memory_sessions:
                self._in_memory_sessions[phone] = SessionData(phone=phone)
            return self._in_memory_sessions[phone]

        key = self._get_key(phone)
        data = self.redis.get(key)

        if data:
            try:
                session = SessionData.from_dict(json.loads(data))
                logger.info("session_retrieved", phone=phone, state=session.state.value)
                return session
            except Exception as e:
                logger.error("session_deserialize_error", phone=phone, error=str(e))

        # Create new session
        session = SessionData(phone=phone)
        await self.save_session(session)
        logger.info("session_created", phone=phone)
        return session

    async def save_session(self, session: SessionData) -> None:
        """Save session to Redis with TTL.

        Args:
            session: SessionData to save
        """
        session.updated_at = datetime.utcnow()

        if not self.redis:
            # Fallback to in-memory
            self._in_memory_sessions[session.phone] = session
            return

        key = self._get_key(session.phone)
        data = json.dumps(session.to_dict())

        self.redis.setex(
            name=key,
            time=self.ttl_seconds,
            value=data
        )

        logger.info(
            "session_saved",
            phone=session.phone,
            state=session.state.value
        )

    async def update_state(self, phone: str, state: ConversationState) -> None:
        """Update session state.

        Args:
            phone: User's phone number
            state: New conversation state
        """
        session = await self.get_session(phone)
        session.state = state
        await self.save_session(session)

        logger.info("session_state_changed", phone=phone, new_state=state.value)

    async def clear_session(self, phone: str) -> None:
        """Clear session for phone number.

        Args:
            phone: User's phone number
        """
        if not self.redis:
            self._in_memory_sessions.pop(phone, None)
            logger.info("session_cleared", phone=phone)
            return

        key = self._get_key(phone)
        self.redis.delete(key)
        logger.info("session_cleared", phone=phone)

    async def extend_ttl(self, phone: str) -> None:
        """Extend session TTL (reset expiry).

        Args:
            phone: User's phone number
        """
        if not self.redis:
            return

        key = self._get_key(phone)
        self.redis.expire(key, self.ttl_seconds)


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create session manager singleton."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
