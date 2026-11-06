"""Recheck identity state after a provider request returns."""
import asyncio
import unittest
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import test_access as fixtures
from app.models import User, Solve
from app.scheduler import poll_user
from app.timekeeping import utc_now


class IdentityRaceGuardTests(unittest.TestCase):
    setUp = fixtures.AccessTests.setUp
    tearDown = fixtures.AccessTests.tearDown
    headers = fixtures.AccessTests.headers

    def claim(self, platform):
        owner = self.db.get(User, 2)
        if platform == "codeforces":
            owner.codeforces_username = "demo_cf"
            self.db.commit()
        handle = getattr(owner, platform + "_username")
        response = self.client.post('/api/users/1/verify-handle/initiate',
                                    json={"platform": platform, "handle": handle}, headers=self.headers())
        self.assertEqual(response.status_code, 200)
        return owner, handle

    def test_confirm_does_not_displace_owner_verified_during_leetcode_request(self):
        self.assert_late_owner_rejected("leetcode")

    def test_confirm_does_not_displace_owner_verified_during_codeforces_request(self):
        self.assert_late_owner_rejected("codeforces")

    def assert_late_owner_rejected(self, platform):
        owner, handle = self.claim(platform)
        async def verify(*args):
            setattr(owner, platform + '_verified_at', utc_now())
            self.db.commit()
            return True
        with patch('app.main.check_' + platform + '_profile_verification', new=AsyncMock(side_effect=verify)):
            response = self.client.post('/api/users/1/verify-handle/confirm',
                                        json={"platform": platform}, headers=self.headers())
        self.assertEqual(response.status_code, 409)
        self.db.refresh(owner)
        self.assertEqual(getattr(owner, platform + '_username'), handle)
        self.assertIsNotNone(getattr(owner, platform + '_verified_at'))

    def test_changed_token_cannot_be_consumed_after_provider_wait(self):
        self.claim("leetcode")
        user = self.db.get(User, 1)
        async def verify(*args):
            user.leetcode_verification_token = 'synthetic-replacement-token'
            self.db.commit()
            return True
        with patch('app.main.check_leetcode_profile_verification', new=AsyncMock(side_effect=verify)):
            response = self.client.post('/api/users/1/verify-handle/confirm',
                                        json={"platform": "leetcode"}, headers=self.headers())
        self.assertEqual(response.status_code, 409)
        self.db.refresh(user)
        self.assertIsNone(user.leetcode_verified_at)

    def test_expiry_during_provider_wait_is_rejected(self):
        self.claim("codeforces")
        user = self.db.get(User, 1)
        async def verify(*args):
            user.codeforces_verification_expires_at = utc_now() - timedelta(seconds=1)
            self.db.commit()
            return True
        with patch('app.main.check_codeforces_profile_verification', new=AsyncMock(side_effect=verify)):
            response = self.client.post('/api/users/1/verify-handle/confirm',
                                        json={"platform": "codeforces"}, headers=self.headers())
        self.assertEqual(response.status_code, 409)

    def test_leetcode_response_for_replaced_account_is_discarded(self):
        user = self.db.get(User, 1)
        async def fetch(*args):
            user.leetcode_username = 'replacement_demo'
            user.leetcode_account_version += 1
            self.db.commit()
            return {"difficulty_counts": {"Easy": 50}, "recent_submissions": []}
        with patch('app.scheduler.fetch_leetcode_user_data', new=AsyncMock(side_effect=fetch)), \
             patch('app.scheduler.fetch_today_daily_challenge_slug', new=AsyncMock(return_value=None)):
            result = asyncio.run(poll_user(self.db, user, sync_codeforces=False))
        self.assertEqual(result, 0)
        self.assertEqual(user.easy_count, 0)
        self.assertEqual(self.db.query(Solve).count(), 0)
        self.assertIsNone(user.leetcode_last_sync)

    def test_replaced_account_generation_invalidates_in_flight_verification(self):
        self.claim("leetcode")
        user = self.db.get(User, 1)
        async def verify(*args):
            user.leetcode_account_version += 1
            self.db.commit()
            return True
        with patch('app.main.check_leetcode_profile_verification', new=AsyncMock(side_effect=verify)):
            response = self.client.post('/api/users/1/verify-handle/confirm',
                                        json={"platform": "leetcode"}, headers=self.headers())
        self.assertEqual(response.status_code, 409)
