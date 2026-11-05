"""Tests for account-backed progress and custom study plans/playlists (FEAT-01)."""
import unittest
import test_access as fixtures

from app.models import User, UserProgress, UserCustomPlan


class ProgressPlansTests(unittest.TestCase):
    def setUp(self):
        self.access = fixtures.AccessTests()
        self.access.setUp()
        self.client = self.access.client
        self.db = self.access.db

    def tearDown(self):
        self.access.tearDown()

    def test_progress_routes_enforce_auth_and_ownership(self):
        # Anonymous requests are rejected
        res = self.client.get("/api/users/1/progress")
        self.assertEqual(res.status_code, 401)

        res = self.client.put("/api/users/1/progress", json={"followed": ["top-sql-50"]})
        self.assertEqual(res.status_code, 401)

        # Cross-user requests are forbidden
        headers_user1 = self.access.headers(1)
        res = self.client.get("/api/users/2/progress", headers=headers_user1)
        self.assertEqual(res.status_code, 403)

        res = self.client.put("/api/users/2/progress", json={"followed": ["top-sql-50"]}, headers=headers_user1)
        self.assertEqual(res.status_code, 403)

        res = self.client.post("/api/users/2/plans", json={
            "name": "User 2 Plan",
            "slug": "user-2-plan",
            "planSubGroups": [],
        }, headers=headers_user1)
        self.assertEqual(res.status_code, 403)

        res = self.client.delete("/api/users/2/plans/some-slug", headers=headers_user1)
        self.assertEqual(res.status_code, 403)

    def test_get_progress_initializes_empty_for_user(self):
        headers = self.access.headers(1)
        res = self.client.get("/api/users/1/progress", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["user_id"], 1)
        self.assertEqual(data["followed"], [])
        self.assertEqual(data["hidden"], [])
        self.assertEqual(data["manual"], [])
        self.assertEqual(data["custom_plans"], [])
        self.assertEqual(data["version"], 1)

    def test_update_progress_persists_and_increments_version(self):
        headers = self.access.headers(1)
        res = self.client.put("/api/users/1/progress", json={
            "followed": ["strivers-a2z", "top-sql-50"],
            "hidden": ["leetcode-75"],
            "manual": ["two-sum", "reverse-linked-list"],
        }, headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["followed"], ["strivers-a2z", "top-sql-50"])
        self.assertEqual(data["hidden"], ["leetcode-75"])
        self.assertEqual(data["manual"], ["two-sum", "reverse-linked-list"])
        self.assertGreater(data["version"], 1)

        # Fetch again to verify persistence
        res2 = self.client.get("/api/users/1/progress", headers=headers)
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(data2["followed"], ["strivers-a2z", "top-sql-50"])
        self.assertEqual(data2["manual"], ["two-sum", "reverse-linked-list"])

    def test_save_custom_plan_persists_and_auto_follows(self):
        headers = self.access.headers(1)
        plan_payload = {
            "name": "Custom Dynamic Programming",
            "slug": "custom-dp-sheet",
            "source": "external",
            "sourceUrl": "https://example.com/dp",
            "planSubGroups": [
                {
                    "name": "1D DP",
                    "questions": [
                        {
                            "title": "Climbing Stairs",
                            "titleSlug": "climbing-stairs",
                            "difficulty": "EASY",
                            "leetcodeSlug": "climbing-stairs",
                        },
                        {
                            "title": "House Robber",
                            "titleSlug": "house-robber",
                            "difficulty": "MEDIUM",
                            "leetcodeSlug": "house-robber",
                        },
                    ],
                }
            ],
        }
        res = self.client.post("/api/users/1/plans", json=plan_payload, headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["slug"], "custom-dp-sheet")
        self.assertEqual(data["name"], "Custom Dynamic Programming")

        # Check that get_progress returns this custom plan and adds it to followed
        prog_res = self.client.get("/api/users/1/progress", headers=headers)
        self.assertEqual(prog_res.status_code, 200)
        prog_data = prog_res.json()
        self.assertIn("custom-dp-sheet", prog_data["followed"])
        self.assertEqual(len(prog_data["custom_plans"]), 1)
        self.assertEqual(prog_data["custom_plans"][0]["slug"], "custom-dp-sheet")
        self.assertEqual(len(prog_data["custom_plans"][0]["planSubGroups"]), 1)

    def test_delete_custom_plan_removes_plan_and_unfollows(self):
        headers = self.access.headers(1)
        plan_payload = {
            "name": "Short Sheet",
            "slug": "short-sheet",
            "planSubGroups": [
                {
                    "name": "Part 1",
                    "questions": [
                        {"title": "Two Sum", "titleSlug": "two-sum", "difficulty": "EASY"},
                    ],
                }
            ],
        }
        self.client.post("/api/users/1/plans", json=plan_payload, headers=headers)

        # Delete it
        del_res = self.client.delete("/api/users/1/plans/short-sheet", headers=headers)
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["ok"])

        # Verify it is removed
        prog_res = self.client.get("/api/users/1/progress", headers=headers)
        prog_data = prog_res.json()
        self.assertNotIn("short-sheet", prog_data["followed"])
        self.assertEqual(len(prog_data["custom_plans"]), 0)

    def test_delete_starter_plan_hides_it_and_restore_unhides(self):
        headers = self.access.headers(1)
        # Follow strivers-a2z
        self.client.put("/api/users/1/progress", json={"followed": ["strivers-a2z"]}, headers=headers)

        # Remove starter plan
        del_res = self.client.delete("/api/users/1/plans/strivers-a2z", headers=headers)
        self.assertEqual(del_res.status_code, 200)

        prog_res = self.client.get("/api/users/1/progress", headers=headers)
        prog_data = prog_res.json()
        self.assertNotIn("strivers-a2z", prog_data["followed"])
        self.assertIn("strivers-a2z", prog_data["hidden"])

        # Restore starters
        restore_res = self.client.post("/api/users/1/plans/restore-starters", headers=headers)
        self.assertEqual(restore_res.status_code, 200)

        prog_res2 = self.client.get("/api/users/1/progress", headers=headers)
        self.assertNotIn("strivers-a2z", prog_res2.json()["hidden"])

    def test_custom_plans_bound_limit(self):
        headers = self.access.headers(1)
        # Plan with too many questions
        large_group = {
            "name": "Huge Group",
            "questions": [
                {"title": f"Question {i}", "titleSlug": f"q-{i}", "difficulty": "EASY"}
                for i in range(1001)
            ],
        }
        res = self.client.post("/api/users/1/plans", json={
            "name": "Too Big",
            "slug": "too-big",
            "planSubGroups": [large_group],
        }, headers=headers)
        self.assertEqual(res.status_code, 400)
