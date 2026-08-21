import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from urllib.parse import urlencode

from app.core.config import settings
from app.core.exceptions import EmailDeliveryError


def build_email_verification_url(
    raw_verification_token: str,
) -> str:
    query_string = urlencode({"token": raw_verification_token})

    return f"{settings.client_url.rstrip('/')}/verify-email?{query_string}"


def build_password_reset_url(
    raw_reset_token: str,
) -> str:
    query_string = urlencode({"token": raw_reset_token})

    return f"{settings.client_url.rstrip('/')}/reset-password?{query_string}"


def build_verification_email(
    recipient_email: str,
    recipient_name: str,
    raw_verification_token: str,
) -> EmailMessage:
    verification_url = build_email_verification_url(raw_verification_token)

    safe_recipient_name = escape(recipient_name)
    safe_verification_url = escape(
        verification_url,
        quote=True,
    )

    message = EmailMessage()

    message["Subject"] = "Verify your CareerSaathi AI email"
    message["From"] = formataddr(
        (
            settings.email_from_name,
            settings.email_from_address,
        )
    )
    message["To"] = recipient_email

    message.set_content(
        f"""Hello {recipient_name},

Welcome to CareerSaathi AI.

Please verify your email address by opening this link:

{verification_url}

This verification link expires in {
            settings.email_verification_token_expire_hours
        } hours and can only be used once.

If you did not create this account, you can ignore this email.

CareerSaathi AI
"""
    )

    message.add_alternative(
        f"""\
<!doctype html>
<html lang="en">
  <body style="font-family: Arial, sans-serif; color: #172033;">
    <div style="max-width: 600px; margin: 0 auto; padding: 32px;">
      <h1 style="color: #2563eb;">CareerSaathi AI</h1>

      <p>Hello {safe_recipient_name},</p>

      <p>
        Welcome to CareerSaathi AI. Please verify your
        email address to activate your account.
      </p>

      <p style="margin: 32px 0;">
        <a
          href="{safe_verification_url}"
          style="
            background: #2563eb;
            color: #ffffff;
            padding: 12px 20px;
            text-decoration: none;
            border-radius: 8px;
          "
        >
          Verify email address
        </a>
      </p>

      <p>
        This link expires in
        {settings.email_verification_token_expire_hours}
        hours and can only be used once.
      </p>

      <p>
        If you did not create this account, you can
        safely ignore this email.
      </p>
    </div>
  </body>
</html>
""",
        subtype="html",
    )

    return message


def build_password_reset_email(
    recipient_email: str,
    recipient_name: str,
    raw_reset_token: str,
) -> EmailMessage:
    reset_url = build_password_reset_url(raw_reset_token)

    safe_recipient_name = escape(recipient_name)
    safe_reset_url = escape(
        reset_url,
        quote=True,
    )

    message = EmailMessage()

    message["Subject"] = "Reset your CareerSaathi AI password"
    message["From"] = formataddr(
        (
            settings.email_from_name,
            settings.email_from_address,
        )
    )
    message["To"] = recipient_email

    message.set_content(
        f"""Hello {recipient_name},

We received a request to reset your CareerSaathi AI password.

Open this link to choose a new password:

{reset_url}

This password reset link expires in {
            settings.password_reset_token_expire_minutes
        } minutes and can only be used once.

If you did not request a password reset, you can safely ignore this email.
Your password has not been changed.

CareerSaathi AI
"""
    )

    message.add_alternative(
        f"""\
<!doctype html>
<html lang="en">
  <body style="font-family: Arial, sans-serif; color: #172033;">
    <div style="max-width: 600px; margin: 0 auto; padding: 32px;">
      <h1 style="color: #2563eb;">CareerSaathi AI</h1>

      <p>Hello {safe_recipient_name},</p>

      <p>
        We received a request to reset your
        CareerSaathi AI password.
      </p>

      <p style="margin: 32px 0;">
        <a
          href="{safe_reset_url}"
          style="
            background: #2563eb;
            color: #ffffff;
            padding: 12px 20px;
            text-decoration: none;
            border-radius: 8px;
          "
        >
          Reset password
        </a>
      </p>

      <p>
        This link expires in
        {settings.password_reset_token_expire_minutes}
        minutes and can only be used once.
      </p>

      <p>
        If you did not request a password reset,
        you can safely ignore this email. Your
        password has not been changed.
      </p>
    </div>
  </body>
</html>
""",
        subtype="html",
    )

    return message


def send_email_message(
    message: EmailMessage,
) -> None:
    if not settings.email_delivery_enabled:
        return

    if settings.smtp_username is None or settings.smtp_password is None:
        raise EmailDeliveryError

    smtp_username = settings.smtp_username.get_secret_value()
    smtp_password = settings.smtp_password.get_secret_value()

    if not smtp_username or not smtp_password:
        raise EmailDeliveryError

    tls_context = ssl.create_default_context()

    try:
        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=15,
        ) as smtp:
            smtp.ehlo()

            if settings.smtp_use_tls:
                smtp.starttls(context=tls_context)
                smtp.ehlo()

            smtp.login(
                smtp_username,
                smtp_password,
            )
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise EmailDeliveryError from exc


def send_verification_email(
    recipient_email: str,
    recipient_name: str,
    raw_verification_token: str,
) -> None:
    message = build_verification_email(
        recipient_email,
        recipient_name,
        raw_verification_token,
    )

    send_email_message(message)


def send_password_reset_email(
    recipient_email: str,
    recipient_name: str,
    raw_reset_token: str,
) -> None:
    message = build_password_reset_email(
        recipient_email,
        recipient_name,
        raw_reset_token,
    )

    send_email_message(message)
