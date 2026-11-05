import unittest
from datetime import datetime, timezone, date
import test_access as fixtures
from app.models import User, Solve, PlatformActivity
from app.point_calculator import recalculate_user_points


class TestUnlinkCodeforces(unittest.TestCase):
    def setUp(self):
        self.access = fixtures.AccessTests()
        self.access.setUp()
        self.client = self.access.client
        self.db = self.access.db
        self.user_id = 1

        # Seed user with both LeetCode and Codeforces data
        db = self.db
        user = db.query(User).filter(User.id == self.user_id).one()
        user.codeforces_username = "tourist_cf"
        user.codeforces_verified_at = datetime.now(timezone.utc).replace(tzinfo=None)
        user.codeforces_account_version = 1

        # Add a LeetCode solve
        lc_solve = Solve(
            user_id=self.user_id,
            platform="leetcode",
            title_slug="two-sum",
            title="Two Sum",
            difficulty="Easy",
            solved_at=datetime(2026, 11, 1, 10, 0, 0),
            first_solve_at=datetime(2026, 11, 1, 10, 0, 0),
            first_solve_verified=True,
            points_earned=8.0,
        )
        db.add(lc_solve)

        # Add a Codeforces solve
        cf_solve = Solve(
            user_id=self.user_id,
            platform="codeforces",
            title_slug="cf-1000-a",
            title="Problem A",
            problem_rating=1200.0,
            solved_at=datetime(2026, 11, 2, 10, 0, 0),
            first_solve_at=datetime(2026, 11, 2, 10, 0, 0),
            first_solve_verified=True,
            points_earned=12.8,
        )
        db.add(cf_solve)

        # Add Codeforces PlatformActivity
        cf_act = PlatformActivity(
            user_id=self.user_id,
            platform="codeforces",
            date=date(2026, 11, 2),
            problems_solved=1,
        )
        db.add(cf_act)

        recalculate_user_points(user, db)
        db.commit()

    def tearDown(self):
        self.access.tearDown()

    def test_unlink_unauthenticated_returns_401(self):
        resp = self.client.delete(f"/api/users/{self.user_id}/codeforces")
        self.assertEqual(resp.status_code, 401)

    def test_unlink_forbidden_returns_403(self):
        other_user_id = self.user_id + 999
        resp = self.client.delete(
            f"/api/users/{other_user_id}/codeforces",
            headers=self.access.headers(self.user_id),
        )
        self.assertEqual(resp.status_code, 403)

    def test_unlink_no_connected_account_returns_400(self):
        db = self.db
        user = db.query(User).filter(User.id == self.user_id).one()
        user.codeforces_username = None
        db.commit()

        resp = self.client.delete(
            f"/api/users/{self.user_id}/codeforces",
            headers=self.access.headers(self.user_id),
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("No Codeforces account", resp.json()["detail"])

    def test_unlink_success(self):
        db = self.db
        user_before = db.query(User).filter(User.id == self.user_id).one()
        version_before = user_before.codeforces_account_version
        points_before = user_before.points

        resp = self.client.delete(
            f"/api/users/{self.user_id}/codeforces",
            headers=self.access.headers(self.user_id),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "unlinked")
        self.assertIn("points", data)

        # Verify DB changes
        db.expire_all()
        user_after = db.query(User).filter(User.id == self.user_id).one()
        self.assertIsNone(user_after.codeforces_username)
        self.assertIsNone(user_after.codeforces_verified_at)
        self.assertEqual(user_after.codeforces_account_version, version_before + 1)

        # Codeforces solves and platform activity removed
        cf_solves = db.query(Solve).filter(Solve.user_id == self.user_id, Solve.platform == "codeforces").all()
        self.assertEqual(len(cf_solves), 0)

        cf_act = db.query(PlatformActivity).filter(PlatformActivity.user_id == self.user_id, PlatformActivity.platform == "codeforces").all()
        self.assertEqual(len(cf_act), 0)

        # LeetCode solves strictly preserved
        lc_solves = db.query(Solve).filter(Solve.user_id == self.user_id, Solve.platform == "leetcode").all()
        self.assertEqual(len(lc_solves), 1)

        # Points recomputed to reflect LeetCode only (lower than before)
        self.assertLess(user_after.points, points_before)
        self.assertAlmostEqual(user_after.points, 8.0, places=1)


if __name__ == "__main__":
    unittest.main()
