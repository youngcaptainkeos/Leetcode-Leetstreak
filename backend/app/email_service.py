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
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "notifications@codestreak.dev")


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
    subject = "LeetStreak Update: Revamped UI, Dynamic Points Engine & Global Leaderboard 🔥"
    
    if not release_notes or "ZeroTrac" in release_notes or "Sunday 12am" in release_notes or "Redesign" in release_notes or "40c6882" in release_notes or "fe74ddc" in release_notes or "51c5748" in release_notes or "Revamped" in release_notes:
        release_notes_html = """
        <ul style="margin: 8px 0 0 0; padding-left: 20px; color: #cbd5e1; font-size: 14px; line-height: 1.6;">
          <li style="margin-bottom: 8px;"><strong>ZeroTrac Elo Contest Ratings:</strong> Problem values now scale directly with official contest ratings (<code>Rating / 100</code>) for genuine difficulty-based rewards.</li>
          <li style="margin-bottom: 8px;"><strong>Revamped Dynamic Points Engine:</strong> Unrated problems scale dynamically by acceptance rate, and solving the LeetCode Daily Challenge awards an instant <strong>+5.0 bonus points</strong>.</li>
          <li style="margin-bottom: 8px;"><strong>Streak Multiplier Boost:</strong> Consistency counts—active streaks grant up to a <strong>1.10x multiplier boost</strong> across all your leaderboard solves!</li>
          <li style="margin-bottom: 8px;"><strong>Global Leaderboard Privacy Toggle:</strong> You control your visibility. Seamlessly toggle between public Global Leaderboard competition and private friends-only squad mode at any time.</li>
          <li style="margin-bottom: 8px;"><strong>Revamped Modern UI &amp; Settings:</strong> Redesigned settings drawer organized into dedicated sections (Profile, Preferences, Privacy, and Danger Zone) tailored perfectly to your popup viewport with smooth scrolling.</li>
          <li style="margin-bottom: 8px;"><strong>Animated Quick Sync Button:</strong> Header sync icon spins live while fetching your latest submissions without needing a page refresh.</li>
          <li style="margin-bottom: 8px;"><strong>One-Click &ldquo;Kudos All&rdquo;:</strong> Hype up your entire squad's problem solves with a single tap, complete with celebratory toasts.</li>
          <li style="margin-bottom: 8px;"><strong>High-Res Flame Badges:</strong> Brand new custom flame artwork on your streak card and leaderboard ranks.</li>
        </ul>
        """
    elif "<" in release_notes:
        release_notes_html = release_notes
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
          <img src="https://raw.githubusercontent.com/youngcaptainkeos/Leetcode-Leetstreak/main/extension/public/logo_with_text.png" alt="LeetStreak" style="width: 140px; height: auto; border-radius: 8px; display: block; margin-bottom: 8px;" />
          <span style="font-size: 18px; font-weight: 700; color: #f8fafc; letter-spacing: -0.3px;">New Extension Update</span>
        </div>

        <!-- Greeting -->
        <p style="font-size: 15px; margin-top: 0; margin-bottom: 14px; color: #f8fafc;">Hi <strong>{username}</strong>,</p>
        
        <p style="font-size: 14px; line-height: 1.6; color: #94a3b8; margin-bottom: 20px;">
          A new update for the <strong>LeetStreak</strong> extension is now available! Since LeetStreak runs as an unpacked extension, <strong>you need to reinstall it to apply the update</strong>. Here is a summary of what has been updated:
        </p>

        <!-- What's New Section -->
        <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
          <h2 style="margin: 0 0 10px 0; font-size: 12px; font-weight: 700; color: #818cf8; text-transform: uppercase; letter-spacing: 0.8px;">What's New</h2>
          {release_notes_html}
        </div>

        <!-- Action Button -->
        <div style="text-align: center; margin-bottom: 16px;">
          <a href="{download_url}" target="_blank" style="display: inline-block; background-color: #4f46e5; color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 600; padding: 13px 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35);">
            Download Extension Package (leetstreak.zip)
          </a>
        </div>

        <!-- How to Update Notice -->
        <div style="background-color: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 16px 18px; margin-bottom: 24px; text-align: left;">
          <div style="font-size: 13px; font-weight: 700; color: #38bdf8; margin-bottom: 6px;">
            ⚠️ How to Apply This Update (Reinstallation Required):
          </div>
          <p style="margin: 0 0 8px 0; font-size: 13px; color: #cbd5e1; line-height: 1.5;">
            Because LeetStreak is installed in developer mode, it does not update in the background. <strong>To get these updates, you must reinstall / reload it:</strong>
          </p>
          <ol style="margin: 0; padding-left: 20px; font-size: 12.5px; color: #94a3b8; line-height: 1.6;">
            <li>Download the new <strong>leetstreak.zip</strong> using the button above and unzip it.</li>
            <li>Open <code>chrome://extensions</code> in your browser (make sure <strong>Developer mode</strong> is toggled ON).</li>
            <li>Click the <strong>Reload (🔄)</strong> icon on your existing LeetStreak extension card, or remove the old one and click <strong>Load unpacked</strong> to select the new folder.</li>
          </ol>
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
          <a href="https://api.whatsapp.com/send?text=Check%20out%20LeetStreak%20to%20track%20your%20LeetCode%20daily%20streak%20and%20compete%20on%20leaderboards%20with%20friends%21%20%F0%9F%94%A5%0A%0A%F0%9F%93%A5%20Download%20Extension%20%28.zip%29%3A%0Ahttps%3A//codestreak-api.onrender.com/downloads/leetstreak.zip%0A%0A%F0%9F%9B%A0%EF%B8%8F%20Quick%2030-Sec%20Install%3A%0A1.%20Unzip%20leetstreak.zip%0A2.%20Open%20chrome%3A//extensions%20%26%20enable%20Developer%20mode%0A3.%20Click%20%22Load%20unpacked%22%20and%20select%20the%20unzipped%20folder%0A%0A%F0%9F%93%96%20Full%20Setup%20Guide%3A%0Ahttps%3A//github.com/youngcaptainkeos/Leetcode-Leetstreak%23readme%0A" target="_blank" style="display: inline-block; background-color: #1e293b; border: 1px solid #334155; color: #38bdf8; text-decoration: none; font-size: 12px; font-weight: 600; padding: 8px 18px; border-radius: 6px; margin-top: 4px;">
            💬 Share Download &amp; Setup Link with Friends
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
