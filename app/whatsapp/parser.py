"""
Message parser for understanding user intents in WhatsApp messages.

Extracts flight search parameters, passenger details, and user commands from natural language.
"""
import re
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class Intent(str, Enum):
    """Recognized user intents."""
    SEARCH_FLIGHT = "search_flight"
    SELECT_OPTION = "select_option"
    PROVIDE_PASSENGER = "provide_passenger"
    CONFIRM_BOOKING = "confirm_booking"
    HELP = "help"
    START = "start"
    CANCEL = "cancel"
    STATUS = "status"
    UNKNOWN = "unknown"


# Airport codes and city mappings (common Nigerian routes)
AIRPORT_CODES = {
    "lagos": "LOS",
    "abuja": "ABV",
    "port harcourt": "PHC",
    "kano": "KAN",
    "enugu": "ENU",
    "ibadan": "IBA",
    "calabar": "CBQ",
    "jos": "JOS",
    "maiduguri": "MIU",
    "owerri": "QOW",
    "benin": "BNI",
    "akure": "AKR",
    "los": "LOS",
    "abv": "ABV",
    "phc": "PHC",
    "ph": "PHC",
    "kan": "KAN",
    "enu": "ENU",
}


class MessageParser:
    """Parses WhatsApp messages to extract intents and data."""

    @staticmethod
    def parse_intent(message: str, context_state: str = "initial") -> Intent:
        """Determine user intent from message text.

        Args:
            message: User's message text
            context_state: Current conversation state for context

        Returns:
            Detected Intent
        """
        msg_lower = message.lower().strip()

        # Command patterns
        if msg_lower in ["start", "hi", "hello", "hey", "help me book"]:
            return Intent.START

        if msg_lower in ["help", "?", "how", "what can you do"]:
            return Intent.HELP

        if msg_lower in ["cancel", "stop", "exit", "quit"]:
            return Intent.CANCEL

        if msg_lower in ["status", "my booking", "check status"]:
            return Intent.STATUS

        # Context-based intents
        if context_state == "viewing_results":
            # User selecting from options
            if re.match(r"^[0-9]+$", msg_lower) or msg_lower in ["1", "2", "3", "4", "5"]:
                return Intent.SELECT_OPTION

        if context_state == "selected_flight":
            # Expecting passenger details
            if any(word in msg_lower for word in ["passenger", "name", "email", "phone"]):
                return Intent.PROVIDE_PASSENGER

        if context_state == "reviewing_booking":
            # Expecting confirmation
            if msg_lower in ["yes", "confirm", "book", "proceed", "ok"]:
                return Intent.CONFIRM_BOOKING
            if msg_lower in ["no", "cancel"]:
                return Intent.CANCEL

        # Flight search patterns
        search_patterns = [
            r"(from|flying from|departure|leaving)\s+([a-z]+)",
            r"(to|flying to|arrival|going to)\s+([a-z]+)",
            r"(on|date|when|departure date)\s+([0-9\-/]+)",
        ]

        for pattern in search_patterns:
            if re.search(pattern, msg_lower):
                return Intent.SEARCH_FLIGHT

        # Generic flight search keywords
        if any(word in msg_lower for word in ["flight", "book", "search", "find", "fly"]):
            return Intent.SEARCH_FLIGHT

        return Intent.UNKNOWN

    @staticmethod
    def parse_flight_search(message: str) -> Optional[Dict[str, Any]]:
        """Extract flight search parameters from message.

        Args:
            message: User's message text

        Returns:
            Dict with 'from_', 'to', 'date', and 'adults' if parseable, else None
        """
        msg_lower = message.lower().strip()
        params = {"adults": 1}

        # Extract origin
        origin_patterns = [
            r"(?:from|leaving|departure)\s+([a-z\s]+?)(?:\s+to|\s+on|$)",
            r"^([a-z\s]+?)\s+to\s+",
        ]
        for pattern in origin_patterns:
            match = re.search(pattern, msg_lower)
            if match:
                origin = match.group(1).strip()
                params["from_"] = MessageParser._resolve_airport(origin)
                break

        # Extract destination
        dest_patterns = [
            r"(?:to|going to|arrival)\s+([a-z\s]+?)(?:\s+on|\s+date|$)",
            r"\s+to\s+([a-z\s]+?)(?:\s+on|$)",
        ]
        for pattern in dest_patterns:
            match = re.search(pattern, msg_lower)
            if match:
                dest = match.group(1).strip()
                params["to"] = MessageParser._resolve_airport(dest)
                break

        # Extract date
        date_patterns = [
            r"(?:on|date|when)\s+([0-9]{4}-[0-9]{2}-[0-9]{2})",  # YYYY-MM-DD
            r"(?:on|date|when)\s+([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{4})",  # DD-MM-YYYY or DD/MM/YYYY
            r"(?:on|date|when)\s+(tomorrow|today)",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, msg_lower)
            if match:
                date_str = match.group(1)
                parsed_date = MessageParser._parse_date(date_str)
                if parsed_date:
                    params["date"] = parsed_date
                break

        # Extract passenger count
        pax_match = re.search(r"([0-9]+)\s+(?:passenger|adult|person|people|pax)", msg_lower)
        if pax_match:
            params["adults"] = int(pax_match.group(1))

        # Validate we have minimum required params
        if "from_" in params and "to" in params and "date" in params:
            logger.info("flight_search_parsed", params=params)
            return params

        return None

    @staticmethod
    def parse_passenger_data(message: str) -> Optional[Dict[str, str]]:
        """Extract passenger information from message.

        Args:
            message: User's message text

        Returns:
            Dict with passenger fields if parseable, else None
        """
        data = {}

        # Extract name
        name_match = re.search(r"(?:name|passenger)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", message, re.IGNORECASE)
        if name_match:
            full_name = name_match.group(1).strip()
            parts = full_name.split()
            if len(parts) >= 2:
                data["first"] = parts[0]
                data["last"] = " ".join(parts[1:])

        # Extract email
        email_match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", message)
        if email_match:
            data["email"] = email_match.group(1)

        # Extract phone
        phone_match = re.search(r"(?:phone|tel|mobile)[:\s]*([\+0-9\s\-\(\)]{10,})", message, re.IGNORECASE)
        if phone_match:
            phone = re.sub(r"[\s\-\(\)]", "", phone_match.group(1))
            data["phone"] = phone

        # Extract DOB
        dob_match = re.search(r"(?:dob|date of birth|born)[:\s]*([0-9]{4}-[0-9]{2}-[0-9]{2})", message, re.IGNORECASE)
        if dob_match:
            data["dob"] = dob_match.group(1)

        if data:
            logger.info("passenger_data_parsed", fields=list(data.keys()))
            return data

        return None

    @staticmethod
    def _resolve_airport(city_or_code: str) -> Optional[str]:
        """Resolve city name or code to IATA code.

        Args:
            city_or_code: City name or airport code

        Returns:
            3-letter IATA code or None
        """
        normalized = city_or_code.lower().strip()

        # Direct match
        if normalized in AIRPORT_CODES:
            return AIRPORT_CODES[normalized]

        # Partial match
        for key, code in AIRPORT_CODES.items():
            if normalized in key or key in normalized:
                return code

        # Return as-is if already looks like airport code
        if len(normalized) == 3 and normalized.isalpha():
            return normalized.upper()

        return None

    @staticmethod
    def _parse_date(date_str: str) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format.

        Args:
            date_str: Date string (various formats)

        Returns:
            Date in YYYY-MM-DD format or None
        """
        if date_str == "today":
            return datetime.now().strftime("%Y-%m-%d")
        if date_str == "tomorrow":
            return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        # Try different date formats
        formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return None


def extract_message_text(webhook_data: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    """Extract message text and sender phone from WhatsApp webhook payload.

    Args:
        webhook_data: WhatsApp webhook JSON payload

    Returns:
        Tuple of (phone_number, message_text) or None
    """
    try:
        entry = webhook_data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        messages = value.get("messages", [])
        if not messages:
            return None

        msg = messages[0]
        phone = msg.get("from")
        msg_type = msg.get("type")

        # Extract text based on message type
        if msg_type == "text":
            text = msg.get("text", {}).get("body", "")
        elif msg_type == "button":
            text = msg.get("button", {}).get("text", "")
        elif msg_type == "interactive":
            interactive = msg.get("interactive", {})
            if interactive.get("type") == "button_reply":
                text = interactive.get("button_reply", {}).get("title", "")
            elif interactive.get("type") == "list_reply":
                text = interactive.get("list_reply", {}).get("title", "")
            else:
                text = ""
        else:
            text = ""

        if phone and text:
            return (phone, text.strip())

        return None

    except Exception as e:
        logger.error("message_extraction_error", error=str(e))
        return None
