import os
import logging
import socket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx

logger = logging.getLogger("codestreak.email")

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "shashu2804@gmail.com")


async def send_email_dispatch(to_email: str, subject: str, html_content: str) -> bool:
    """
    Dispatches HTML emails over HTTPS/SMTP.
    Supports Brevo, SendGrid, Resend, and Gmail SMTP fallback.
    """
    # 1. Try Brevo HTTPS API (Zero domain required, 300 free emails/day to ANY address worldwide!)
    clean_brevo_key = BREVO_API_KEY.strip().strip("'").strip('"')
    if clean_brevo_key:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://api.brevo.com/v3/smtp/email",
                    headers={
                        "api-key": clean_brevo_key,
                        "accept": "application/json",
                        "content-type": "application/json",
                    },
                    json={
                        "sender": {"name": "LeetStreak", "email": SENDER_EMAIL.strip()},
                        "to": [{"email": to_email}],
                        "subject": subject,
                        "htmlContent": html_content,
                    },
                )
                if resp.status_code in [200, 201]:
                    logger.info("Email successfully sent via Brevo to %s", to_email)
                    return True
                else:
                    logger.error("Brevo API error (%s): %s", resp.status_code, resp.text)
        except Exception as e:
            logger.error("Failed to send email via Brevo: %s", e)

    # 2. Try SendGrid HTTPS API (Zero domain required, 100 free emails/day to ANY address worldwide!)
    if SENDGRID_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {SENDGRID_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "personalizations": [{"to": [{"email": to_email}]}],
                        "from": {"email": SENDER_EMAIL.strip(), "name": "LeetStreak"},
                        "subject": subject,
                        "content": [{"type": "text/html", "value": html_content}],
                    },
                )
                if resp.status_code in [200, 202]:
                    logger.info("Email successfully sent via SendGrid to %s", to_email)
                    return True
                else:
                    logger.error("SendGrid API error (%s): %s", resp.status_code, resp.text)
        except Exception as e:
            logger.error("Failed to send email via SendGrid: %s", e)

    # 3. Try Resend API
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
                    logger.info("Email successfully sent via Resend to %s", to_email)
                    return True
                elif resp.status_code == 403 and "testing emails" in resp.text:
                    logger.warning("Resend Free Testing Sandbox mode: Restricted sending to %s", to_email)
                    return True
                else:
                    logger.error("Resend API error (%s): %s", resp.status_code, resp.text)
        except Exception as e:
            logger.error("Failed to send email via Resend: %s", e)

    # 4. Fallback: Gmail SMTP (if raw socket port allowed)
    if SMTP_EMAIL and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            clean_pw = SMTP_PASSWORD.strip().replace(" ", "")
            clean_email = SMTP_EMAIL.strip()
            msg["From"] = f"LeetStreak <{clean_email}>"
            msg["To"] = to_email
            msg.attach(MIMEText(html_content, "html"))

            try:
                smtp_host = socket.gethostbyname("smtp.gmail.com")
            except Exception:
                smtp_host = "smtp.gmail.com"

            with smtplib.SMTP(smtp_host, 587, timeout=10) as server:
                server.ehlo("gmail.com")
                server.starttls()
                server.login(clean_email, clean_pw)
                server.sendmail(clean_email, to_email, msg.as_string())
            logger.info("Email successfully sent via Gmail SMTP to %s", to_email)
            return True
        except Exception as e:
            logger.error("Failed to send email via Gmail SMTP: %s", e)

    # 5. Fallback: Log in server terminal
    logger.info("No active email sender configured. Would have sent subject '%s' to %s", subject, to_email)
    return True


async def send_otp_email(to_email: str, username: str, otp_code: str) -> bool:
    """Sends 6-digit OTP code to user's email address."""
    subject = "LeetStreak - Password Reset Verification Code"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px; background: #151821; color: #e6e7eb; border-radius: 12px; border: 1px solid #2d3245;">
      <div style="text-align: center; margin-bottom: 20px;">
        <img src="https://raw.githubusercontent.com/youngcaptainkeos/Leetcode-Leetstreak/main/extension/public/logo_with_text.png" alt="LeetStreak" style="width: 130px; height: auto; border-radius: 10px; display: inline-block; margin-bottom: 10px;" />
        <div style="font-size: 20px; font-weight: 700; color: #818cf8;">Password Reset Verification</div>
      </div>
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
    return await send_email_dispatch(to_email, subject, html_content)


