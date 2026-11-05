"""Bounded email dispatch with truthful acceptance results and no personal-data logs."""
import asyncio
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
import logging
import os
import smtplib
from urllib.parse import urlsplit

import httpx

logger = logging.getLogger("codestreak.email")
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "").strip().strip("'\"")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "").strip()
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "notifications@codestreak.dev").strip()
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "auto").strip().lower()


@dataclass(frozen=True)
class DeliveryResult:
    status: str
    provider: str

    def __bool__(self):
        # Provider acceptance is not a promise of inbox delivery.
        return self.status == "accepted"


def _smtp_send(to_email: str, subject: str, html: str) -> bool:
    message = MIMEMultipart("alternative")
    message["Subject"], message["From"], message["To"] = subject, SENDER_EMAIL, to_email
    message.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        refused = server.sendmail(SMTP_EMAIL, [to_email], message.as_string())
    return not refused


async def send_email_dispatch(to_email: str, subject: str, html_content: str) -> DeliveryResult:
    configured = {
        "brevo": bool(BREVO_API_KEY), "sendgrid": bool(SENDGRID_API_KEY),
        "resend": bool(RESEND_API_KEY), "smtp": bool(SMTP_EMAIL and SMTP_PASSWORD),
    }
    provider = EMAIL_BACKEND
    if provider == "auto":
        provider = next((name for name, enabled in configured.items() if enabled), "none")
    if provider not in configured or not configured[provider]:
        logger.warning("Email transport unavailable; no message sent.")
        return DeliveryResult("unavailable", "configuration")
    if any("\r" in value or "\n" in value for value in (to_email, subject, SENDER_EMAIL)):
        return DeliveryResult("rejected", provider)
    try:
        if provider == "smtp":
            accepted = await asyncio.to_thread(_smtp_send, to_email, subject, html_content)
            return DeliveryResult("accepted" if accepted else "rejected", provider)
        if provider == "brevo":
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {"api-key": BREVO_API_KEY}
            payload = {"sender": {"name": "LeetStreak", "email": SENDER_EMAIL}, "to": [{"email": to_email}], "subject": subject, "htmlContent": html_content}
        elif provider == "sendgrid":
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {"Authorization": "Bearer " + SENDGRID_API_KEY}
            payload = {"personalizations": [{"to": [{"email": to_email}]}], "from": {"email": SENDER_EMAIL, "name": "LeetStreak"}, "subject": subject, "content": [{"type": "text/html", "value": html_content}]}
        else:
            url = "https://api.resend.com/emails"
            headers = {"Authorization": "Bearer " + RESEND_API_KEY}
            payload = {"from": "LeetStreak <" + SENDER_EMAIL + ">", "to": [to_email], "subject": subject, "html": html_content}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, headers=headers, json=payload)
        status = "accepted" if 200 <= response.status_code < 300 else "rejected" if response.status_code < 500 else "failed"
        # Do not log recipient, provider response text, OTP, headers, or body.
        logger.info("Email transport %s: %s (HTTP %d)", provider, status, response.status_code)
        return DeliveryResult(status, provider)
    except (httpx.TimeoutException, smtplib.SMTPServerDisconnected):
        # The provider may have accepted the request before the connection ended.
        logger.warning("Email transport %s: outcome unknown; no automatic resend.", provider)
        return DeliveryResult("unknown", provider)
    except Exception:
        logger.warning("Email transport %s: delivery attempt failed.", provider)
        return DeliveryResult("failed", provider)


def _message(username: str, title: str, body: str) -> str:
    return f'''<!doctype html><html><body style="background:#111318;color:#f1f5f9;font-family:Arial,sans-serif;padding:24px">
<div style="max-width:480px;margin:auto;background:#1d2028;border:1px solid #363b47;border-radius:16px;padding:24px">
<h2 style="color:#a78bfa;margin-top:0">LeetStreak</h2><h3>{escape(title)}</h3>
<p>Hello {escape(username)},</p>{body}<p style="color:#9ca3af;font-size:12px">LeetStreak</p></div></body></html>'''


async def send_otp_email(to_email: str, username: str, otp_code: str) -> DeliveryResult:
    body = f'<p>Your password reset code is:</p><p style="font-size:30px;letter-spacing:6px;color:#a78bfa">{escape(otp_code)}</p><p>It expires in 15 minutes. If you did not request this, ignore this message.</p>'
    return await send_email_dispatch(to_email, "LeetStreak password reset", _message(username, "Reset your password", body))


async def send_update_notification_email(to_email: str, username: str, commit_id: str, release_notes: str, download_url: str) -> DeliveryResult:
    url = urlsplit(download_url)
    if url.scheme != "https" or url.hostname != "codestreak-api.onrender.com" or url.path != "/downloads/leetstreak.zip" or url.username or url.password or url.port or url.query or url.fragment:
        return DeliveryResult("rejected", "configuration")
    body = f'<p>{escape(release_notes)}</p><p><a style="color:#a78bfa" href="{escape(download_url, quote=True)}">Download the extension</a></p><p>Replace the files in your existing unpacked extension folder, then reload it on your browser\'s extensions page. Unpacked installations do not update automatically.</p>'
    return await send_email_dispatch(to_email, "LeetStreak release update", _message(username, "A LeetStreak update is available", body))
