import unittest
from unittest.mock import AsyncMock, patch

import httpx
from app import email_service as mail
import test_access as fixtures
from app import main
from app.models import User


class EmailTests(unittest.IsolatedAsyncioTestCase):
    async def test_no_transport_is_not_success(self):
        with patch.multiple(mail, EMAIL_BACKEND="auto", BREVO_API_KEY="", SENDGRID_API_KEY="", RESEND_API_KEY="", SMTP_EMAIL="", SMTP_PASSWORD=""):
            result = await mail.send_otp_email("demo@example.com", "Demo", "123456")
        self.assertFalse(result)
        self.assertEqual(result.status, "unavailable")

    async def test_provider_acceptance_rejection_and_failure(self):
        for status, expected in [(201, "accepted"), (403, "rejected"), (500, "failed")]:
            def handler(request):
                return httpx.Response(status, json={"private": "must not appear in logs"})
            client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            with self.subTest(status=status), patch.multiple(mail, EMAIL_BACKEND="resend", RESEND_API_KEY="synthetic-only"), patch.object(mail.httpx, "AsyncClient", return_value=client), self.assertLogs("codestreak.email", level="INFO") as logs:
                result = await mail.send_otp_email("demo@example.com", "Demo", "123456")
            self.assertEqual(result.status, expected)
            self.assertEqual(bool(result), expected == "accepted")
            output = " ".join(logs.output)
            self.assertNotIn("demo@example.com", output)
            self.assertNotIn("123456", output)
            self.assertNotIn("private", output)

    async def test_timeout_does_not_fallback_or_report_success(self):
        def handler(request):
            raise httpx.ReadTimeout("fictional timeout", request=request)
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        with patch.multiple(mail, EMAIL_BACKEND="resend", RESEND_API_KEY="synthetic-only"), patch.object(mail.httpx, "AsyncClient", return_value=client):
            result = await mail.send_otp_email("demo@example.com", "Demo", "123456")
        self.assertEqual(result.status, "unknown")
        self.assertFalse(result)

    async def test_smtp_is_offloaded_and_false_result_is_rejected(self):
        for accepted in [True, False]:
            with patch.multiple(mail, EMAIL_BACKEND="smtp", SMTP_EMAIL="demo@example.com", SMTP_PASSWORD="synthetic-only"), patch.object(mail.asyncio, "to_thread", new=AsyncMock(return_value=accepted)) as thread:
                result = await mail.send_otp_email("demo@example.com", "Demo", "123456")
                self.assertEqual(bool(result), accepted)
                thread.assert_awaited_once()

    async def test_templates_escape_untrusted_values_and_restrict_links(self):
        dispatch = AsyncMock(return_value=mail.DeliveryResult("accepted", "synthetic"))
        with patch.object(mail, "send_email_dispatch", new=dispatch):
            await mail.send_otp_email("demo@example.com", "<img src=x>", "123456")
            html = dispatch.call_args.args[2]
            self.assertIn("&lt;img src=x&gt;", html)
            self.assertNotIn("<img src=x>", html)
            result = await mail.send_update_notification_email("demo@example.com", "Demo", "demo", "notes", "https://example.com/")
            self.assertFalse(result)
            dispatch.assert_awaited_once()


class DeliveryStateTests(unittest.IsolatedAsyncioTestCase):
    setUp = fixtures.AccessTests.setUp
    tearDown = fixtures.AccessTests.tearDown

    async def test_only_accepted_delivery_updates_release_state(self):
        for status in ["rejected", "failed", "unavailable", "unknown", "accepted"]:
            with self.subTest(status=status), patch.object(main, "send_update_notification_email", new=AsyncMock(return_value=mail.DeliveryResult(status, "synthetic"))):
                result = await main.send_and_update_user_commit(1, "demo@example.com", "Demo", "synthetic-release", "Synthetic notes", "https://codestreak-api.onrender.com/downloads/leetstreak.zip")
                self.assertEqual(bool(result), status == "accepted")
                self.db.expire_all()
                value = self.db.query(User).filter_by(id=1).one().last_notified_commit
                self.assertEqual(value, "synthetic-release" if status == "accepted" else "legacy")
