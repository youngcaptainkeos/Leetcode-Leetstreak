"""Unit and integration tests for weekly and monthly period rankings (FEAT-06)."""
import os
import unittest
from datetime import datetime, timezone, timedelta
from app.timekeeping import period_bounds, ist_today, ist_date
import test_access as fixtures
from app.models import User, Solve, PointAward, Group, GroupMember
from app.database import engine
from app.migrations import run_all_migrations


class TestPeriodRankings(unittest.TestCase):
    def setUp(self):
        self.access = fixtures.AccessTests()
        self.access.setUp()
        run_all_migrations(engine)
        self.client = self.access.client
        self.db = self.access.db
        self.user1_id = 1
        self.user2_id = 2
        self.user3_id = 3

        # Configure users with baseline points
        u1 = self.db.query(User).filter(User.id == self.user1_id).one()
        u2 = self.db.query(User).filter(User.id == self.user2_id).one()
        u3 = self.db.query(User).filter(User.id == self.user3_id).one()

        u1.name = "Alice"
        u1.points = 100.0  # High lifetime baseline, e.g. from historical unlogged solves

        u2.name = "Bob"
        u2.points = 50.0

        u3.name = "Charlie"
        u3.points = 10.0
        self.db.commit()

    def tearDown(self):
        self.access.tearDown()

    def test_lifetime_leaderboard_uses_user_points(self):
        resp = self.client.get(
            "/api/leaderboard?period=all",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["period"], "all")
        self.assertIsNone(data["period_start"])
        self.assertIsNone(data["period_end"])
        entries = data["entries"]
        # Alice has 100, Bob 50, Charlie 10
        self.assertEqual(entries[0]["id"], self.user1_id)
        self.assertEqual(entries[0]["points"], 100)
        self.assertEqual(entries[1]["id"], self.user2_id)
        self.assertEqual(entries[1]["points"], 50)
        self.assertEqual(entries[2]["id"], self.user3_id)
        self.assertEqual(entries[2]["points"], 10)

    def test_week_and_month_period_rankings(self):
        week_start_dt, week_end_dt = period_bounds("week")
        month_start_dt, month_end_dt = period_bounds("month")

        # User 2 (Bob) solves a problem inside this week (15 pts)
        now_utc = week_start_dt + timedelta(hours=2)
        solve_b1 = Solve(
            user_id=self.user2_id,
            platform="leetcode",
            title_slug="two-sum",
            title="Two Sum",
            difficulty="Easy",
            solved_at=now_utc,
            first_solve_at=now_utc,
            points_earned=15.0,
        )
        self.db.add(solve_b1)
        self.db.flush()

        award_b1 = PointAward(
            award_key=f"u{self.user2_id}-two-sum-base",
            user_id=self.user2_id,
            solve_id=solve_b1.id,
            kind="base",
            points=15.0,
            earned_at=now_utc,
            scoring_version="leetcode-v2",
        )
        self.db.add(award_b1)

        # User 3 (Charlie) solves LC (10 pts) and CF (10 pts) inside this week
        solve_c1 = Solve(
            user_id=self.user3_id,
            platform="leetcode",
            title_slug="add-two-numbers",
            title="Add Two Numbers",
            difficulty="Medium",
            solved_at=now_utc,
            first_solve_at=now_utc,
            points_earned=10.0,
        )
        solve_c2 = Solve(
            user_id=self.user3_id,
            platform="codeforces",
            title_slug="cf-1-A",
            title="Theatre Square",
            difficulty="800",
            solved_at=now_utc,
            first_solve_at=now_utc,
            points_earned=10.0,
        )
        self.db.add_all([solve_c1, solve_c2])
        self.db.flush()

        award_c1 = PointAward(
            award_key=f"u{self.user3_id}-add-two-numbers-base",
            user_id=self.user3_id,
            solve_id=solve_c1.id,
            kind="base",
            points=10.0,
            earned_at=now_utc,
            scoring_version="leetcode-v2",
        )
        award_c2 = PointAward(
            award_key=f"u{self.user3_id}-cf-1-A-base",
            user_id=self.user3_id,
            solve_id=solve_c2.id,
            kind="base",
            points=10.0,
            earned_at=now_utc,
            scoring_version="codeforces-v1",
        )
        self.db.add_all([award_c1, award_c2])

        # User 1 (Alice) earns 0 points inside this week/month, but earned 30 points last month
        past_dt = month_start_dt - timedelta(days=5)
        solve_a_old = Solve(
            user_id=self.user1_id,
            platform="leetcode",
            title_slug="old-problem",
            title="Old Problem",
            difficulty="Hard",
            solved_at=past_dt,
            first_solve_at=past_dt,
            points_earned=30.0,
        )
        self.db.add(solve_a_old)
        self.db.flush()

        award_a_old = PointAward(
            award_key=f"u{self.user1_id}-old-problem-base",
            user_id=self.user1_id,
            solve_id=solve_a_old.id,
            kind="base",
            points=30.0,
            earned_at=past_dt,
            scoring_version="leetcode-v2",
        )
        self.db.add(award_a_old)
        self.db.commit()

        # Query Weekly Leaderboard
        resp_week = self.client.get(
            "/api/leaderboard?period=week",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp_week.status_code, 200)
        data_week = resp_week.json()
        self.assertEqual(data_week["period"], "week")
        self.assertEqual(data_week["period_start"], ist_date(week_start_dt).isoformat())
        self.assertEqual(data_week["period_end"], ist_date(week_end_dt - timedelta(seconds=1)).isoformat())

        entries_week = data_week["entries"]
        # In weekly points:
        # Charlie has 20 (10 LC + 10 CF) -> Rank 1
        # Bob has 15 -> Rank 2
        # Alice has 0 -> Rank 3 (despite 100 lifetime points!)
        self.assertEqual(entries_week[0]["id"], self.user3_id)
        self.assertEqual(entries_week[0]["points"], 20)
        self.assertEqual(entries_week[0]["codeforces_points"], 10.0)
        self.assertEqual(entries_week[0]["leetcode_points"], 10.0)

        self.assertEqual(entries_week[1]["id"], self.user2_id)
        self.assertEqual(entries_week[1]["points"], 15)

        self.assertEqual(entries_week[2]["id"], self.user1_id)
        self.assertEqual(entries_week[2]["points"], 0)

        # Query Monthly Leaderboard
        resp_month = self.client.get(
            "/api/leaderboard?period=month",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp_month.status_code, 200)
        data_month = resp_month.json()
        self.assertEqual(data_month["period"], "month")
        self.assertEqual(data_month["period_start"], ist_date(month_start_dt).isoformat())
        self.assertEqual(data_month["period_end"], ist_date(month_end_dt - timedelta(seconds=1)).isoformat())

        entries_month = data_month["entries"]
        # In monthly points:
        # Charlie has 20 -> Rank 1
        # Bob has 15 -> Rank 2
        # Alice has 0 (her award was last month) -> Rank 3
        self.assertEqual(entries_month[0]["id"], self.user3_id)
        self.assertEqual(entries_month[0]["points"], 20)
        self.assertEqual(entries_month[1]["id"], self.user2_id)
        self.assertEqual(entries_month[1]["points"], 15)
        self.assertEqual(entries_month[2]["id"], self.user1_id)
        self.assertEqual(entries_month[2]["points"], 0)

    def test_friends_and_group_leaderboard_period_parameter(self):
        week_start_dt, _ = period_bounds("week")
        now_utc = week_start_dt + timedelta(hours=1)

        # User 1 & 2 are in group 1
        solve = Solve(
            user_id=self.user2_id,
            platform="leetcode",
            title_slug="reverse-integer",
            title="Reverse Integer",
            difficulty="Medium",
            solved_at=now_utc,
            first_solve_at=now_utc,
            points_earned=25.0,
        )
        self.db.add(solve)
        self.db.flush()

        award = PointAward(
            award_key=f"u{self.user2_id}-reverse-integer-base",
            user_id=self.user2_id,
            solve_id=solve.id,
            kind="base",
            points=25.0,
            earned_at=now_utc,
            scoring_version="leetcode-v2",
        )
        self.db.add(award)
        self.db.commit()

        # Group leaderboard with period=week
        resp_grp = self.client.get(
            "/api/groups/1/leaderboard?period=week",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp_grp.status_code, 200)
        data_grp = resp_grp.json()
        self.assertEqual(data_grp["period"], "week")
        entries = data_grp["entries"]
        # Bob has 25, Alice has 0
        self.assertEqual(entries[0]["id"], self.user2_id)
        self.assertEqual(entries[0]["points"], 25)
        self.assertEqual(entries[1]["id"], self.user1_id)
        self.assertEqual(entries[1]["points"], 0)

        # Friends leaderboard with period=week
        resp_frnd = self.client.get(
            f"/api/friends/leaderboard?user_id={self.user1_id}&period=week",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp_frnd.status_code, 200)
        self.assertEqual(resp_frnd.json()["period"], "week")

    def test_deterministic_tie_breaking(self):
        # Two users with exact same points and streak
        u1 = self.db.query(User).filter(User.id == self.user1_id).one()
        u2 = self.db.query(User).filter(User.id == self.user2_id).one()
        u1.points = 50.0
        u2.points = 50.0
        self.db.commit()

        resp = self.client.get(
            "/api/leaderboard?period=all",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp.status_code, 200)
        entries = resp.json()["entries"]
        # Tie break by -user.id: user1 (id=1) comes before user2 (id=2)
        idx_u1 = next(i for i, e in enumerate(entries) if e["id"] == self.user1_id)
        idx_u2 = next(i for i, e in enumerate(entries) if e["id"] == self.user2_id)
        self.assertLess(idx_u1, idx_u2)

    def test_invalid_period_rejected(self):
        resp = self.client.get(
            "/api/leaderboard?period=yearly",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
