"""Public submission parsing, with mocked Codeforces responses only."""
import unittest
from unittest.mock import AsyncMock, patch

from app.codeforces_client import fetch_accepted_history, CodeforcesError


def submission(number=100, timestamp=1760000000, **changes):
    row = {"id": number, "creationTimeSeconds": timestamp, "verdict": "OK", "testset": "TESTS",
           "author": {"members": [{"handle": "demo_cf"}]},
           "problem": {"contestId": 100, "index": "A", "name": "Synthetic problem", "rating": 1200}}
    return {**row, **changes}


class CodeforcesHistoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_repeats_preserve_individual_events_and_one_earliest_problem(self):
        rows = [submission(103, 1761300000), submission(102, 1760600000), submission()]
        with patch("app.codeforces_client.codeforces_request", new=AsyncMock(return_value=rows)):
            result = await fetch_accepted_history("demo_cf")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["submission_id"], 100)
        self.assertEqual([row["submission_id"] for row in result[0]["accepted_submissions"]], [100, 102, 103])

    async def test_only_individual_final_acceptances_for_the_requested_handle_count(self):
        rows = [submission(), submission(101, verdict="WRONG_ANSWER"), submission(102, verdict="TESTING"),
                submission(103, testset="PRETESTS"),
                submission(104, author={"members": [{"handle": "someone_else"}]}),
                submission(105, author={"members": [{"handle": "demo_cf"}], "ghost": True}),
                submission(106, author={"members": [{"handle": "demo_cf"}], "teamId": 9}),
                submission(107, author={"members": [{"handle": "demo_cf"}, {"handle": "another"}]})]
        with patch("app.codeforces_client.codeforces_request", new=AsyncMock(return_value=rows)):
            result = await fetch_accepted_history("demo_cf")
        self.assertEqual(result[0]["accepted_submissions"], [{"submission_id": 100, "timestamp": 1760000000}])

    async def test_overlapping_pages_are_deduplicated_and_preserve_every_repeat(self):
        first = [submission(number, 1760000000 + number) for number in range(2000, 1000, -1)]
        second = [submission(number, 1760000000 + number) for number in range(1100, 998, -1)]
        with patch("app.codeforces_client.codeforces_request", new=AsyncMock(side_effect=[first, second])) as request:
            result = await fetch_accepted_history("demo_cf")
        events = result[0]["accepted_submissions"]
        self.assertEqual(len(events), 1002)
        self.assertEqual(len({row["submission_id"] for row in events}), 1002)
        self.assertEqual(result[0]["submission_id"], 999)
        self.assertEqual(request.await_args_list[1].args[1]["from"], 901)

    async def test_changed_verdict_during_page_overlap_aborts_the_import(self):
        first = [submission(number) for number in range(2000, 1000, -1)]
        with patch("app.codeforces_client.codeforces_request", new=AsyncMock(side_effect=[first, [submission(1100, verdict="WRONG_ANSWER")]])):
            with self.assertRaises(CodeforcesError):
                await fetch_accepted_history("demo_cf")

    async def test_invalid_submission_list_or_identity_is_not_successful_empty_history(self):
        for rows in [None, {}, [submission(True)], [submission(timestamp="not-a-timestamp")],
                     [submission(author=None)], [submission(author={"members": None})], [submission(problem=None)]]:
            with self.subTest(rows=rows), patch("app.codeforces_client.codeforces_request", new=AsyncMock(return_value=rows)):
                with self.assertRaises(CodeforcesError):
                    await fetch_accepted_history("demo_cf")

    async def test_unrated_and_gym_questions_keep_identity_without_guessed_rating(self):
        rows = [submission(problem={"contestId": 100100, "index": "B2", "rating": float("nan")})]
        with patch("app.codeforces_client.codeforces_request", new=AsyncMock(return_value=rows)):
            result = await fetch_accepted_history("demo_cf")
        self.assertEqual(result[0]["slug"], "cf-100100-b2")
        self.assertIsNone(result[0]["rating"])
        self.assertIn("/gym/100100/problem/B2", result[0]["url"])

    async def test_incremental_window_stops_only_after_reading_the_boundary_page(self):
        rows = [submission(number, 1760000000 + number) for number in range(2000, 1000, -1)]
        with patch("app.codeforces_client.codeforces_request", new=AsyncMock(return_value=rows)) as request:
            result = await fetch_accepted_history("demo_cf", since=1760001500)
        self.assertEqual(len(result[0]["accepted_submissions"]), 1000)
        request.assert_awaited_once()
