"""AI-powered conversational assistant for web chat."""
import structlog
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
from app.core.settings import get_settings
from datetime import datetime, timedelta
import json

logger = structlog.get_logger(__name__)


class ChatAIAssistant:
    """OpenAI-powered conversational assistant for flight booking chat."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

        self.system_prompt = """You are a helpful and friendly flight booking assistant for SureFlights, a Nigerian domestic flight booking service.

Your personality:
- Warm, conversational, and helpful
- Like a knowledgeable travel agent
- Proactive in suggesting better options
- Patient and understanding

Your capabilities:
1. Search for flights (single date or date range)
2. Analyze flight results and recommend best options
3. Find cheapest flights
4. Find fastest flights
5. Compare different dates
6. Explain price differences
7. Suggest alternatives if no flights found

Available airports in Nigeria:
- Lagos (LOS)
- Abuja (ABV)
- Port Harcourt (PHC)
- Kano (KAN)
- Enugu (ENU)

When discussing flight results:
- Highlight the cheapest option
- Point out fastest flights
- Mention best value (balance of price and time)
- Suggest flexible dates if prices are high
- Be conversational and friendly

Keep responses concise but helpful. Use emojis sparingly for warmth.
"""

    async def analyze_flight_results(
        self,
        flights: List[Dict[str, Any]],
        user_question: str,
        search_params: Dict[str, Any]
    ) -> str:
        """Analyze flight results and answer user's question conversationally.

        Args:
            flights: List of flight offers
            user_question: User's question about the flights
            search_params: Original search parameters

        Returns:
            Conversational response about the flights
        """
        if not self.client:
            return self._fallback_analysis(flights, user_question)

        try:
            # Prepare flight data for AI
            flight_summary = self._prepare_flight_summary(flights)

            prompt = f"""The user searched for flights from {search_params.get('from_')} to {search_params.get('to')} on {search_params.get('date')}.

Here are the available flights:

{flight_summary}

User's question: "{user_question}"

