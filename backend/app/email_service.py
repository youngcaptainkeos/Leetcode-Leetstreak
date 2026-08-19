import os
import logging
import httpx

logger = logging.getLogger("codestreak.email")

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

async def send_otp_email(to_email: str, username: str, otp_code: str):
    """
    Sends 6-digit OTP code to user's email address via Resend API.
    If no API key is set, logs the OTP code clearly in the server terminal for local testing.
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

    # Log email sending status without exposing OTP code
    logger.info("Sending OTP verification email to user: %s (Email: %s)", username, to_email)

    if not RESEND_API_KEY:
        logger.info("No RESEND_API_KEY set. Logged OTP code to server terminal above.")
        return True

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
            else:
                logger.error("Resend API error (%s): %s", resp.status_code, resp.text)
                return False
    except Exception as e:
        logger.error("Failed to send OTP email via Resend: %s", e)
        return False
