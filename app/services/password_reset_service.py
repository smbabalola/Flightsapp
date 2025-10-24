import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import User, PasswordResetToken
from app.integrations.email_notifier import send_email
import hashlib


class PasswordResetService:
    TOKEN_EXPIRY_HOURS = 24

    @staticmethod
    def generate_reset_token() -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash the token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def request_password_reset(cls, db: Session, email: str, base_url: str) -> dict:
        """
        Create a password reset request and send email
        Returns: {"success": bool, "message": str}
        """
        # Find user by email
        user = db.query(User).filter(User.email == email).first()

        # Always return success to prevent email enumeration
        if not user:
            return {
                "success": True,
                "message": "If an account exists with this email, a password reset link has been sent."
            }

        # Generate token
        plain_token = cls.generate_reset_token()
        hashed_token = cls.hash_token(plain_token)

        # Invalidate any existing tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False
        ).update({"used": True})

        # Create new reset token
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=hashed_token,
            expires_at=datetime.utcnow() + timedelta(hours=cls.TOKEN_EXPIRY_HOURS),
            used=False
        )
        db.add(reset_token)
        db.commit()

        # Send reset email
        reset_link = f"{base_url}/reset-password.html?token={plain_token}"

        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Password Reset Request</h2>
                <p>Hello,</p>
                <p>We received a request to reset your password for your SureFlights account.</p>
                <p>Click the button below to reset your password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}"
                       style="background-color: #2563eb; color: white; padding: 12px 30px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                <p>Or copy and paste this link into your browser:</p>
                <p style="background: #f3f4f6; padding: 10px; word-break: break-all;">{reset_link}</p>
                <p><strong>This link will expire in {cls.TOKEN_EXPIRY_HOURS} hours.</strong></p>
                <p>If you didn't request this password reset, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                <p style="font-size: 12px; color: #6b7280;">
                    SureFlights - Your trusted partner for flight bookings worldwide
                </p>
            </div>
        </body>
        </html>
        """

        try:
            send_email(
                to_email=user.email,
                subject="Reset Your SureFlights Password",
                body=email_body
            )
        except Exception as e:
            # Log error but don't expose it to user
            print(f"Failed to send password reset email: {e}")

        return {
            "success": True,
            "message": "If an account exists with this email, a password reset link has been sent."
        }

    @classmethod
    def verify_reset_token(cls, db: Session, token: str) -> dict:
        """
        Verify if reset token is valid
        Returns: {"valid": bool, "user_id": int | None, "message": str}
        """
        hashed_token = cls.hash_token(token)

        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == hashed_token,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        ).first()

        if not reset_token:
            return {
                "valid": False,
                "user_id": None,
                "message": "Invalid or expired reset token"
            }

        return {
            "valid": True,
            "user_id": reset_token.user_id,
            "message": "Token is valid"
        }

    @classmethod
    def reset_password(cls, db: Session, token: str, new_password: str) -> dict:
        """
        Reset user password using token
        Returns: {"success": bool, "message": str}
        """
        # Verify token
        verification = cls.verify_reset_token(db, token)
        if not verification["valid"]:
            return {
                "success": False,
                "message": verification["message"]
            }

        # Get user
        user = db.query(User).filter(User.id == verification["user_id"]).first()
        if not user:
            return {
                "success": False,
                "message": "User not found"
            }

        # Hash new password (assuming you have a hash_password utility)
        from app.auth.jwt_service import hash_password
        user.hash_password = hash_password(new_password)

        # Mark token as used
        hashed_token = cls.hash_token(token)
        db.query(PasswordResetToken).filter(
            PasswordResetToken.token == hashed_token
        ).update({"used": True})

        db.commit()

        return {
            "success": True,
            "message": "Password has been reset successfully"
        }