Provide a helpful, conversational response. Be specific with flight numbers/options. If they're asking about cheapest, fastest, or best value, analyze the data and recommend accordingly.
"""

            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            error_msg = str(e)
            # Check for specific quota error
            if "429" in error_msg or "quota" in error_msg.lower():
                logger.warning("openai_quota_exceeded", error=error_msg, fallback="using_basic_analysis")
            else:
                logger.error("ai_analysis_error", error=error_msg)
            return self._fallback_analysis(flights, user_question)

    def _prepare_flight_summary(self, flights: List[Dict[str, Any]]) -> str:
        """Prepare a summary of flights for AI analysis."""
        summary = []

        for i, flight in enumerate(flights[:10], 1):
            price_ngn = flight.get("price_ngn") or flight.get("price", 0)
            slices = flight.get("slices", [{}])
            segments = slices[0].get("segments", [{}]) if slices else [{}]

            airline = segments[0].get("airline", "Unknown") if segments else "Unknown"
            departure = segments[0].get("departure_time", "")[:5] if segments and segments[0].get("departure_time") else "N/A"
            arrival = segments[0].get("arrival_time", "")[:5] if segments and segments[0].get("arrival_time") else "N/A"
            duration = slices[0].get("duration_minutes", 0) if slices else 0

            summary.append(
                f"Option {i}: {airline} - {departure} to {arrival} ({duration} mins) - ₦{price_ngn:,.0f}"
            )

        return "\n".join(summary)

    def _fallback_analysis(self, flights: List[Dict[str, Any]], question: str) -> str:
        """Fallback analysis when OpenAI is not available."""
        question_lower = question.lower()

        if "cheap" in question_lower or "lowest" in question_lower or "affordable" in question_lower:
            return self._find_cheapest(flights)
        elif "fast" in question_lower or "quick" in question_lower or "shortest" in question_lower:
            return self._find_fastest(flights)
        elif "best" in question_lower or "recommend" in question_lower:
            return self._find_best_value(flights)
        else:
            return "I can help you find the cheapest flight, fastest flight, or best value option. What would you prefer?"

    def _find_cheapest(self, flights: List[Dict[str, Any]]) -> str:
        """Find and describe the cheapest flight."""
        if not flights:
            return "No flights available to compare."

        cheapest = min(flights, key=lambda f: f.get("price_ngn", f.get("price", float('inf'))))
        index = flights.index(cheapest) + 1

        price = cheapest.get("price_ngn") or cheapest.get("price", 0)
        slices = cheapest.get("slices", [{}])
        segments = slices[0].get("segments", [{}]) if slices else [{}]
        airline = segments[0].get("airline", "Unknown") if segments else "Unknown"

        return f"💰 The cheapest option is **Option {index}** - {airline} for ₦{price:,.0f}. This is the most affordable choice!"

    def _find_fastest(self, flights: List[Dict[str, Any]]) -> str:
        """Find and describe the fastest flight."""
        if not flights:
            return "No flights available to compare."

        fastest = min(
            flights,
            key=lambda f: f.get("slices", [{}])[0].get("duration_minutes", float('inf')) if f.get("slices") else float('inf')
        )
        index = flights.index(fastest) + 1

        slices = fastest.get("slices", [{}])
        duration = slices[0].get("duration_minutes", 0) if slices else 0
        hours = duration // 60
        mins = duration % 60

        segments = slices[0].get("segments", [{}]) if slices else [{}]
        airline = segments[0].get("airline", "Unknown") if segments else "Unknown"

        return f"⚡ The fastest option is **Option {index}** - {airline} at {hours}h {mins}m. Gets you there quickest!"

    def _find_best_value(self, flights: List[Dict[str, Any]]) -> str:
        """Find and describe the best value flight (balance of price and time)."""
        if not flights:
            return "No flights available to compare."

        # Calculate a simple value score (normalized price + duration)
        def value_score(flight):
            price = flight.get("price_ngn", flight.get("price", 0))
            slices = flight.get("slices", [{}])
            duration = slices[0].get("duration_minutes", 0) if slices else 0

            # Normalize (lower is better)
            price_norm = price / 100000  # Rough normalization
            duration_norm = duration / 120  # Normalize to ~2 hours

            return price_norm + duration_norm

        best = min(flights, key=value_score)
        index = flights.index(best) + 1

        price = best.get("price_ngn") or best.get("price", 0)
        slices = best.get("slices", [{}])
        segments = slices[0].get("segments", [{}]) if slices else [{}]
        airline = segments[0].get("airline", "Unknown") if segments else "Unknown"
        duration = slices[0].get("duration_minutes", 0) if slices else 0
        hours = duration // 60
        mins = duration % 60

        return f"⭐ I'd recommend **Option {index}** - {airline} for ₦{price:,.0f} ({hours}h {mins}m). It's the best balance of price and travel time!"

    async def understand_search_intent(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Understand user's search intent from natural language.

        Args:
            message: User's message
            context: Optional conversation context

        Returns:
            Dict with search parameters or analysis request
        """
        if not self.client:
            return self._fallback_intent_parsing(message)

        try:
            today = datetime.now().strftime("%Y-%m-%d")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            prompt = f"""Analyze this flight booking request: "{message}"

Today is {today}. Tomorrow is {tomorrow}.

Extract and return JSON with ONE of these structures:

For SINGLE DATE search:
{{
  "intent": "search_flight",
  "from": "LOS",  // Airport code
  "to": "ABV",
  "date": "2025-11-15",  // YYYY-MM-DD
  "adults": 1
}}

For DATE RANGE search:
{{
  "intent": "search_date_range",
  "from": "LOS",
  "to": "ABV",
  "start_date": "2025-11-15",
  "end_date": "2025-11-20",
  "adults": 1
}}

For ANALYZING existing results:
{{
  "intent": "analyze",
  "question": "which is cheapest"
}}

For OTHER questions:
{{
  "intent": "conversation",
  "topic": "general_help"
}}

Return ONLY valid JSON, no markdown.
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

            # Remove markdown code blocks if present
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
                result = result.strip()

            intent_data = json.loads(result)
            logger.info("ai_intent_parsed", intent=intent_data.get("intent"))
            return intent_data

        except Exception as e:
            error_msg = str(e)
            # Check for specific quota error
            if "429" in error_msg or "quota" in error_msg.lower():
                logger.warning("openai_quota_exceeded", error=error_msg, fallback="using_regex_parser")
            else:
                logger.error("ai_intent_error", error=error_msg)
            return self._fallback_intent_parsing(message)

    def _fallback_intent_parsing(self, message: str) -> Dict[str, Any]:
        """Fallback intent parsing using regex (enhanced)."""
        import re
        from datetime import datetime

        text_lower = message.lower()

        # Check if analyzing results
        if any(word in text_lower for word in ["cheap", "fast", "best", "recommend", "which", "compare"]):
            return {"intent": "analyze", "question": message}

        # Try to extract cities and dates
        airports = {
            "lagos": "LOS", "los": "LOS",
            "abuja": "ABV", "abv": "ABV",
            "port harcourt": "PHC", "phc": "PHC", "ph": "PHC",
            "kano": "KAN", "kan": "KAN",
            "enugu": "ENU", "enu": "ENU",
            "london": "LON", "lon": "LON"  # Added London for international
        }

        origin = None
        destination = None

        for city, code in airports.items():
            if city in text_lower:
                if "from " + city in text_lower:
                    origin = code
                elif "to " + city in text_lower:
                    destination = code
                elif not origin:
                    origin = code
                elif not destination:
                    destination = code

        # Extract dates - support multiple formats
        dates = []

        # Format 1: YYYY-MM-DD (already supported)
        yyyy_mm_dd = re.findall(r'(\d{4})-(\d{2})-(\d{2})', message)
        for match in yyyy_mm_dd:
            try:
                date_obj = datetime(int(match[0]), int(match[1]), int(match[2]))
                dates.append(date_obj.strftime("%Y-%m-%d"))
            except ValueError:
                continue

        # Format 2: DD-MM-YYYY or MM-DD-YYYY
        if not dates:
            dd_mm_yyyy = re.findall(r'(\d{2})-(\d{2})-(\d{4})', message)
            for match in dd_mm_yyyy:
                # Try DD-MM-YYYY first (more common internationally)
                try:
                    date_obj = datetime(int(match[2]), int(match[1]), int(match[0]))
                    dates.append(date_obj.strftime("%Y-%m-%d"))
                except ValueError:
                    # Try MM-DD-YYYY (US format)
                    try:
                        date_obj = datetime(int(match[2]), int(match[0]), int(match[1]))
                        dates.append(date_obj.strftime("%Y-%m-%d"))
                    except ValueError:
                        continue

        # Format 3: Natural language dates like "November 15th", "Nov 15"
        if not dates:
            month_names = {
                "january": 1, "jan": 1,
                "february": 2, "feb": 2,
                "march": 3, "mar": 3,
                "april": 4, "apr": 4,
                "may": 5,
                "june": 6, "jun": 6,
                "july": 7, "jul": 7,
                "august": 8, "aug": 8,
                "september": 9, "sep": 9, "sept": 9,
                "october": 10, "oct": 10,
                "november": 11, "nov": 11,
                "december": 12, "dec": 12
            }

            for month_name, month_num in month_names.items():
                pattern = rf'{month_name}\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:\s+(\d{{4}}))?'
                match = re.search(pattern, text_lower)
                if match:
                    day = int(match.group(1))
                    year = int(match.group(2)) if match.group(2) else datetime.now().year
                    try:
                        date_obj = datetime(year, month_num, day)
                        dates.append(date_obj.strftime("%Y-%m-%d"))
                        break
                    except ValueError:
                        continue

        if origin and destination and dates:
            if len(dates) >= 2:
                # Date range search
                return {
                    "intent": "search_date_range",
                    "from": origin,
                    "to": destination,
                    "start_date": dates[0],
                    "end_date": dates[1],
                    "adults": 1
                }
            else:
                # Single date search
                return {
                    "intent": "search_flight",
                    "from": origin,
                    "to": destination,
                    "date": dates[0],
                    "adults": 1
                }

        return {"intent": "conversation", "topic": "unclear_request"}


# Global AI assistant instance
_assistant: Optional[ChatAIAssistant] = None


def get_chat_ai_assistant() -> ChatAIAssistant:
    """Get or create chat AI assistant singleton."""
    global _assistant
    if _assistant is None:
        _assistant = ChatAIAssistant()
    return _assistant
