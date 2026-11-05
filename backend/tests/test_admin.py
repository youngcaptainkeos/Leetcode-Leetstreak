import unittest
from unittest.mock import AsyncMock, patch

import test_access as fixtures
from app.main import app, verify_admin_secret
from app.models import User, AdminOperation


class AdminTests(unittest.TestCase):
    setUp = fixtures.AccessTests.setUp
    tearDown = fixtures.AccessTests.tearDown
    headers = fixtures.AccessTests.headers

    def admin_headers(self):
        return {"X-Admin-Secret": "synthetic-admin-key-" + "a" * 40}

    def test_every_admin_route_declares_the_guard(self):
        routes = [route for route in app.routes if route.path.startswith("/api/admin/")]
        self.assertGreaterEqual(len(routes), 5)
        for route in routes:
            with self.subTest(path=route.path):
                self.assertTrue(any(dependency.call is verify_admin_secret for dependency in route.dependant.dependencies))
        self.assertFalse(any(route.path == "/api/admin/test-update-email" for route in app.routes))

    def test_missing_blank_short_and_wrong_admin_credentials_fail_closed(self):
        cases = [
            ("", {}), ("", self.admin_headers()), ("short", {"X-Admin-Secret": "short"}),
            ("synthetic-admin-key-" + "a" * 40, {}),
            ("synthetic-admin-key-" + "a" * 40, {"X-Admin-Secret": "wrong"}),
        ]
        for secret, headers in cases:
            with self.subTest(configured=bool(secret), provided=bool(headers)), patch("app.main.ADMIN_SECRET", secret), patch("app.main.poll_all_users", new=AsyncMock()) as poll:
                self.assertEqual(self.client.post("/api/admin/poll-now", headers=headers).status_code, 403)
                self.assertEqual(self.client.post("/api/admin/reset-db", headers=headers).status_code, 403)
                self.assertEqual(self.client.get("/api/admin/debug-users", headers=headers).status_code, 403)
                poll.assert_not_awaited()
                self.assertEqual(self.db.query(User).count(), 3)

    def test_broadcast_is_reviewed_and_preview_is_default(self):
        with patch("app.main.ADMIN_SECRET", self.admin_headers()["X-Admin-Secret"]), patch("app.main.broadcast_release", new=AsyncMock()) as send:
            url = "/api/admin/broadcast-update-email"
            response = self.client.post(url, headers=self.admin_headers(), json={"release_id": "integration-2026-11-05"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "preview")
            send.assert_not_awaited()
            self.assertEqual(self.client.post(url, headers=self.admin_headers(), json={"release_id": "unknown"}).status_code, 400)
            self.assertEqual(self.client.post(url, headers=self.admin_headers(), json={"release_id": "integration-2026-11-05", "download_url": "https://example.com/"}).status_code, 422)

    def test_duplicate_broadcast_has_durable_guard(self):
        with patch("app.main.ADMIN_SECRET", self.admin_headers()["X-Admin-Secret"]), patch("app.main.broadcast_release", new=AsyncMock()) as send:
            url = "/api/admin/broadcast-update-email"
            body = {"release_id": "integration-2026-11-05", "dry_run": False}
            self.assertEqual(self.client.post(url, headers=self.admin_headers(), json=body).status_code, 200)
            self.assertEqual(self.client.post(url, headers=self.admin_headers(), json=body).status_code, 409)
            send.assert_awaited_once()
            self.assertEqual(self.db.query(AdminOperation).count(), 1)

    def test_all_user_sync_is_admin_only_and_rate_limited(self):
        with patch("app.main.ADMIN_SECRET", self.admin_headers()["X-Admin-Secret"]), patch("app.main.poll_all_users", new=AsyncMock(return_value={"synthetic": 1})) as poll:
            self.assertEqual(self.client.post("/api/admin/poll-now", headers=self.headers()).status_code, 403)
            response = self.client.post("/api/admin/poll-now", headers=self.admin_headers())
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["accounts_polled"], 1)
            self.assertEqual(self.client.post("/api/admin/poll-now", headers=self.admin_headers()).status_code, 429)
            poll.assert_awaited_once()
