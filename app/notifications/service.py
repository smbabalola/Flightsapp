"""
Notification service for sending emails, SMS, and WhatsApp messages.

Supports multiple providers:
- Email: SMTP, SendGrid, Mailgun
- SMS: Twilio, Africa's Talking, Termii
- WhatsApp: WhatsApp Business Cloud API
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
import httpx
import structlog
from app.core.settings import get_settings
from app.whatsapp.client import get_whatsapp_client

logger = structlog.get_logger(__name__)


class EmailService:
    """Email sending service."""

    def __init__(self):
        self.settings = get_settings()

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional)

        Returns:
            True if sent successfully
        """
        try:
            # Check if SMTP is configured
            smtp_host = self.settings.__dict__.get("smtp_host")
            smtp_port = self.settings.__dict__.get("smtp_port", 587)
            smtp_user = self.settings.__dict__.get("smtp_user")
            smtp_password = self.settings.__dict__.get("smtp_password")
            from_email = self.settings.__dict__.get("from_email", "noreply@sureflights.ng")

            if not smtp_host or not smtp_user or not smtp_password:
                # Log email instead of sending (for development)
                logger.info(
                    "email_simulated",
                    to=to_email,
                    subject=subject,
                    body_length=len(html_body)
                )
                print(f"\n📧 EMAIL SIMULATION")
                print(f"To: {to_email}")
                print(f"Subject: {subject}")
                print(f"Body:\n{html_body}\n")
                return True

            # Send via SMTP
            msg = MIMEMultipart("alternative")
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = subject

            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            logger.info("email_sent", to=to_email, subject=subject)
            return True

        except Exception as e:
            logger.error("email_send_failed", to=to_email, error=str(e))
            return False


class SMSService:
    """SMS sending service."""

    def __init__(self):
        self.settings = get_settings()

    async def send_sms(
        self,
        to_phone: str,
        message: str
    ) -> bool:
        """Send an SMS.

        Args:
            to_phone: Recipient phone number (E.164 format)
            message: SMS message text

        Returns:
            True if sent successfully
        """
        try:
            # Check which SMS provider is configured
            provider = self.settings.__dict__.get("sms_provider", "simulation")

            if provider == "twilio":
                return await self._send_via_twilio(to_phone, message)
            elif provider == "africastalking":
                return await self._send_via_africastalking(to_phone, message)
            elif provider == "termii":
                return await self._send_via_termii(to_phone, message)
            else:
                # Log SMS instead of sending (for development)
                logger.info(
                    "sms_simulated",
                    to=to_phone,
                    message=message[:100]
                )
                print(f"\n📱 SMS SIMULATION")
                print(f"To: {to_phone}")
                print(f"Message: {message}\n")
                return True

        except Exception as e:
            logger.error("sms_send_failed", to=to_phone, error=str(e))
            return False

    async def _send_via_twilio(self, to_phone: str, message: str) -> bool:
        """Send SMS via Twilio."""
        account_sid = self.settings.__dict__.get("twilio_account_sid")
        auth_token = self.settings.__dict__.get("twilio_auth_token")
        from_number = self.settings.__dict__.get("twilio_from_number")

        if not all([account_sid, auth_token, from_number]):
            raise ValueError("Twilio credentials not configured")

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                auth=(account_sid, auth_token),
                data={
                    "From": from_number,
                    "To": to_phone,
                    "Body": message
                }
            )
            response.raise_for_status()

        logger.info("sms_sent_twilio", to=to_phone)
        return True

    async def _send_via_africastalking(self, to_phone: str, message: str) -> bool:
        """Send SMS via Africa's Talking."""
        api_key = self.settings.__dict__.get("africastalking_api_key")
        username = self.settings.__dict__.get("africastalking_username")
        from_id = self.settings.__dict__.get("africastalking_from", "SureFlights")

        if not all([api_key, username]):
            raise ValueError("Africa's Talking credentials not configured")

        url = "https://api.africastalking.com/version1/messaging"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "apiKey": api_key,
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "username": username,
                    "to": to_phone,
                    "message": message,
                    "from": from_id
                }
            )
            response.raise_for_status()

        logger.info("sms_sent_africastalking", to=to_phone)
        return True

    async def _send_via_termii(self, to_phone: str, message: str) -> bool:
        """Send SMS via Termii (Nigerian provider)."""
        api_key = self.settings.__dict__.get("termii_api_key")
        sender_id = self.settings.__dict__.get("termii_sender_id", "SureFlight")

        if not api_key:
            raise ValueError("Termii API key not configured")

        url = "https://api.ng.termii.com/api/sms/send"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "to": to_phone,
                    "from": sender_id,
                    "sms": message,
                    "type": "plain",
                    "channel": "generic",
                    "api_key": api_key
                }
            )
            response.raise_for_status()

        logger.info("sms_sent_termii", to=to_phone)
        return True


