import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict
from app.core.logging import logger
from datetime import datetime
from app.core.settings import get_settings
from app.db.session import SessionLocal
from sqlalchemy import text


def send_email(to_email: str, subject: str, body: str, is_html: bool = True) -> bool:
    """
    Send an email using SMTP.

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body (HTML or plain text)
        is_html: Whether the body is HTML (default: True)

    Returns:
        True if email sent successfully, False otherwise
    """
    # Get SMTP configuration from DB (overrides) or environment
    db_host = db_port = db_user = db_pass = db_from_email = db_from_name = db_use_tls = None
    try:
        with SessionLocal() as db:
            row = db.execute(text("SELECT host, port, user, password, from_email, from_name, use_tls FROM smtp_settings ORDER BY id ASC LIMIT 1")).fetchone()
            if row:
                db_host = row.host; db_port = row.port; db_user = row.user; db_pass = row.password
                db_from_email = row.from_email; db_from_name = row.from_name; db_use_tls = row.use_tls
    except Exception:
        pass
    smtp_host = db_host or os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(db_port or os.getenv('SMTP_PORT', '587'))
    smtp_user = db_user or os.getenv('SMTP_USER', '')
    smtp_password = db_pass or os.getenv('SMTP_PASSWORD', '')
    from_email = db_from_email or os.getenv('SMTP_FROM_EMAIL', smtp_user)
    from_name = db_from_name or os.getenv('SMTP_FROM_NAME', 'SureFlights')
    use_tls = bool(db_use_tls) if db_use_tls is not None else True

    # If SMTP not configured, just log and return
    if not smtp_user or not smtp_password:
        logger.warning("email_not_configured", to_email=to_email)
        logger.info("email_would_send", to_email=to_email, subject=subject)
        return False

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = to_email

        # Attach body
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if use_tls:
                server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info("email_sent", to_email=to_email, subject=subject)
        return True

    except Exception as e:
        logger.error("email_send_failed", to_email=to_email, error=str(e))
        return False


