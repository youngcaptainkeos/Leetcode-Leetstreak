"""Tests for coding-account ownership verification and challenge-response recovery (FEAT-04)."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock
import test_access as fixtures

from app.models import User


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.access = fixtures.AccessTests()
        self.access.setUp()
        self.client = self.access.client
        self.db = self.access.db

        self.user1 = self.db.query(User).filter(User.id == 1).first()
        self.user2 = self.db.query(User).filter(User.id == 2).first()
        self.user2.codeforces_username = "bob_cf"
        self.db.commit()

        self.headers_user1 = self.access.headers(1)
        self.headers_user2 = self.access.headers(2)

    def tearDown(self):
        self.access.tearDown()

    def test_unverified_by_default(self):
        resp = self.client.get(f"/api/users/{self.user1.id}/dashboard", headers=self.headers_user1)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data.get("leetcode_verified"))
        self.assertFalse(data.get("codeforces_verified"))

        # Status endpoint
        resp_status = self.client.get(f"/api/users/{self.user1.id}/verify-handle/status", headers=self.headers_user1)
        self.assertEqual(resp_status.status_code, 200)
        status_data = resp_status.json()
        self.assertFalse(status_data["leetcode"]["verified"])
        self.assertFalse(status_data["codeforces"]["verified"])
        self.assertFalse(status_data["leetcode"]["pending_token"])

    def test_initiate_requires_auth_and_self(self):
        # Anonymous
        resp = self.client.post(f"/api/users/{self.user1.id}/verify-handle/initiate", json={"platform": "leetcode"})
        self.assertEqual(resp.status_code, 401)

        # Cross account
        resp = self.client.post(f"/api/users/{self.user1.id}/verify-handle/initiate", json={"platform": "leetcode"}, headers=self.headers_user2)
        self.assertEqual(resp.status_code, 403)

    def test_initiate_and_confirm_leetcode_verification_success(self):
        resp = self.client.post(
            f"/api/users/{self.user1.id}/verify-handle/initiate",
            json={"platform": "leetcode"},
            headers=self.headers_user1,
        )
        self.assertEqual(resp.status_code, 200)
        init_data = resp.json()
        token = init_data["token"]
        self.assertTrue(token.startswith("codestreak-verify-"))
        self.assertIn(token, init_data["instructions"])

        # Mock successful profile check containing the token
        with patch("app.main.check_leetcode_profile_verification", new_callable=AsyncMock) as mock_check, \
             patch("app.main.poll_user", new_callable=AsyncMock) as mock_poll:
            mock_check.return_value = True

            confirm_resp = self.client.post(
                f"/api/users/{self.user1.id}/verify-handle/confirm",
                json={"platform": "leetcode"},
                headers=self.headers_user1,
            )
            self.assertEqual(confirm_resp.status_code, 200)
            self.assertEqual(confirm_resp.json()["status"], "verified")
            mock_check.assert_called_once_with(self.user1.leetcode_username, token)

        # Verify user state in DB and dashboard
        self.db.refresh(self.user1)
        self.assertIsNotNone(self.user1.leetcode_verified_at)
        self.assertIsNone(self.user1.leetcode_verification_token)

        dash = self.client.get(f"/api/users/{self.user1.id}/dashboard", headers=self.headers_user1).json()
        self.assertTrue(dash["leetcode_verified"])

    def test_confirm_leetcode_verification_missing_token_fails(self):
        self.client.post(
            f"/api/users/{self.user1.id}/verify-handle/initiate",
            json={"platform": "leetcode"},
            headers=self.headers_user1,
        )
        with patch("app.main.check_leetcode_profile_verification", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = False

            confirm_resp = self.client.post(
                f"/api/users/{self.user1.id}/verify-handle/confirm",
                json={"platform": "leetcode"},
                headers=self.headers_user1,
            )
            self.assertEqual(confirm_resp.status_code, 400)
            self.assertIn("not found on LeetCode profile", confirm_resp.json()["detail"])

        self.db.refresh(self.user1)
        self.assertIsNone(self.user1.leetcode_verified_at)

    def test_confirm_expired_token_fails(self):
        resp = self.client.post(
            f"/api/users/{self.user1.id}/verify-handle/initiate",
            json={"platform": "leetcode"},
            headers=self.headers_user1,
        )
        self.assertEqual(resp.status_code, 200)
        # Artificially expire the token
        self.user1.leetcode_verification_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
        self.db.commit()

        confirm_resp = self.client.post(
            f"/api/users/{self.user1.id}/verify-handle/confirm",
            json={"platform": "leetcode"},
            headers=self.headers_user1,
        )
        self.assertEqual(confirm_resp.status_code, 400)
        self.assertIn("expired", confirm_resp.json()["detail"].lower())

    def test_initiate_and_confirm_codeforces_verification(self):
        resp = self.client.post(
            f"/api/users/{self.user2.id}/verify-handle/initiate",
            json={"platform": "codeforces"},
            headers=self.headers_user2,
        )
        self.assertEqual(resp.status_code, 200)
        token = resp.json()["token"]

        with patch("app.main.check_codeforces_profile_verification", new_callable=AsyncMock) as mock_check, \
             patch("app.main.background_codeforces_sync", new_callable=AsyncMock):
            mock_check.return_value = True

            confirm_resp = self.client.post(
                f"/api/users/{self.user2.id}/verify-handle/confirm",
                json={"platform": "codeforces"},
                headers=self.headers_user2,
            )
            self.assertEqual(confirm_resp.status_code, 200)
            self.assertEqual(confirm_resp.json()["status"], "verified")
            mock_check.assert_called_once_with("bob_cf", token)

        self.db.refresh(self.user2)
        self.assertIsNotNone(self.user2.codeforces_verified_at)

    def test_claim_unverified_handle_recovery(self):
        # user2 has bob_cf (unverified)
        # user1 claims bob_cf by proving ownership
        init_resp = self.client.post(
            f"/api/users/{self.user1.id}/verify-handle/initiate",
            json={"platform": "codeforces", "handle": "bob_cf"},
            headers=self.headers_user1,
        )
        self.assertEqual(init_resp.status_code, 200)
        self.assertTrue(init_resp.json()["is_claim_recovery"])
        token = init_resp.json()["token"]

        with patch("app.main.check_codeforces_profile_verification", new_callable=AsyncMock) as mock_check, \
             patch("app.main.background_codeforces_sync", new_callable=AsyncMock):
            mock_check.return_value = True

            confirm_resp = self.client.post(
                f"/api/users/{self.user1.id}/verify-handle/confirm",
                json={"platform": "codeforces"},
                headers=self.headers_user1,
            )
            self.assertEqual(confirm_resp.status_code, 200)

        self.db.refresh(self.user1)
        self.db.refresh(self.user2)

        # User 1 is now the verified owner of bob_cf
        self.assertEqual(self.user1.codeforces_username, "bob_cf")
        self.assertIsNotNone(self.user1.codeforces_verified_at)

        # User 2 had their unverified claim detached
        self.assertIsNone(self.user2.codeforces_username)
        self.assertIsNone(self.user2.codeforces_verified_at)

    def test_cannot_claim_already_verified_handle(self):
        # Make user2 verified on bob_cf
        self.user2.codeforces_verified_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.db.commit()

        # User 1 attempts to claim it -> 409
        resp = self.client.post(
            f"/api/users/{self.user1.id}/verify-handle/initiate",
            json={"platform": "codeforces", "handle": "bob_cf"},
            headers=self.headers_user1,
        )
        self.assertEqual(resp.status_code, 409)
        self.assertIn("already claimed and verified", resp.json()["detail"])

    def test_handle_change_resets_verification(self):
        # User 2 is verified
        self.user2.codeforces_verified_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.db.commit()

        with patch("app.main.fetch_profile", new_callable=AsyncMock) as mock_profile, \
             patch("app.main.background_codeforces_sync", new_callable=AsyncMock):
            mock_profile.return_value = {"handle": "new_bob_cf"}
            update_resp = self.client.put(
                f"/api/users/{self.user2.id}/codeforces-username",
                json={"codeforces_username": "new_bob_cf"},
                headers=self.headers_user2,
            )
            self.assertEqual(update_resp.status_code, 200)

        self.db.refresh(self.user2)
        self.assertEqual(self.user2.codeforces_username, "new_bob_cf")
        self.assertIsNone(self.user2.codeforces_verified_at)


if __name__ == "__main__":
    unittest.main()