class WhatsAppService:
    """WhatsApp messaging service."""

    def __init__(self):
        self.settings = get_settings()
        self.client = None

    def _get_client(self):
        """Lazy load WhatsApp client."""
        if self.client is None:
            try:
                # Check if credentials are configured
                if (self.settings.whatsapp_phone_number_id and
                    self.settings.whatsapp_access_token and
                    self.settings.whatsapp_phone_number_id != "your_phone_number_id" and
                    self.settings.whatsapp_access_token != "your_whatsapp_access_token"):
                    self.client = get_whatsapp_client()
                else:
                    logger.info("whatsapp_credentials_not_configured_using_simulation")
            except Exception as e:
                logger.warning("whatsapp_client_init_failed", error=str(e))
        return self.client

    async def send_whatsapp(
        self,
        to_phone: str,
        message: str,
        use_template: bool = False
    ) -> bool:
        """Send a WhatsApp message.

        Args:
            to_phone: Recipient phone number (with country code, no +)
            message: Message text to send
            use_template: Whether to use a template (for first message to user)

        Returns:
            True if sent successfully
        """
        try:
            client = self._get_client()
            if not client:
                # Simulate WhatsApp in development
                logger.info(
                    "whatsapp_simulated",
                    to=to_phone,
                    message_length=len(message)
                )
                try:
                    print(f"\n[WHATSAPP SIMULATION]")
                    print(f"To: {to_phone}")
                    print(f"Message:\n{message}\n")
                except UnicodeEncodeError:
                    # Handle Windows console encoding issues
                    print(f"\n[WHATSAPP SIMULATION]")
                    print(f"To: {to_phone}")
                    print(f"Message length: {len(message)} characters")
                return True

            # Send via WhatsApp Cloud API
            # Remove + if present in phone number
            clean_phone = to_phone.replace("+", "").strip()

            result = await client.send_text(clean_phone, message)

            logger.info("whatsapp_sent", to=clean_phone, message_id=result.get("messages", [{}])[0].get("id"))
            return True

        except Exception as e:
            logger.error("whatsapp_send_failed", to=to_phone, error=str(e))
            # Don't fail the entire notification flow
            return False


