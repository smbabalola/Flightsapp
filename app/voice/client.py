"""Twilio client for voice operations."""
import structlog
from typing import Optional
from twilio.rest import Client
from app.core.settings import get_settings

logger = structlog.get_logger(__name__)


class TwilioVoiceClient:
    """Twilio client for making and managing voice calls."""

    def __init__(self):
        settings = get_settings()
        self.client = Client(
            settings.twilio_account_sid,
            settings.twilio_auth_token
        )
        self.phone_number = settings.twilio_phone_number
        logger.info("twilio_client_initialized", phone=self.phone_number)

    async def make_call(self, to_number: str, callback_url: str) -> Optional[str]:
        """Initiate an outbound call.

        Args:
            to_number: Phone number to call
            callback_url: URL for TwiML instructions

        Returns:
            Call SID or None if failed
        """
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=callback_url,
                method='POST'
            )
            logger.info("call_initiated", to=to_number, call_sid=call.sid)
            return call.sid
        except Exception as e:
            logger.error("call_failed", to=to_number, error=str(e))
            return None

    async def send_sms(self, to_number: str, message: str) -> bool:
        """Send SMS notification.

        Args:
            to_number: Phone number to text
            message: SMS content

        Returns:
            True if sent successfully
        """
        try:
            message = self.client.messages.create(
                to=to_number,
                from_=self.phone_number,
                body=message
            )
            logger.info("sms_sent", to=to_number, message_sid=message.sid)
            return True
        except Exception as e:
            logger.error("sms_failed", to=to_number, error=str(e))
            return False


# Global client instance
_client: Optional[TwilioVoiceClient] = None


def get_twilio_client() -> TwilioVoiceClient:
    """Get or create Twilio client singleton."""
    global _client
    if _client is None:
        _client = TwilioVoiceClient()
    return _client
