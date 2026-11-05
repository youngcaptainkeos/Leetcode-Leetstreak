"""Unit and integration tests for FEAT-08: History, Activity Views, and Exports."""
import os
import unittest
from datetime import datetime, date, timezone, timedelta
import test_access as fixtures
from app.models import User, Solve, PointAward, UserProgress, UserCustomPlan
from app.timekeeping import ist_today, ist_date
from app.database import engine
from app.migrations import run_all_migrations


class TestHistoryAndExports(unittest.TestCase):
    def setUp(self):
        self.access = fixtures.AccessTests()
        self.access.setUp()
        run_all_migrations(engine)
        self.client = self.access.client
        self.db = self.access.db
        self.user1_id = 1
        self.user2_id = 2

        # Configure user1 with account creation 10 days ago
        today = ist_today()
        u1 = self.db.query(User).filter(User.id == self.user1_id).one()
        u1.name = "Test Coder"
        u1.created_at = datetime.combine(today - timedelta(days=10), datetime.min.time())
        u1.leetcode_username = "coder_lc"
        u1.codeforces_username = "coder_cf"

        # Create multiple solves for user1
        solve1 = Solve(
            user_id=self.user1_id,
            platform="leetcode",
            title_slug="two-sum",
            title="Two Sum",
            difficulty="Easy",
            solved_at=datetime.combine(today - timedelta(days=5), datetime.min.time()) + timedelta(hours=14),
            points_earned=10.0,
            scoring_version="leetcode-v2",
        )
        solve2 = Solve(
            user_id=self.user1_id,
            platform="leetcode",
            title_slug="median-of-two-sorted-arrays",
            title="Median of Two Sorted Arrays",
            difficulty="Hard",
            solved_at=datetime.combine(today - timedelta(days=2), datetime.min.time()) + timedelta(hours=15),
            points_earned=40.0,
            scoring_version="leetcode-v2",
        )
        solve3 = Solve(
            user_id=self.user1_id,
            platform="codeforces",
            title_slug="cf-1000-A",
            title="Codeforces Problem A",
            difficulty="800",
            problem_rating=800.0,
            solved_at=datetime.combine(today - timedelta(days=1), datetime.min.time()) + timedelta(hours=16),
            points_earned=15.0,
            scoring_version="codeforces-v1",
        )
        # Solve with potentially dangerous title to test CSV formula injection
        solve4 = Solve(
            user_id=self.user1_id,
            platform="leetcode",
            title_slug="formula-injection-test",
            title="=SUM(A1:A10)",
            difficulty="Medium",
            solved_at=datetime.combine(today, datetime.min.time()) + timedelta(hours=10),
            points_earned=20.0,
            scoring_version="leetcode-v2",
        )
        self.db.add_all([solve1, solve2, solve3, solve4])
        self.db.flush()

        # Add point awards
        award1 = PointAward(
            award_key=f"u1-two-sum-base",
            user_id=self.user1_id,
            solve_id=solve1.id,
            kind="base",
            points=10.0,
            earned_at=solve1.solved_at,
            scoring_version="leetcode-v2",
        )
        award2 = PointAward(
            award_key=f"u1-median-base",
            user_id=self.user1_id,
            solve_id=solve2.id,
            kind="base",
            points=40.0,
            earned_at=solve2.solved_at,
            scoring_version="leetcode-v2",
        )
        self.db.add_all([award1, award2])

        # Add user progress and custom plans
        prog = UserProgress(
            user_id=self.user1_id,
            followed_plans=["strivers-a2z", "custom-blind-75"],
            hidden_plans=["top-sql-50"],
            manual_solves=["lc:two-sum", "lc:reverse-integer"],
            version=3,
        )
        custom_plan = UserCustomPlan(
            user_id=self.user1_id,
            slug="custom-blind-75",
            name="My Blind 75",
            source="external",
            source_url="https://example.com/plan",
            plan_json={
                "name": "My Blind 75",
                "slug": "custom-blind-75",
                "planSubGroups": [
                    {
                        "name": "Arrays",
                        "questions": [
                            {"title": "Two Sum", "titleSlug": "two-sum", "difficulty": "Easy", "paidOnly": False}
                        ]
                    }
                ],
                "source": "external",
            },
        )
        self.db.add_all([prog, custom_plan])
        self.db.commit()

    def tearDown(self):
        self.access.tearDown()

    def test_search_solves_with_filters_and_pagination(self):
        # 1. Search by title text query
        resp_q = self.client.get(
            f"/api/users/{self.user1_id}/solves/search?q=two",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp_q.status_code, 200)
        data_q = resp_q.json()
        self.assertEqual(data_q["total_count"], 2)
        slugs = [s["title_slug"] for s in data_q["solves"]]
        self.assertIn("two-sum", slugs)
        self.assertIn("median-of-two-sorted-arrays", slugs)

        # 2. Filter by platform
        resp_plat = self.client.get(
            f"/api/users/{self.user1_id}/solves/search?platform=codeforces",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp_plat.status_code, 200)
        data_plat = resp_plat.json()
        self.assertEqual(data_plat["total_count"], 1)
        self.assertEqual(data_plat["solves"][0]["platform"], "codeforces")
        self.assertEqual(data_plat["solves"][0]["title_slug"], "cf-1000-A")

        # 3. Filter by difficulty
        resp_diff = self.client.get(
            f"/api/users/{self.user1_id}/solves/search?difficulty=Hard",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp_diff.status_code, 200)
        data_diff = resp_diff.json()
        self.assertEqual(data_diff["total_count"], 1)
        self.assertEqual(data_diff["solves"][0]["difficulty"], "Hard")

        # 4. Filter by date range
        today = ist_today()
        start = (today - timedelta(days=3)).isoformat()
        end = today.isoformat()
        resp_date = self.client.get(
            f"/api/users/{self.user1_id}/solves/search?start_date={start}&end_date={end}",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp_date.status_code, 200)
        data_date = resp_date.json()
        # Days 2, 1, and today -> 3 solves
        self.assertEqual(data_date["total_count"], 3)

        # 5. Sorting by points_desc
        resp_sort = self.client.get(
            f"/api/users/{self.user1_id}/solves/search?sort_by=points_desc",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp_sort.status_code, 200)
        pts = [s["points_earned"] for s in resp_sort.json()["solves"]]
        self.assertEqual(pts, sorted(pts, reverse=True))

        # 6. Pagination
        resp_p1 = self.client.get(
            f"/api/users/{self.user1_id}/solves/search?page=1&page_size=2",
            headers=self.access.headers(self.user1_id),
        )
        resp_p2 = self.client.get(
            f"/api/users/{self.user1_id}/solves/search?page=2&page_size=2",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(len(resp_p1.json()["solves"]), 2)
        self.assertEqual(len(resp_p2.json()["solves"]), 2)
        p1_ids = {s["id"] for s in resp_p1.json()["solves"]}
        p2_ids = {s["id"] for s in resp_p2.json()["solves"]}
        # No duplicates or omissions across pages
        self.assertTrue(p1_ids.isdisjoint(p2_ids))

        # 7. Coverage metadata
        coverage = resp_p1.json()["coverage"]
        self.assertEqual(coverage["total_solves"], 4)
        self.assertEqual(coverage["leetcode_solves"], 3)
        self.assertEqual(coverage["codeforces_solves"], 1)
        self.assertIsNotNone(coverage["oldest_solve_at"])
        self.assertIsNotNone(coverage["newest_solve_at"])

    def test_activity_heatmap_distinguishes_unobserved_from_zero_and_active(self):
        resp = self.client.get(
            f"/api/users/{self.user1_id}/activity/heatmap?days=30",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_days"], 30)

        # User was created 10 days ago.
        # Days 11-30 ago must be "unobserved" (NOT confirmed zero!)
        # Days 0-10 ago without solves must be "zero".
        # Days with solves must be "active".
        statuses = {d["status"] for d in data["days"]}
        self.assertIn("active", statuses)
        self.assertIn("zero", statuses)
        self.assertIn("unobserved", statuses)

        self.assertGreater(data["active_days"], 0)
        self.assertGreater(data["zero_days"], 0)
        self.assertGreater(data["unobserved_days"], 0)
        self.assertEqual(data["active_days"] + data["zero_days"] + data["unobserved_days"], 30)

        # Inspect specific day 20 days ago: must be unobserved
        day_20_ago = (ist_today() - timedelta(days=20)).isoformat()
        item_20 = next(d for d in data["days"] if d["date"] == day_20_ago)
        self.assertEqual(item_20["status"], "unobserved")
        self.assertEqual(item_20["count"], 0)

        # Inspect day 4 days ago (no solves in test fixture, but within 10-day tracking): must be zero
        day_4_ago = (ist_today() - timedelta(days=4)).isoformat()
        item_4 = next(d for d in data["days"] if d["date"] == day_4_ago)
        self.assertEqual(item_4["status"], "zero")
        self.assertEqual(item_4["count"], 0)

    def test_export_data_authorization_fail_closed(self):
        # Cross-user export is forbidden (SEC-01 fail closed)
        resp = self.client.get(
            f"/api/users/{self.user1_id}/export?format=json",
            headers=self.access.headers(self.user2_id),
        )
        self.assertEqual(resp.status_code, 403)

        # Anonymous export is unauthorized
        resp_anon = self.client.get(f"/api/users/{self.user1_id}/export?format=json")
        self.assertEqual(resp_anon.status_code, 401)

    def test_export_json_payload_structure_and_privacy(self):
        resp = self.client.get(
            f"/api/users/{self.user1_id}/export?format=json",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["export_version"], "1.0")
        self.assertIn("exported_at", data)

        # User profile
        user_data = data["user"]
        self.assertEqual(user_data["id"], self.user1_id)
        self.assertEqual(user_data["name"], "Test Coder")
        self.assertNotIn("password_hash", user_data)
        self.assertNotIn("session_version", user_data)

        # Solves
        solves_data = data["solves"]
        self.assertEqual(len(solves_data), 4)

        # Progress and Custom Plans
        prog_data = data["progress"]
        self.assertEqual(prog_data["followed_plans"], ["strivers-a2z", "custom-blind-75"])
        self.assertEqual(prog_data["manual_solves"], ["lc:two-sum", "lc:reverse-integer"])

        custom_plans_data = data["custom_plans"]
        self.assertEqual(len(custom_plans_data), 1)
        self.assertEqual(custom_plans_data[0]["slug"], "custom-blind-75")

        # Point Awards
        awards_data = data["point_awards"]
        self.assertEqual(len(awards_data), 2)

    def test_export_csv_formula_injection_protection(self):
        resp = self.client.get(
            f"/api/users/{self.user1_id}/export?format=csv",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp.headers["content-type"])
        self.assertIn("attachment; filename=", resp.headers["content-disposition"])

        csv_text = resp.text
        lines = csv_text.strip().split("\r\n") if "\r\n" in csv_text else csv_text.strip().split("\n")
        header = lines[0].split(",")
        self.assertIn("problem_slug", header)
        self.assertIn("problem_title", header)

        # Verify formula injection is escaped with leading single quote: '=SUM(A1:A10)
        injection_line = next(l for l in lines if "formula-injection-test" in l)
        self.assertIn("'=SUM(A1:A10)", injection_line)

    def test_plans_export_and_import(self):
        # 1. Export plans
        resp_exp = self.client.get(
            f"/api/users/{self.user1_id}/plans/export",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp_exp.status_code, 200)
        exp_data = resp_exp.json()
        self.assertEqual(exp_data["user_id"], self.user1_id)
        self.assertIn("custom-blind-75", exp_data["followed_plans"])
        self.assertEqual(len(exp_data["custom_plans"]), 1)

        # 2. Cross user cannot export or import
        resp_cross = self.client.get(
            f"/api/users/{self.user1_id}/plans/export",
            headers=self.access.headers(self.user2_id),
        )
        self.assertEqual(resp_cross.status_code, 403)

        # 3. Dry-run import for user2
        new_plan = {
            "name": "NeetCode 150",
            "slug": "neetcode-150",
            "source": "external",
            "sourceUrl": "https://neetcode.io",
            "planSubGroups": [
                {
                    "name": "Sliding Window",
                    "questions": [
                        {"title": "Best Time to Buy and Sell Stock", "titleSlug": "best-time-to-buy-and-sell-stock", "difficulty": "Easy", "paidOnly": False}
                    ]
                }
            ]
        }
        import_payload = {
            "version": 1,
            "followed_plans": ["neetcode-150"],
            "manual_solves": ["lc:best-time-to-buy-and-sell-stock"],
            "custom_plans": [new_plan]
        }

        resp_dry = self.client.post(
            f"/api/users/{self.user2_id}/plans/import?dry_run=true&mode=merge",
            json=import_payload,
            headers=self.access.headers(self.user2_id),
        )
        self.assertEqual(resp_dry.status_code, 200)
        dry_data = resp_dry.json()
        self.assertTrue(dry_data["dry_run"])
        self.assertEqual(dry_data["plans_imported"], 1)

        # Verify nothing was committed in dry run
        cp_u2 = self.db.query(UserCustomPlan).filter(UserCustomPlan.user_id == self.user2_id).all()
        self.assertEqual(len(cp_u2), 0)

        # 4. Real merge import for user2
        resp_real = self.client.post(
            f"/api/users/{self.user2_id}/plans/import?dry_run=false&mode=merge",
            json=import_payload,
            headers=self.access.headers(self.user2_id),
        )
        self.assertEqual(resp_real.status_code, 200)
        self.assertFalse(resp_real.json()["dry_run"])

        cp_u2_after = self.db.query(UserCustomPlan).filter(UserCustomPlan.user_id == self.user2_id).all()
        self.assertEqual(len(cp_u2_after), 1)
        self.assertEqual(cp_u2_after[0].slug, "neetcode-150")

        prog_u2 = self.db.query(UserProgress).filter(UserProgress.user_id == self.user2_id).one()
        self.assertIn("neetcode-150", prog_u2.followed_plans)
        self.assertIn("lc:best-time-to-buy-and-sell-stock", prog_u2.manual_solves)


if __name__ == "__main__":
    unittest.main()