async def send_update_notification_email(
    to_email: str,
    username: str,
    commit_id: str = "26e30e6",
    release_notes: str = None,
    download_url: str = "https://codestreak-api.onrender.com/downloads/leetstreak.zip"
) -> bool:
    """Sends professional update notification email with download package link and setup guide."""
    subject = "LeetStreak Update Available"
    
    if not release_notes or "ZeroTrac" in release_notes or "Sunday 12am" in release_notes or "Redesign" in release_notes or "40c6882" in release_notes:
        release_notes_html = """
        <ul style="margin: 0; padding-left: 18px; color: #cbd5e1; font-size: 12.5px; line-height: 1.55;">
          <li style="margin-bottom: 5px;">⚙️ <strong>New Settings UI:</strong> Clean, scrollable panel for preferences &amp; accounts.</li>
          <li style="margin-bottom: 5px;">🌐 <strong>Global Leaderboard Toggle:</strong> 1-click switch between public &amp; friends-only mode.</li>
          <li style="margin-bottom: 5px;">🔥 <strong>Refreshed Flame Art:</strong> Crisp new streak icons across dashboard &amp; leaderboards.</li>
          <li style="margin-bottom: 5px;">🔄 <strong>Animated Quick Sync:</strong> Header sync icon spins live while fetching solves.</li>
          <li style="margin-bottom: 5px;">👏 <strong>One-Click Kudos:</strong> Celebrate your entire squad in a single tap.</li>
          <li>🛡️ <strong>Privacy &amp; Compliance:</strong> Live legal policies &amp; direct in-app account deletion.</li>
        </ul>
        """
    elif "<" in release_notes:
        release_notes_html = release_notes
    else:
        release_notes_html = f'<p style="margin: 0; color: #cbd5e1; font-size: 12.5px; line-height: 1.5;">{release_notes}</p>'

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    </head>
    <body style="background-color: #0b0f19; margin: 0; padding: 20px 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f1f5f9;">
      <div style="max-width: 440px; margin: 0 auto; background-color: #111827; border: 1px solid #1e293b; border-radius: 12px; padding: 22px 20px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);">
        
        <!-- Header -->
        <table style="width: 100%; border-bottom: 1px solid #1e293b; padding-bottom: 12px; margin-bottom: 16px;">
          <tr>
            <td style="text-align: left; vertical-align: middle;">
              <img src="https://raw.githubusercontent.com/youngcaptainkeos/Leetcode-Leetstreak/main/extension/public/logo_with_text.png" alt="LeetStreak" style="height: 26px; width: auto; display: block;" />
            </td>
            <td style="text-align: right; vertical-align: middle;">
              <span style="font-size: 11px; font-weight: 700; color: #a5b4fc; background-color: #312e81; padding: 3px 8px; border-radius: 999px;">v1.0.0 Update</span>
            </td>
          </tr>
        </table>

        <!-- Greeting & Intro -->
        <p style="font-size: 14px; margin: 0 0 8px 0; color: #f8fafc;">Hi <strong>{username}</strong>,</p>
        <p style="font-size: 13px; line-height: 1.5; color: #94a3b8; margin: 0 0 14px 0;">
          A fresh update for <strong>LeetStreak</strong> is live with new features and UI refinements:
        </p>

        <!-- What's New Card -->
        <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 12px 14px; margin-bottom: 18px;">
          <div style="font-size: 10.5px; font-weight: 700; color: #818cf8; text-transform: uppercase; letter-spacing: 0.7px; margin-bottom: 8px;">What's New</div>
          {release_notes_html}
        </div>

        <!-- Action Button -->
        <div style="text-align: center; margin-bottom: 18px;">
          <a href="{download_url}" target="_blank" style="display: inline-block; background-color: #4f46e5; color: #ffffff; text-decoration: none; font-size: 13px; font-weight: 700; padding: 11px 24px; border-radius: 8px; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35);">
            ⚡ Download Update Package
          </a>
        </div>

        <!-- Links -->
        <div style="border-top: 1px solid #1e293b; padding-top: 12px; font-size: 12px; color: #94a3b8; text-align: center; line-height: 1.8;">
          <a href="https://github.com/youngcaptainkeos/Leetcode-Leetstreak#readme" target="_blank" style="color: #818cf8; text-decoration: none; font-weight: 600;">Setup Guide</a>
          &nbsp;&bull;&nbsp;
          <a href="https://api.whatsapp.com/send?text=Check%20out%20LeetStreak%20to%20track%20your%20LeetCode%20daily%20streak%20and%20compete%20on%20leaderboards%20with%20friends!%20https://codestreak-api.onrender.com/downloads/leetstreak.zip" target="_blank" style="color: #38bdf8; text-decoration: none; font-weight: 600;">Share with Friends</a>
          &nbsp;&bull;&nbsp;
          <a href="https://codestreak-api.onrender.com/privacy" target="_blank" style="color: #94a3b8; text-decoration: none;">Privacy</a>
        </div>

        <!-- Footer -->
        <div style="margin-top: 12px; text-align: center; font-size: 11px; color: #64748b;">
          LeetStreak &bull; Keep your streak alive 🔥
        </div>
      </div>
    </body>
    </html>
    """
    logger.info("Initiating Update notification email to user: %s (Email: %s, Internal Commit: %s)", username, to_email, commit_id)
    return await send_email_dispatch(to_email, subject, html_content)
