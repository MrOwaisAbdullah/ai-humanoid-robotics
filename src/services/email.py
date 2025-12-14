"""
Email service for sending password reset emails and other notifications.

This module handles email configuration and sending using SMTP.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from jinja2 import Template
import aiosmtplib
from email.utils import formataddr

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.email_from = os.getenv("EMAIL_FROM", self.smtp_user)
        self.email_from_name = os.getenv("EMAIL_FROM_NAME", "AI Book App")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    def _get_smtp_connection(self):
        """Create SMTP connection."""
        if self.use_tls:
            return smtplib.SMTP(self.smtp_host, self.smtp_port)
        else:
            return smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)

    def send_password_reset_email(self, to_email: str, reset_token: str, frontend_url: str) -> bool:
        """
        Send password reset email.

        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            frontend_url: Frontend URL for reset link

        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create reset link
            reset_link = f"{frontend_url}/reset-password?token={reset_token}"

            # Render email template
            subject = "Reset your AI Book password"

            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Reset your password</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    .container {
                        background-color: #f9f9f9;
                        padding: 30px;
                        border-radius: 5px;
                        border: 1px solid #ddd;
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 30px;
                    }
                    .button {
                        display: inline-block;
                        background-color: #007bff;
                        color: white;
                        padding: 12px 30px;
                        text-decoration: none;
                        border-radius: 5px;
                        margin: 20px 0;
                    }
                    .footer {
                        margin-top: 30px;
                        text-align: center;
                        font-size: 12px;
                        color: #666;
                    }
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
                        <a href="{{ reset_link }}" class="button">Reset Password</a>
                    </p>

                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p>{{ reset_link }}</p>

                    <p>This link will expire in 24 hours for security reasons.</p>

                    <p>If you didn't request this password reset, you can safely ignore this email.</p>

                    <div class="footer">
                        <p>Best regards,<br>The AI Book Team</p>
                        <p>This is an automated message. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_template = """
            AI Book - Password Reset Request

            Hello,

            We received a request to reset the password for your AI Book account.
            Please visit this link to reset your password:

            {reset_link}

            This link will expire in 24 hours for security reasons.

            If you didn't request this password reset, you can safely ignore this email.

            Best regards,
            The AI Book Team
            """

            # Render templates
            html_content = Template(html_template).render(reset_link=reset_link)
            text_content = text_template.format(reset_link=reset_link)

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = formataddr((self.email_from_name, self.email_from))
            msg["To"] = to_email

            # Attach HTML and text parts
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Send email
            with self._get_smtp_connection() as server:
                if self.use_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Password reset email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {e}")
            return False

    async def send_password_reset_email_async(self, to_email: str, reset_token: str, frontend_url: str) -> bool:
        """
        Send password reset email asynchronously.

        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            frontend_url: Frontend URL for reset link

        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create reset link
            reset_link = f"{frontend_url}/reset-password?token={reset_token}"

            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = formataddr((self.email_from_name, self.email_from))
            message["To"] = to_email
            message["Subject"] = "Reset your AI Book password"

            # HTML content
            html = f"""
            <html>
                <body>
                    <h2>Reset your AI Book password</h2>
                    <p>Hello,</p>
                    <p>We received a request to reset the password for your AI Book account.</p>
                    <p>Click <a href="{reset_link}">here</a> to reset your password.</p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you didn't request this reset, you can safely ignore this email.</p>
                </body>
            </html>
            """

            # Attach parts
            message.attach(MIMEText("Hello,\n\nWe received a request to reset your password. Visit: " + reset_link, "plain"))
            message.attach(MIMEText(html, "html"))

            # Send email using aiosmtplib
            await aiosmtplib.send_message(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=self.use_tls,
                username=self.smtp_user,
                password=self.smtp_password,
            )

            logger.info(f"Password reset email sent asynchronously to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {e}")
            return False

    def send_verification_email(self, to_email: str, verification_token: str, frontend_url: str) -> bool:
        """
        Send email verification email.

        Args:
            to_email: Recipient email address
            verification_token: Email verification token
            frontend_url: Frontend URL for verification link

        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create verification link
            verification_link = f"{frontend_url}/verify-email?token={verification_token}"

            # Create message
            msg = MIMEMultipart()
            msg["Subject"] = "Verify your AI Book email address"
            msg["From"] = formataddr((self.email_from_name, self.email_from))
            msg["To"] = to_email

            # HTML content
            html = f"""
            <html>
                <body>
                    <h2>Welcome to AI Book!</h2>
                    <p>Thank you for signing up. Please click the link below to verify your email address:</p>
                    <p><a href="{verification_link}">Verify Email</a></p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you didn't create an account, you can safely ignore this email.</p>
                </body>
            </html>
            """

            # Attach parts
            msg.attach(MIMEText(f"Welcome to AI Book! Please verify your email: {verification_link}", "plain"))
            msg.attach(MIMEText(html, "html"))

            # Send email
            with self._get_smtp_connection() as server:
                if self.use_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Verification email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send verification email to {to_email}: {e}")
            return False

    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return all([
            self.smtp_host,
            self.smtp_user,
            self.smtp_password,
            self.email_from
        ])


# Singleton instance
email_service = EmailService()