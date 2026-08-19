import os
import logging
import socket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx

logger = logging.getLogger("codestreak.email")

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

async def send_otp_email(to_email: str, username: str, otp_code: str) -> bool:
    """
    Sends 6-digit OTP code to user's email address.
    Supports:
    1. Gmail / Custom SMTP (zero domain required) if SMTP_EMAIL and SMTP_PASSWORD are set.
    2. Resend API if RESEND_API_KEY is set.
    3. Terminal log fallback if no email service is configured.
    """
    subject = "LeetStreak - Password Reset Verification Code"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 20px; background: #151821; color: #e6e7eb; border-radius: 10px;">
      <h2 style="color: #6366f1; text-align: center;">🔥 LeetStreak Password Reset</h2>
      <p>Hello <strong>{username}</strong>,</p>
      <p>We received a request to reset your password. Use the 6-digit verification code below:</p>
      <div style="text-align: center; margin: 24px 0;">
        <span style="font-size: 32px; font-weight: 800; letter-spacing: 6px; background: #232734; color: #a5b4fc; padding: 12px 24px; border-radius: 8px; border: 1px solid #4338ca;">
          {otp_code}
        </span>
      </div>
      <p style="font-size: 13px; color: #9ca3af;">This code is valid for 15 minutes. If you did not request a password reset, you can safely ignore this email.</p>
    </div>
    """

    logger.info("Initiating OTP verification email to user: %s (Email: %s)", username, to_email)

    # 1. Try Gmail SMTP if credentials exist (Zero domain required, sends to anyone!)
    if SMTP_EMAIL and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            # Clean password by stripping spaces if present in Google App Password
            clean_pw = SMTP_PASSWORD.strip().replace(" ", "")
            clean_email = SMTP_EMAIL.strip()
            msg["From"] = f"LeetStreak <{clean_email}>"
            msg["To"] = to_email
            msg.attach(MIMEText(html_content, "html"))

            # Resolve IPv4 address for smtp.gmail.com to avoid IPv6 "Network is unreachable" on Render
            try:
                smtp_host = socket.gethostbyname("smtp.gmail.com")
            except Exception:
                smtp_host = "smtp.gmail.com"

            with smtplib.SMTP(smtp_host, 587, timeout=10) as server:
                server.ehlo("gmail.com")
                server.starttls()
                server.login(clean_email, clean_pw)
                server.sendmail(clean_email, to_email, msg.as_string())
            logger.info("OTP Email successfully sent via Gmail SMTP to %s", to_email)
            return True
        except Exception as e:
            logger.error("Failed to send OTP email via Gmail SMTP: %s", e)

    # 2. Try Resend API if API Key exists
    if RESEND_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {RESEND_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": "LeetStreak <onboarding@resend.dev>",
                        "to": [to_email],
                        "subject": subject,
                        "html": html_content,
                    },
                )
                if resp.status_code in [200, 201]:
                    logger.info("OTP Email successfully sent via Resend to %s", to_email)
                    return True
                elif resp.status_code == 403 and "testing emails" in resp.text:
                    logger.warning("Resend Free Testing Sandbox mode: Resend restricted sending to %s. OTP Code: %s", to_email, otp_code)
                    return True
                else:
                    logger.error("Resend API error (%s): %s", resp.status_code, resp.text)
        except Exception as e:
            logger.error("Failed to send OTP email via Resend: %s", e)

    # 3. Fallback: Log in server terminal
    logger.info("No active email sender. Verification OTP Code for %s (%s): %s", username, to_email, otp_code)
    return True