class NotificationService:
    """Unified notification service for emails, SMS, and WhatsApp."""

    def __init__(self):
        self.email = EmailService()
        self.sms = SMSService()
        self.whatsapp = WhatsAppService()

    async def send_booking_confirmation(
        self,
        email: str,
        phone: Optional[str],
        pnr: str,
        route: str,
        date: str,
        passenger_name: str,
        amount: float
    ) -> None:
        """Send booking confirmation notification.

        Args:
            email: Customer email
            phone: Customer phone (optional)
            pnr: Booking reference
            route: Flight route
            date: Travel date
            passenger_name: Passenger name
            amount: Total amount paid
        """
        # Email
        subject = f"Booking Confirmed - {pnr}"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2c3e50;">✈️ Booking Confirmed!</h2>
            <p>Dear {passenger_name},</p>
            <p>Your flight booking has been confirmed.</p>

            <div style="background: #f5f7fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Booking Details</h3>
                <p><strong>Reference:</strong> {pnr}</p>
                <p><strong>Route:</strong> {route}</p>
                <p><strong>Date:</strong> {date}</p>
                <p><strong>Amount:</strong> ₦{amount:,.2f}</p>
            </div>

            <p>Your e-ticket will be sent to you once payment is confirmed.</p>

            <p style="color: #666; font-size: 0.9em;">
                Thank you for choosing SureFlights!<br>
                For support, contact us at support@sureflights.ng
            </p>
        </body>
        </html>
        """

        await self.email.send_email(email, subject, html_body)

        # SMS
        if phone:
            sms_message = (
                f"SureFlights: Your booking {pnr} for {route} on {date} is confirmed. "
                f"Amount: ₦{amount:,.0f}. E-ticket will be sent after payment."
            )
            await self.sms.send_sms(phone, sms_message)

    async def send_payment_received(
        self,
        email: str,
        phone: Optional[str],
        pnr: str,
        amount: float
    ) -> None:
        """Send payment received notification."""
        # Email
        subject = f"Payment Received - {pnr}"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #27ae60;">💳 Payment Received!</h2>
            <p>We have received your payment of ₦{amount:,.2f} for booking {pnr}.</p>
            <p>Your e-ticket is being processed and will be sent to you shortly.</p>
            <p style="color: #666; font-size: 0.9em;">
                Thank you for your payment!<br>
                SureFlights Team
            </p>
        </body>
        </html>
        """

        await self.email.send_email(email, subject, html_body)

        # SMS
        if phone:
            sms_message = (
                f"SureFlights: Payment of ₦{amount:,.0f} received for {pnr}. "
                f"E-ticket will be sent shortly."
            )
            await self.sms.send_sms(phone, sms_message)

    async def send_eticket(
        self,
        email: str,
        phone: Optional[str],
        pnr: str,
        etickets: List[str]
    ) -> None:
        """Send e-ticket notification."""
        # Email
        subject = f"E-Ticket - {pnr}"
        tickets_list = "<br>".join([f"• {ticket}" for ticket in etickets])

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #3498db;">🎫 Your E-Tickets</h2>
            <p>Your e-tickets for booking {pnr} are ready!</p>

            <div style="background: #f5f7fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0;">E-Ticket Numbers</h3>
                {tickets_list}
            </div>

            <p><strong>Important:</strong> Please present these e-ticket numbers at check-in.</p>

            <p style="color: #666; font-size: 0.9em;">
                Have a safe flight!<br>
                SureFlights Team
            </p>
        </body>
        </html>
        """

        await self.email.send_email(email, subject, html_body)

        # SMS
        if phone:
            tickets_str = ", ".join(etickets)
            sms_message = (
                f"SureFlights: Your e-tickets for {pnr}: {tickets_str}. "
                f"Present at check-in. Have a safe flight!"
            )
            await self.sms.send_sms(phone, sms_message)

    async def send_whatsapp_booking_confirmation(
        self,
        phone: str,
        pnr: str,
        etickets: List[str],
        flight_details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send WhatsApp booking confirmation with itinerary.

        Args:
            phone: Customer phone number
            pnr: Booking reference
            etickets: List of e-ticket numbers
            flight_details: Optional flight details from raw_offer
        """
        if not phone:
            logger.info("whatsapp_skipped_no_phone", pnr=pnr)
            return

        # Format e-ticket list
        eticket_list = "\n".join([f"  • {ticket}" for ticket in etickets])

        # Build itinerary message
        message = f"""✈️ *BOOKING CONFIRMED*

Your flight booking is confirmed!

*Booking Reference:* {pnr}

*E-Ticket Numbers:*
{eticket_list}
"""

        # Add flight details if available
        if flight_details:
            try:
                # Extract flight info from raw_offer
                slices = flight_details.get("slices", [])
                if slices:
                    message += "\n*Flight Details:*\n"
                    for idx, slice_info in enumerate(slices, 1):
                        segments = slice_info.get("segments", [])
                        if segments:
                            first_seg = segments[0]
                            last_seg = segments[-1]

                            origin = first_seg.get("origin", {}).get("iata_code", "")
                            destination = last_seg.get("destination", {}).get("iata_code", "")
                            airline = first_seg.get("marketing_carrier", {}).get("name", "")
                            departure_time = first_seg.get("departing_at", "")
                            arrival_time = last_seg.get("arriving_at", "")

                            # Parse datetime strings (ISO format: 2025-10-15T14:30:00)
                            if departure_time:
                                dep_date = departure_time.split("T")[0]
                                dep_time = departure_time.split("T")[1][:5] if "T" in departure_time else ""
                            else:
                                dep_date = ""
                                dep_time = ""

                            if arrival_time:
                                arr_time = arrival_time.split("T")[1][:5] if "T" in arrival_time else ""
                            else:
                                arr_time = ""

                            if len(slices) > 1:
                                message += f"\n*Flight {idx}:* {origin} → {destination}\n"
                            else:
                                message += f"\n*Route:* {origin} → {destination}\n"

                            message += f"  Airline: {airline}\n"
                            message += f"  Date: {dep_date}\n"
                            message += f"  Departure: {dep_time}\n"
                            message += f"  Arrival: {arr_time}\n"

                            # Add stops info
                            if len(segments) > 1:
                                stops = len(segments) - 1
                                message += f"  Stops: {stops}\n"

                # Add passenger count if available
                passengers = flight_details.get("passengers", [])
                if passengers:
                    message += f"\n*Passengers:* {len(passengers)}\n"

                # Add total amount if available
                total_amount = flight_details.get("total_amount")
                total_currency = flight_details.get("total_currency", "NGN")
                if total_amount:
                    currency_symbol = "₦" if total_currency == "NGN" else total_currency
                    message += f"*Total Paid:* {currency_symbol}{float(total_amount):,.2f}\n"

            except Exception as e:
                logger.error("whatsapp_flight_details_parse_error", error=str(e))
                # Continue without flight details

        # Add instructions
        message += """
*Next Steps:*
1. Save your e-ticket numbers
2. Arrive at airport 2-3 hours before departure
3. Present e-ticket at check-in counter
4. Have a safe flight! ✈️

_Thank you for choosing SureFlights!_

For support, contact us at support@sureflights.ng
"""

        await self.whatsapp.send_whatsapp(phone, message)

    async def send_cancellation_confirmed(
        self,
        email: str,
        phone: Optional[str],
        pnr: str,
        refund_amount: float,
        currency: str = "NGN"
    ) -> None:
        """Send cancellation confirmation notification."""
        # Email
        subject = f"Booking Cancelled - {pnr}"
        currency_symbol = "₦" if currency == "NGN" else "$"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #e74c3c;">❌ Booking Cancelled</h2>
            <p>Your booking {pnr} has been cancelled.</p>

            <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <h3 style="margin-top: 0;">Cancellation Details</h3>
                <p><strong>Reference:</strong> {pnr}</p>
                <p><strong>Refund Amount:</strong> {currency_symbol}{refund_amount:,.2f}</p>
                <p><strong>Status:</strong> Confirmed</p>
            </div>

            <p>Your refund will be processed within 5-10 business days and credited to your original payment method.</p>

            <p style="color: #666; font-size: 0.9em;">
                If you have any questions, please contact us at support@sureflights.ng<br>
                SureFlights Team
            </p>
        </body>
        </html>
        """

        await self.email.send_email(email, subject, html_body)

        # SMS
        if phone:
            sms_message = (
                f"SureFlights: Your booking {pnr} has been cancelled. "
                f"Refund of {currency_symbol}{refund_amount:,.0f} will be processed in 5-10 days."
            )
            await self.sms.send_sms(phone, sms_message)

    async def send_cancellation_pending(
        self,
        email: str,
        phone: Optional[str],
        pnr: str
    ) -> None:
        """Send cancellation request received notification."""
        # Email
        subject = f"Cancellation Request - {pnr}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #f39c12;">⏳ Cancellation Request Received</h2>
            <p>We have received your cancellation request for booking {pnr}.</p>

            <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>What's Next?</strong></p>
                <p>• Our team is processing your cancellation</p>
                <p>• We're calculating your refund amount</p>
                <p>• You'll receive confirmation within 24 hours</p>
            </div>

            <p style="color: #666; font-size: 0.9em;">
                For urgent matters, contact us at support@sureflights.ng<br>
                SureFlights Team
            </p>
        </body>
        </html>
        """

        await self.email.send_email(email, subject, html_body)

        # SMS
        if phone:
            sms_message = (
                f"SureFlights: Cancellation request for {pnr} received. "
                f"You'll receive confirmation within 24 hours."
            )
            await self.sms.send_sms(phone, sms_message)


# Global notification service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get or create notification service singleton."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
