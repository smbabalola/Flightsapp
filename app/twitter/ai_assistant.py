"""AI-powered conversational assistant for Twitter DMs."""
import structlog
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from app.core.settings import get_settings

logger = structlog.get_logger(__name__)


class AIAssistant:
    """OpenAI-powered conversational assistant."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

        self.system_prompt = """You are a helpful flight booking assistant for SureFlights, a Nigerian domestic flight booking service.

Your role is to help customers:
1. Search for flights within Nigeria
2. Select flights
3. Collect passenger information
4. Complete bookings

Available airports in Nigeria:
- Lagos (LOS)
- Abuja (ABV)
- Port Harcourt (PHC)
- Kano (KAN)
- Enugu (ENU)

When customers ask about flights, extract:
- Origin city/airport
- Destination city/airport
- Travel date (format: YYYY-MM-DD)
- Number of passengers (default: 1 adult)

Be conversational, friendly, and helpful. Keep responses concise for Twitter DM format (max 280 characters when possible).

For ambiguous dates like "tomorrow", "next week", calculate the actual date based on today's date.
"""

    async def parse_flight_search(self, message: str, context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Parse flight search intent from user message using AI.

        Args:
            message: User's message
            context: Optional conversation context

        Returns:
            Dict with flight search parameters or None
        """
        if not self.client:
            logger.warning("openai_not_configured")
            return None

        try:
            prompt = f"""Extract flight search parameters from this message: "{message}"

Return a JSON object with these fields:
- from_: origin airport code (e.g., "LOS", "ABV")
- to: destination airport code
- date: travel date in YYYY-MM-DD format
- adults: number of adult passengers (default: 1)

If you cannot extract clear flight search parameters, return null.

Examples:
"Flight from Lagos to Abuja on Nov 15" -> {{"from_": "LOS", "to": "ABV", "date": "2025-11-15", "adults": 1}}
"LOS to ABV tomorrow" -> {{"from_": "LOS", "to": "ABV", "date": "2025-10-05", "adults": 1}}

Message: "{message}"
"""

            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )

            result = response.choices[0].message.content.strip()

            # Try to parse JSON response
            import json
            try:
                params = json.loads(result)
                if params and all(k in params for k in ["from_", "to", "date"]):
                    logger.info("ai_parsed_search", params=params)
                    return params
            except json.JSONDecodeError:
                logger.warning("ai_response_not_json", result=result)

            return None

        except Exception as e:
            logger.error("ai_parse_error", error=str(e))
            return None

    async def parse_passenger_info(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse passenger information from message using AI.

        Args:
            message: User's message with passenger details

        Returns:
            Dict with passenger info or None
        """
        if not self.client:
            logger.warning("openai_not_configured")
            return None

        try:
            prompt = f"""Extract passenger information from this message: "{message}"

Return a JSON object with these fields:
- first: first name
- last: last name
- email: email address
- phone: phone number (with country code)
- dob: date of birth in YYYY-MM-DD format

If you cannot extract complete passenger information, return null.

Message: "{message}"
"""

            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )

            result = response.choices[0].message.content.strip()

            import json
            try:
                params = json.loads(result)
                if params and all(k in params for k in ["first", "last", "email"]):
                    logger.info("ai_parsed_passenger", params=params)
                    return params
            except json.JSONDecodeError:
                logger.warning("ai_response_not_json", result=result)

            return None

        except Exception as e:
            logger.error("ai_parse_error", error=str(e))
            return None

    async def generate_response(self, user_message: str, context: Optional[str] = None) -> str:
        """Generate a conversational response using AI.

        Args:
            user_message: User's message
            context: Optional conversation context

        Returns:
            Generated response text
        """
        if not self.client:
            return "I'm currently unable to process your request. Please try again later."

        try:
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]

            if context:
                messages.append({"role": "assistant", "content": context})

            messages.append({"role": "user", "content": user_message})

            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=200
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error("ai_response_error", error=str(e))
            return "I encountered an error. Please rephrase your request."


# Global AI assistant instance
_assistant: Optional[AIAssistant] = None


def get_ai_assistant() -> AIAssistant:
    """Get or create AI assistant singleton."""
    global _assistant
    if _assistant is None:
        _assistant = AIAssistant()
    return _assistant
