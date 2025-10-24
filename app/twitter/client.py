"""Twitter API client for sending and receiving DMs."""
import structlog
import tweepy
from typing import Optional
from app.core.settings import get_settings

logger = structlog.get_logger(__name__)


class TwitterClient:
    """Twitter API v2 client for DM operations."""

    def __init__(self):
        settings = get_settings()

        # Initialize Twitter API v2 client
        self.client = tweepy.Client(
            bearer_token=settings.twitter_bearer_token,
            consumer_key=settings.twitter_api_key,
            consumer_secret=settings.twitter_api_secret,
            access_token=settings.twitter_access_token,
            access_token_secret=settings.twitter_access_token_secret,
            wait_on_rate_limit=True
        )

        # Get authenticated user info
        try:
            self.me = self.client.get_me()
            logger.info("twitter_client_initialized", user_id=self.me.data.id if self.me.data else None)
        except Exception as e:
            logger.error("twitter_init_error", error=str(e))
            self.me = None

    async def send_dm(self, user_id: str, text: str) -> bool:
        """Send a direct message to a Twitter user.

        Args:
            user_id: Twitter user ID
            text: Message text

        Returns:
            bool: True if message sent successfully
        """
        try:
            # Twitter API v2 DM creation
            response = self.client.create_direct_message(
                participant_id=user_id,
                text=text
            )
            logger.info("dm_sent", user_id=user_id, text_length=len(text))
            return True
        except Exception as e:
            logger.error("dm_send_error", user_id=user_id, error=str(e))
            return False

    async def get_user_id_from_username(self, username: str) -> Optional[str]:
        """Get user ID from username.

        Args:
            username: Twitter username (without @)

        Returns:
            User ID or None
        """
        try:
            user = self.client.get_user(username=username)
            if user.data:
                return user.data.id
            return None
        except Exception as e:
            logger.error("get_user_error", username=username, error=str(e))
            return None


# Global client instance
_client: Optional[TwitterClient] = None


def get_twitter_client() -> TwitterClient:
    """Get or create Twitter client singleton."""
    global _client
    if _client is None:
        _client = TwitterClient()
    return _client
