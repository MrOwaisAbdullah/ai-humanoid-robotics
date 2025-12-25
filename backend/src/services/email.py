"""
Email service for sending password reset emails and other notifications.

This module handles email configuration and sending using SMTP or Resend.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from email.utils import formataddr
import httpx

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP or Resend."""

    def __init__(self):
        # Email service type: 'resend' or 'smtp'
        self.email_service = os.getenv("EMAIL_SERVICE", "smtp")

        # SMTP configuration
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")

        # Resend configuration
        self.resend_api_key = os.getenv("RESEND_API_KEY")

        # Common email settings
        self.email_from = os.getenv("EMAIL_FROM") or os.getenv("EMAIL_FROM_ADDRESS", "noreply@yourdomain.com")
        self.email_from_name = os.getenv("EMAIL_FROM_NAME", "AI Book")
        self.use_tls = os.getenv("SMTP_TLS", "true").lower() == "true"

    async def send_verification_email(self, to_email: str, verification_token: str, frontend_url: str) -> bool:
        """
        Send email verification email.

        Args:
            to_email: Recipient email address
            verification_token: Email verification token
            frontend_url: Frontend URL for verification link

        Returns:
            True if email was sent successfully, False otherwise
        """
        # Create verification link
        verification_link = f"{frontend_url}/verify-email?token={verification_token}"

        # HTML content
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 5px;
                    border: 1px solid #ddd;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .button {{
                    display: inline-block;
                    background-color: #10a37f;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>AI Book</h1>
                    <h2>Verify Your Email Address</h2>
                </div>

                <p>Hello,</p>

                <p>Thank you for signing up for AI Book! Please click the button below to verify your email address:</p>

                <p style="text-align: center;">
                    <a href="{verification_link}" class="button">Verify Email</a>
                </p>

                <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                <p>{verification_link}</p>

                <p>This link will expire in 24 hours for security reasons.</p>

                <p>If you didn't create an account, you can safely ignore this email.</p>

                <div class="footer">
                    <p>Best regards,<br>The AI Book Team</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        AI Book - Verify Your Email Address

        Hello,

        Thank you for signing up for AI Book! Please verify your email address by visiting the link below:

        {verification_link}

        This link will expire in 24 hours for security reasons.

        If you didn't create an account, you can safely ignore this email.

        Best regards,
        The AI Book Team
        """

        # Send via the configured service
        if self.email_service == "resend":
            return await self._send_via_resend(
                to_email=to_email,
                subject="Verify Your AI Book Email Address",
                html_content=html,
                text_content=text_content
            )
        else:
            return await self._send_via_smtp(
                to_email=to_email,
                subject="Verify Your AI Book Email Address",
                html_content=html,
                text_content=text_content
            )

    async def send_password_reset_email(self, to_email: str, reset_token: str, frontend_url: str) -> bool:
        """
        Send password reset email.

        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            frontend_url: Frontend URL for reset link

        Returns:
            True if email was sent successfully, False otherwise
        """
        # Create reset link
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"

        # HTML content
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 5px;
                    border: 1px solid #ddd;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .button {{
                    display: inline-block;
                    background-color: #10a37f;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>AI Book</h1>
                    <h2>Password Reset Request</h2>
                </div>

                <p>Hello,</p>

                <p>We received a request to reset the password for your AI Book account.
                Click the button below to reset your password:</p>

                <p style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Password</a>
                </p>

                <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                <p>{reset_link}</p>

                <p>This link will expire in 1 hour for security reasons.</p>

                <p>If you didn't request this password reset, you can safely ignore this email.</p>

                <div class="footer">
                    <p>Best regards,<br>The AI Book Team</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        AI Book - Password Reset Request

        Hello,

        We received a request to reset the password for your AI Book account.
        Please visit this link to reset your password:

        {reset_link}

        This link will expire in 1 hour for security reasons.

        If you didn't request this password reset, you can safely ignore this email.

        Best regards,
        The AI Book Team
        """

        # Send via the configured service
        if self.email_service == "resend":
            return await self._send_via_resend(
                to_email=to_email,
                subject="Reset Your AI Book Password",
                html_content=html,
                text_content=text_content
            )
        else:
            return await self._send_via_smtp(
                to_email=to_email,
                subject="Reset Your AI Book Password",
                html_content=html,
                text_content=text_content
            )

    async def _send_via_resend(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str
    ) -> bool:
        """Send email via Resend API."""
        try:
            if not self.resend_api_key or not self.resend_api_key.startswith("re_"):
                logger.warning(f"Resend API key not configured or invalid (starts with: {self.resend_api_key[:10] if self.resend_api_key else 'None'}...)")
                return False

            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {self.resend_api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "from": formataddr((self.email_from_name, self.email_from)),
                "to": [to_email],
                "subject": subject,
                "html": html_content,
                "text": text_content
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

            logger.info(f"Email sent via Resend to {to_email}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to send email via Resend to {to_email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email via Resend to {to_email}: {e}")
            return False

    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str
    ) -> bool:
        """Send email via SMTP."""
        try:
            import aiosmtplib

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = formataddr((self.email_from_name, self.email_from))
            msg["To"] = to_email

            # Attach parts
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Send email using aiosmtplib
            await aiosmtplib.send_message(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=self.use_tls,
                username=self.smtp_user,
                password=self.smtp_password,
            )

            logger.info(f"Email sent via SMTP to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email via SMTP to {to_email}: {e}")
            return False

    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        if self.email_service == "resend":
            return bool(self.resend_api_key and self.resend_api_key.startswith("re_"))
        else:
            return all([
                self.smtp_host,
                self.smtp_user,
                self.smtp_password,
            ])


# Singleton instance
email_service = EmailService()