def send_booking_confirmation_email(
    to_email: str,
    booking_details: Dict,
    pnr: Optional[str] = None,
    etickets: Optional[List[str]] = None
) -> bool:
    """
    Send booking confirmation email with flight details.

    Args:
        to_email: Customer email
        booking_details: Dictionary containing flight and passenger info
        pnr: Booking reference number
        etickets: List of e-ticket numbers

    Returns:
        True if email sent successfully
    """
    subject = f"Booking Confirmed - {pnr or 'SureFlights'}"

    # Extract details
    passenger_name = booking_details.get('passenger_name', 'Valued Customer')
    route = booking_details.get('route', 'Your Flight')
    departure_date = booking_details.get('departure_date', '')
    airline = booking_details.get('airline', '')
    total_amount = booking_details.get('total_amount', 0)
    currency = booking_details.get('currency', 'NGN')

    # Format e-tickets
    etickets_html = ""
    if etickets and len(etickets) > 0:
        etickets_list = "".join([f"<li><strong>{ticket}</strong></li>" for ticket in etickets])
        etickets_html = f"""
        <div style="background: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #374151;">E-Ticket Numbers:</h3>
            <ul style="list-style: none; padding: 0; margin: 0;">
                {etickets_list}
            </ul>
        </div>
        """

    # Format price
    if currency == 'NGN':
        price_display = f"₦{int(total_amount):,}"
    else:
        price_display = f"{currency} {float(total_amount):.2f}"

    # Create HTML email body
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">Booking Confirmed!</h1>
        </div>

        <div style="padding: 30px; background: white;">
            <p style="font-size: 16px;">Dear {passenger_name},</p>

            <p>Thank you for booking with SureFlights! Your flight has been confirmed.</p>

            <div style="background: #eff6ff; border-left: 4px solid #2563eb; padding: 20px; margin: 20px 0;">
                <h2 style="margin-top: 0; color: #1d4ed8;">Booking Details</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; font-weight: 600; color: #4b5563;">Booking Reference:</td>
                        <td style="padding: 8px 0; color: #111827;"><strong>{pnr or 'N/A'}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: 600; color: #4b5563;">Route:</td>
                        <td style="padding: 8px 0; color: #111827;">{route}</td>
                    </tr>
                    {f'<tr><td style="padding: 8px 0; font-weight: 600; color: #4b5563;">Departure:</td><td style="padding: 8px 0; color: #111827;">{departure_date}</td></tr>' if departure_date else ''}
                    {f'<tr><td style="padding: 8px 0; font-weight: 600; color: #4b5563;">Airline:</td><td style="padding: 8px 0; color: #111827;">{airline}</td></tr>' if airline else ''}
                    <tr>
                        <td style="padding: 8px 0; font-weight: 600; color: #4b5563;">Total Paid:</td>
                        <td style="padding: 8px 0; color: #111827; font-size: 18px;"><strong style="color: #10b981;">{price_display}</strong></td>
                    </tr>
                </table>
            </div>

            {etickets_html}

            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0;">
                <p style="margin: 0; color: #92400e;">
                    <strong>Important:</strong> Please arrive at the airport at least 2 hours before departure for domestic flights and 3 hours for international flights.
                </p>
            </div>

            <p>Your e-tickets have been attached to this email. You can also access your booking details anytime from your dashboard.</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="http://localhost:8000/dashboard.html"
                   style="background-color: #2563eb; color: white; padding: 12px 30px;
                          text-decoration: none; border-radius: 5px; display: inline-block; font-weight: 600;">
                    View My Bookings
                </a>
            </div>

            <p>If you have any questions, please don't hesitate to contact our support team.</p>

            <p style="margin-top: 30px;">
                Safe travels!<br>
                <strong>The SureFlights Team</strong>
            </p>
        </div>

        <div style="background: #f3f4f6; padding: 20px; text-align: center; font-size: 12px; color: #6b7280;">
            <p style="margin: 0;">SureFlights - Your trusted partner for flight bookings worldwide</p>
            <p style="margin: 5px 0;">
                <a href="mailto:support@sureflights.com" style="color: #2563eb; text-decoration: none;">support@sureflights.com</a>
            </p>
        </div>
    </body>
    </html>
    """

    return send_email(to_email, subject, body, is_html=True)


def send_email_confirmation(email: str | None, pnr: str | None, etickets: List[str] | None) -> None:
    """Legacy function for backward compatibility"""
    if not email:
        logger.warning("email_send_no_recipient")
        return

    logger.info("email_send", extra={
        "email": email,
        "pnr": pnr or "",
        "tickets_count": len(etickets or [])
    })

    # Send booking confirmation
    booking_details = {
        'pnr': pnr,
        'passenger_name': 'Valued Customer'
    }

    send_booking_confirmation_email(
        to_email=email,
        booking_details=booking_details,
        pnr=pnr,
        etickets=etickets
    )


def send_welcome_email(to_email: str, first_name: str | None = None) -> bool:
    """Send a CEO-branded welcome email on registration."""
    settings = get_settings()
    app_name = settings.__dict__.get('app_name') or os.getenv('APP_NAME', 'GoCome')
    login_url = os.getenv('APP_LOGIN_URL', 'https://gocome.africa')
    ceo_name = os.getenv('CEO_NAME', 'Your Name')
    ceo_email = os.getenv('CEO_EMAIL', 'ceo@gocome.africa')

    fname = (first_name or '').strip() or 'there'
    # Allow subject/body overrides via DB first, then env or template path
    db_subject = None
    db_body = None
    try:
        with SessionLocal() as db:
            row = db.execute(text("SELECT welcome_subject, welcome_body FROM messaging_settings ORDER BY id ASC LIMIT 1")).fetchone()
            if row:
                db_subject = row.welcome_subject
                db_body = row.welcome_body
    except Exception:
        pass

    subject = (db_subject or os.getenv('WELCOME_EMAIL_SUBJECT') or f"Welcome to {app_name}!")

    # Build HTML body, with override from file or env if provided
    tpl_path = os.getenv('WELCOME_EMAIL_TEMPLATE_PATH')
    env_body = os.getenv('WELCOME_EMAIL_BODY')
    if tpl_path and os.path.exists(tpl_path):
        try:
            with open(tpl_path, 'r', encoding='utf-8') as f:
                raw = f.read()
        except Exception:
            raw = None
        if raw:
            body = raw
        else:
            body = None
    elif env_body:
        body = env_body
    else:
        body = None

    # Default template if no override
    if not body:
        if db_body:
            body = db_body
    if not body:
        body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height:1.6; color:#111; max-width:640px; margin:0 auto;">
      <div style="padding:24px 0; text-align:center;">
        <h1 style="margin:0; color:#111;">Welcome to {app_name} 🎉</h1>
      </div>
      <div style="background:#fff; padding:24px; border:1px solid #eee; border-radius:8px;">
        <p>Hi {fname},</p>
        <p>
          Welcome to <strong>{app_name}</strong>! 🎉
        </p>
        <p>
          I’m <strong>{ceo_name}</strong>, the founder and CEO, and I’m thrilled to have you join our community of travelers, explorers, and dreamers.
        </p>
        <p>
          At {app_name}, we believe travel should feel easy, local, and made for you.
          Whether you’re booking a quick flight from Lagos to Accra or planning your next big adventure abroad, {app_name} is built to help you go confidently — and come back with stories to tell.
        </p>
        <h3>Here’s what you can do next:</h3>
        <ul>
          <li>✈️ <strong>Search flights</strong> — discover the best fares instantly.</li>
          <li>💼 <strong>Add extras</strong> — choose your seat, bags, and more (powered by our partners).</li>
          <li>💳 <strong>Pay your way</strong> — local currency, secure checkout, no stress.</li>
        </ul>
        <p>
          Your account is now ready. Log in anytime at <a href="{login_url}" style="color:#2563eb;">{login_url}</a> and start exploring.
        </p>
        <p>
          If you ever need help, our support team is just a message away — or you can reach me directly at <a href="mailto:{ceo_email}">{ceo_email}</a>.
        </p>
        <p>Thanks for choosing {app_name}. We can’t wait to help you go (and come) everywhere you dream. 🌍</p>
        <p style="margin-top:24px;">
          Warm regards,<br>
          <strong>{ceo_name}</strong><br>
          Founder &amp; CEO, {app_name}<br>
          ✈️ <a href="{login_url}" style="color:#2563eb;">{login_url.replace('https://','').replace('http://','')}</a>
        </p>
      </div>
    </body>
    </html>
    """
    # Perform simple placeholder substitution
    body = (
        body
        .replace('{{first_name}}', fname)
        .replace('{{CEO_Name}}', ceo_name)
        .replace('{{APP_NAME}}', app_name)
        .replace('{{LOGIN_URL}}', login_url)
    )
    return send_email(to_email, subject, body, is_html=True)
