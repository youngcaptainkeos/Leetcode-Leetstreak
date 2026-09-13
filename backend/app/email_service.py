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
      <div style="text-align: center; margin-bottom: 18px;">
        <img src="https://raw.githubusercontent.com/youngcaptainkeos/Leetcode-Leetstreak/main/extension/public/icon128.png" alt="LeetStreak" style="width: 44px; height: 44px; border-radius: 9px; vertical-align: middle; display: inline-block; margin-right: 10px;" />
        <span style="font-size: 20px; font-weight: 700; color: #6366f1; vertical-align: middle; display: inline-block;">LeetStreak Password Reset</span>
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
    
    if not release_notes or "ZeroTrac" in release_notes or "Sunday 12am" in release_notes:
        release_notes_html = """
        <ul style="margin: 8px 0 0 0; padding-left: 20px; color: #cbd5e1; font-size: 14px; line-height: 1.6;">
          <li style="margin-bottom: 6px;"><strong>ZeroTrac Elo Contest Ratings</strong>: Contest problems now use official Elo ratings for accurate problem point distribution.</li>
          <li style="margin-bottom: 6px;"><strong>Detailed Points Breakdown</strong>: Click any recent solve in your dashboard to view exact base points, contest ratings, acceptance deltas, and streak multipliers.</li>
          <li style="margin-bottom: 6px;"><strong>Sunday Midnight Resets</strong>: Weekly leaderboards now reset reliably every Sunday at 12:00 AM.</li>
          <li style="margin-bottom: 6px;"><strong>In-App Update Notifications</strong>: Automatic update banner in the extension popup when new versions are released.</li>
        </ul>
        """
    else:
        release_notes_html = f'<p style="margin: 8px 0 0 0; color: #cbd5e1; font-size: 14px; line-height: 1.6;">{release_notes}</p>'

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    </head>
    <body style="background-color: #0b0f19; margin: 0; padding: 32px 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f1f5f9;">
      <div style="max-width: 520px; margin: 0 auto; background-color: #111827; border: 1px solid #1e293b; border-radius: 12px; padding: 32px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);">
        
        <!-- Header Logo & Title -->
        <div style="margin-bottom: 24px; text-align: left;">
          <img src="https://raw.githubusercontent.com/youngcaptainkeos/Leetcode-Leetstreak/main/extension/public/icon128.png" alt="LeetStreak" style="width: 44px; height: 44px; border-radius: 8px; vertical-align: middle; margin-right: 12px;" />
          <span style="font-size: 20px; font-weight: 700; color: #f8fafc; letter-spacing: -0.3px; vertical-align: middle;">LeetStreak Update</span>
        </div>

        <!-- Greeting -->
        <p style="font-size: 15px; margin-top: 0; margin-bottom: 14px; color: #f8fafc;">Hi <strong>{username}</strong>,</p>
        
        <p style="font-size: 14px; line-height: 1.6; color: #94a3b8; margin-bottom: 24px;">
          A new update for the <strong>LeetStreak</strong> extension is now available. Here is a summary of what has been updated:
        </p>

        <!-- What's New Section -->
        <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; margin-bottom: 28px;">
          <h2 style="margin: 0 0 10px 0; font-size: 12px; font-weight: 700; color: #818cf8; text-transform: uppercase; letter-spacing: 0.8px;">What's New</h2>
          {release_notes_html}
        </div>

        <!-- Action Button -->
        <div style="text-align: center; margin-bottom: 28px;">
          <a href="{download_url}" target="_blank" style="display: inline-block; background-color: #4f46e5; color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 600; padding: 13px 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35);">
            Download Extension Package (leetstreak.zip)
          </a>
        </div>

        <!-- Installation Instructions Link -->
        <div style="border-top: 1px solid #1e293b; padding-top: 20px; font-size: 13px; color: #94a3b8; text-align: center;">
          <span style="display: block; margin-bottom: 6px; font-weight: 500;">Installation & Setup Guide</span>
          <a href="https://github.com/youngcaptainkeos/Leetcode-Leetstreak#readme" target="_blank" style="color: #818cf8; text-decoration: none; font-weight: 600;">
            View Setup Instructions (Chrome, Edge, Brave & Firefox) &rarr;
          </a>
        </div>

        <!-- Share with Friends Section -->
        <div style="border-top: 1px solid #1e293b; padding-top: 20px; margin-top: 20px; font-size: 13px; color: #94a3b8; text-align: center;">
          <span style="display: block; margin-bottom: 8px; font-weight: 600; color: #e2e8f0;">Know others grinding LeetCode?</span>
          <a href="https://api.whatsapp.com/send?text=Check%20out%20LeetStreak%20to%20track%20your%20LeetCode%20daily%20streak%20and%20compete%20on%20leaderboards%20with%20friends!%20Download%20link:%20https://codestreak-api.onrender.com/downloads/leetstreak.zip%20%7C%20Setup%20Guide:%20https://github.com/youngcaptainkeos/Leetcode-Leetstreak%23readme" target="_blank" style="display: inline-block; background-color: #1e293b; border: 1px solid #334155; color: #38bdf8; text-decoration: none; font-size: 12px; font-weight: 600; padding: 7px 16px; border-radius: 6px; margin-top: 4px;">
            💬 Share Download & Setup Link with Friends
          </a>
        </div>

        <!-- Footer -->
        <div style="margin-top: 28px; border-top: 1px solid #1e293b; padding-top: 16px; text-align: center; font-size: 12px; color: #64748b;">
          LeetStreak Team
        </div>
      </div>
    </body>
    </html>
    """
    logger.info("Initiating Update notification email to user: %s (Email: %s, Internal Commit: %s)", username, to_email, commit_id)
    return await send_email_dispatch(to_email, subject, html_content)
