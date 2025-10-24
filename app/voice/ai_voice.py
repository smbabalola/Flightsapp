"""AI voice assistant using OpenAI for speech processing."""
import structlog
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from app.core.settings import get_settings
from datetime import datetime, timedelta

logger = structlog.get_logger(__name__)


class VoiceAIAssistant:
    """OpenAI-powered voice assistant for flight booking."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

        self.system_prompt = """You are a helpful voice assistant for SureFlights, a Nigerian domestic flight booking service.

You help customers book flights over the phone by:
1. Collecting origin city
2. Collecting destination city
3. Collecting travel date
4. Searching and presenting flight options
5. Collecting passenger details
6. Completing the booking

Available Nigerian airports:
- Lagos (LOS)
- Abuja (ABV)
- Port Harcourt (PHC)
- Kano (KAN)
- Enugu (ENU)

Be conversational, clear, and patient. Speak naturally as if talking on the phone.
For dates, interpret relative terms like "tomorrow", "next week" based on today's date.
"""

    async def extract_city(self, speech_text: str) -> Optional[str]:
        """Extract city/airport code from speech.

        Args:
            speech_text: Transcribed speech

        Returns:
            Airport code or None
        """
        if not self.client:
            return None

        try:
            prompt = f"""From this speech text, extract the Nigerian city or airport code: "{speech_text}"

Valid cities: Lagos (LOS), Abuja (ABV), Port Harcourt (PHC), Kano (KAN), Enugu (ENU)

Return ONLY the 3-letter airport code (e.g., "LOS", "ABV") or "unknown" if unclear.

Speech: "{speech_text}"
"""

            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=10
            )

            result = response.choices[0].message.content.strip().upper()

            if result in ["LOS", "ABV", "PHC", "KAN", "ENU"]:
                logger.info("city_extracted", speech=speech_text, city=result)
                return result

            return None

        except Exception as e:
            logger.error("city_extraction_error", error=str(e))
            return None

    async def extract_date(self, speech_text: str) -> Optional[str]:
        """Extract travel date from speech.

        Args:
            speech_text: Transcribed speech

        Returns:
            Date in YYYY-MM-DD format or None
        """
        if not self.client:
            return None

        try:
            today = datetime.now().strftime("%Y-%m-%d")
            prompt = f"""From this speech text, extract the travel date: "{speech_text}"

Today is {today}.

Interpret relative dates:
- "tomorrow" -> {(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")}
- "next week" -> approximately 7 days from today
- specific dates like "November 15" or "15th of November"

Return the date in YYYY-MM-DD format or "unknown" if unclear.

Speech: "{speech_text}"
"""

            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=20
            )

            result = response.choices[0].message.content.strip()

            # Validate date format
            try:
                datetime.strptime(result, "%Y-%m-%d")
                logger.info("date_extracted", speech=speech_text, date=result)
                return result
            except ValueError:
                return None

        except Exception as e:
            logger.error("date_extraction_error", error=str(e))
            return None

    async def extract_selection(self, speech_text: str) -> Optional[int]:
        """Extract flight selection number from speech.

        Args:
            speech_text: Transcribed speech

        Returns:
            Selection number (1-5) or None
        """
        if not self.client:
            return None

        try:
            prompt = f"""From this speech text, extract the flight option number: "{speech_text}"

The customer should say a number from 1 to 5 (e.g., "option one", "number 3", "the second one").

Return ONLY the digit (1, 2, 3, 4, or 5) or "unknown" if unclear.

Speech: "{speech_text}"
"""

            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=5
            )

            result = response.choices[0].message.content.strip()

            if result.isdigit() and 1 <= int(result) <= 5:
                return int(result)

            return None

        except Exception as e:
            logger.error("selection_extraction_error", error=str(e))
            return None

    async def extract_passenger_name(self, speech_text: str) -> Optional[Dict[str, str]]:
        """Extract passenger name from speech.

        Args:
            speech_text: Transcribed speech

        Returns:
            Dict with first and last name or None
        """
        if not self.client:
            return None

        try:
            prompt = f"""From this speech text, extract the passenger's full name: "{speech_text}"

Return a JSON object with "first" and "last" name fields, or null if unclear.

Example: "John Adeola" -> {{"first": "John", "last": "Adeola"}}

Speech: "{speech_text}"
"""

            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=50
            )

            result = response.choices[0].message.content.strip()

            import json
            try:
                name = json.loads(result)
                if name and "first" in name and "last" in name:
                    logger.info("name_extracted", name=name)
                    return name
            except json.JSONDecodeError:
                pass

            return None

        except Exception as e:
            logger.error("name_extraction_error", error=str(e))
            return None


# Global AI assistant instance
_assistant: Optional[VoiceAIAssistant] = None


def get_voice_ai() -> VoiceAIAssistant:
    """Get or create voice AI assistant singleton."""
    global _assistant
    if _assistant is None:
        _assistant = VoiceAIAssistant()
    return _assistant
