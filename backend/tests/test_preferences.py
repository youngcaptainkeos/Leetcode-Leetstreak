import tempfile
import unittest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from sqlalchemy import create_engine, text
import test_access as fixtures
from app.models import User, Solve
from app.migrations import migrate_display_preference
from app import main


class PreferenceTests(unittest.TestCase):
    setUp = fixtures.AccessTests.setUp
    tearDown = fixtures.AccessTests.tearDown
    headers = fixtures.AccessTests.headers

    def test_hiding_global_view_never_removes_participation(self):
        response = self.client.put("/api/users/1/settings", headers=self.headers(), json={"show_global_leaderboard": False})
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.json()["show_global_leaderboard"], False)
        board = self.client.get("/api/leaderboard?user_id=2", headers=self.headers(2))
        self.assertEqual(board.status_code, 200)
        self.assertEqual({row["id"] for row in board.json()["entries"]}, {1, 2, 3})
        own = self.client.get("/api/users/1/dashboard", headers=self.headers())
        self.assertIs(own.json()["show_global_leaderboard"], False)
        other = self.client.get("/api/users/1/dashboard", headers=self.headers(2))
        self.assertEqual(other.status_code, 200)
        self.assertNotIn("show_global_leaderboard", other.json())
        self.assertNotIn("global_leaderboard_enabled", other.json())
        self.assertNotIn("codeforces_sync_error", other.json())

    def test_legacy_alias_and_conflicting_choices(self):
        url = "/api/users/1/settings"
        self.assertEqual(self.client.put(url, headers=self.headers(), json={"global_leaderboard_enabled": False}).status_code, 200)
        self.assertEqual(self.client.put(url, headers=self.headers(), json={"show_global_leaderboard": True, "global_leaderboard_enabled": False}).status_code, 422)
        self.assertEqual(self.client.put(url, headers=self.headers(), json={}).status_code, 422)
        self.assertEqual(self.client.put(url, headers=self.headers(2), json={"show_global_leaderboard": True}).status_code, 403)

    def test_signup_persists_display_only_choice(self):
        body = {"name": "New Demo", "email": "new@example.com", "leetcode_username": "new_demo", "password": "a fictional passphrase", "show_global_leaderboard": False}
        with patch.object(main, "fetch_leetcode_user_data", new=AsyncMock(return_value={"username": "new_demo"})), patch.object(main, "poll_user", new=AsyncMock(return_value=0)):
            response = self.client.post("/api/users/register", json=body)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIs(response.json()["show_global_leaderboard"], False)
        board = self.client.get("/api/leaderboard", headers=self.headers())
        self.assertIn(response.json()["id"], {row["id"] for row in board.json()["entries"]})

    def test_hidden_view_user_remains_in_activity_and_solve_profiles(self):
        self.db.query(User).filter_by(id=1).update({User.show_global_leaderboard: False, User.global_leaderboard_enabled: False})
        self.db.add(Solve(user_id=1, title_slug="synthetic-question", title="Synthetic Question", difficulty="Easy", ac_rate=50, solved_at=datetime(2026, 1, 1), platform="leetcode"))
        self.db.commit()
        feed = self.client.get("/api/feed/recent-solves", headers=self.headers(2))
        self.assertEqual(feed.status_code, 200)
        self.assertEqual(feed.json()[0]["user_id"], 1)
        with patch.object(main, "fetch_today_daily_challenge_slug", new=AsyncMock(return_value=None)):
            solves = self.client.get("/api/users/1/recent-solves", headers=self.headers(2))
        self.assertEqual(solves.status_code, 200)
        self.assertEqual(solves.json()[0]["title_slug"], "synthetic-question")

    def test_existing_false_choice_migrates_once(self):
        with tempfile.TemporaryDirectory(prefix="leetstreak-preference-test-") as directory:
            engine = create_engine("sqlite:///" + directory + "/old.db")
            with engine.begin() as connection:
                connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, global_leaderboard_enabled BOOLEAN)"))
                connection.execute(text("INSERT INTO users VALUES (1, FALSE), (2, TRUE), (3, NULL)"))
            migrate_display_preference(engine)
            with engine.begin() as connection:
                self.assertEqual(connection.execute(text("SELECT show_global_leaderboard FROM users ORDER BY id")).scalars().all(), [0, 1, 1])
                connection.execute(text("UPDATE users SET show_global_leaderboard = TRUE WHERE id=1"))
            migrate_display_preference(engine)
            with engine.connect() as connection:
                self.assertEqual(connection.execute(text("SELECT show_global_leaderboard FROM users WHERE id=1")).scalar(), 1)
            engine.dispose()
