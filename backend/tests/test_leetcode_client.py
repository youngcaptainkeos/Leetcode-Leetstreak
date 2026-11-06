"""Provider-only synthetic checks; never contact a real coding account."""
import json
import unittest
from unittest.mock import patch

import httpx

from app import leetcode_client


class ProviderIdentityTests(unittest.IsolatedAsyncioTestCase):
    async def test_test_prefixes_do_not_bypass_provider(self):
        client_type = httpx.AsyncClient
        for username in ("test_synthetic", "tester_synthetic"):
            calls = []

            def respond(request):
                calls.append(json.loads(request.content)["variables"]["username"])
                return httpx.Response(200, json={"data": {"matchedUser": None}})

            with self.subTest(username=username), patch.object(
                leetcode_client.httpx, "AsyncClient",
                side_effect=lambda **kwargs: client_type(
                    **kwargs, transport=httpx.MockTransport(respond)
                ),
            ):
                with self.assertRaises(leetcode_client.LeetCodeError):
                    await leetcode_client.fetch_leetcode_user_data(username)
                self.assertEqual(calls, [username])

    async def test_provider_values_are_used_for_prefixed_account(self):
        client_type = httpx.AsyncClient

        def respond(request):
            query = json.loads(request.content)["query"]
            data = {"matchedUser": {
                "username": "test_synthetic", "profile": {},
                "submitStatsGlobal": {"acSubmissionNum": [{"difficulty": "Easy", "count": 3}]},
                "userCalendar": {"streak": 2, "submissionCalendar": "{}"},
            }} if "userFullProfile" in query else {"recentAcSubmissionList": []}
            return httpx.Response(200, json={"data": data})

        with patch.object(leetcode_client.httpx, "AsyncClient", side_effect=lambda **kwargs:
                          client_type(**kwargs, transport=httpx.MockTransport(respond))):
            result = await leetcode_client.fetch_leetcode_user_data("test_synthetic")
        self.assertEqual(result["difficulty_counts"], {"Easy": 3, "Medium": 0, "Hard": 0})
        self.assertEqual(result["official_streak"], 2)
        self.assertTrue(result["recent_submissions_available"])

    async def test_recent_query_errors_are_not_reported_as_successful_empty_history(self):
        client_type = httpx.AsyncClient

        def respond(request):
            query = json.loads(request.content)["query"]
            data = {"data": {"matchedUser": {"username": "demo_lc", "profile": {}, "userCalendar": {}}}} if "userFullProfile" in query else {"errors": [{"message": "synthetic unavailable history"}]}
            return httpx.Response(200, json=data)

        with patch.object(leetcode_client.httpx, "AsyncClient", side_effect=lambda **kwargs:
                          client_type(**kwargs, transport=httpx.MockTransport(respond))):
            result = await leetcode_client.fetch_leetcode_user_data("demo_lc")
        self.assertFalse(result["recent_submissions_available"])
        self.assertEqual(result["recent_submissions"], [])

    async def test_missing_problem_metadata_is_not_medium_and_is_retried(self):
        client_type = httpx.AsyncClient
        responses = [None, {"difficulty": "Hard", "stats": json.dumps({"acRate": "nan"})}]

        def respond(request):
            return httpx.Response(200, json={"data": {"question": responses.pop(0)}})

        with patch.object(leetcode_client.httpx, "AsyncClient", side_effect=lambda **kwargs:
                          client_type(**kwargs, transport=httpx.MockTransport(respond))):
            first = await leetcode_client.fetch_problem_info("synthetic-retry-metadata")
            second = await leetcode_client.fetch_problem_info("synthetic-retry-metadata")
        self.assertIsNone(first["difficulty"])
        self.assertEqual(second["difficulty"], "Hard")
        self.assertIsNone(second["ac_rate"])
