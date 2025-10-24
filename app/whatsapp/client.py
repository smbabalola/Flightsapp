"""
WhatsApp Cloud API client for sending messages.

Handles authentication and message sending via WhatsApp Business Cloud API.
"""
import httpx
from typing import Dict, Any, List, Optional
import structlog
from app.core.settings import get_settings

logger = structlog.get_logger(__name__)


class WhatsAppClient:
    """Client for WhatsApp Business Cloud API."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = f"https://graph.facebook.com/v18.0/{self.settings.whatsapp_phone_number_id}"
        self.headers = {
            "Authorization": f"Bearer {self.settings.whatsapp_access_token}",
            "Content-Type": "application/json"
        }

    async def send_text(self, to: str, text: str) -> Dict[str, Any]:
        """Send a text message to a phone number.

        Args:
            to: Recipient phone number (with country code, no +)
            text: Message text to send

        Returns:
            API response dict with message_id
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }

        return await self._send_message(payload)

    async def send_buttons(
        self,
        to: str,
        body: str,
        buttons: List[Dict[str, str]],
        header: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an interactive button message.

        Args:
            to: Recipient phone number
            body: Main message text
            buttons: List of button dicts with 'id' and 'title' keys (max 3)
            header: Optional header text

        Returns:
            API response dict
        """
        button_list = [
            {
                "type": "reply",
                "reply": {"id": btn["id"], "title": btn["title"][:20]}  # Title max 20 chars
            }
            for btn in buttons[:3]  # WhatsApp allows max 3 buttons
        ]

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body},
                "action": {"buttons": button_list}
            }
        }

        if header:
            payload["interactive"]["header"] = {"type": "text", "text": header}

        return await self._send_message(payload)

    async def send_list(
        self,
        to: str,
        body: str,
        button_text: str,
        sections: List[Dict[str, Any]],
        header: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an interactive list message.

        Args:
            to: Recipient phone number
            body: Main message text
            button_text: Text on the list button
            sections: List of sections, each with 'title' and 'rows' (list of {id, title, description})
            header: Optional header text

        Returns:
            API response dict
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": body},
                "action": {
                    "button": button_text,
                    "sections": sections
                }
            }
        }

        if header:
            payload["interactive"]["header"] = {"type": "text", "text": header}

        return await self._send_message(payload)

    async def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send a pre-approved message template.

        Args:
            to: Recipient phone number
            template_name: Name of approved template
            language_code: Template language (default: en)
            components: Optional template parameter components

        Returns:
            API response dict
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code}
            }
        }

        if components:
            payload["template"]["components"] = components

        return await self._send_message(payload)

    async def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as read.

        Args:
            message_id: WhatsApp message ID to mark as read

        Returns:
            API response dict
        """
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload
            )
            resp.raise_for_status()
            return resp.json()

    async def _send_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to send message payload to WhatsApp API.

        Args:
            payload: Message payload dict

        Returns:
            API response with message_id

        Raises:
            httpx.HTTPStatusError: If API returns error status
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=payload
                )
                resp.raise_for_status()
                result = resp.json()

                logger.info(
                    "whatsapp_message_sent",
                    to=payload.get("to"),
                    type=payload.get("type"),
                    message_id=result.get("messages", [{}])[0].get("id")
                )

                return result

        except httpx.HTTPStatusError as e:
            logger.error(
                "whatsapp_send_failed",
                status_code=e.response.status_code,
                error=e.response.text,
                payload_type=payload.get("type")
            )
            raise
        except Exception as e:
            logger.error("whatsapp_send_error", error=str(e))
            raise


# Global client instance
_client: Optional[WhatsAppClient] = None


def get_whatsapp_client() -> WhatsAppClient:
    """Get or create WhatsApp client singleton."""
    global _client
    if _client is None:
        _client = WhatsAppClient()
    return _client
