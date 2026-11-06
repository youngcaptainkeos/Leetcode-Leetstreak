"""Restart safety with fictional data and disposable local databases only."""
import asyncio
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import Mock, patch

import test_access as fixtures  # Sets isolated config before importing the app.
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app import main, migrations, scheduler
from app.models import User


class StartupMigrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="leetstreak-startup-")
        self.engine = create_engine("sqlite:///" + self.directory.name + "/test.db")

    def tearDown(self):
        self.engine.dispose()
        self.directory.cleanup()

    def legacy_database(self):
        with self.engine.begin() as connection:
            connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR(80), leetcode_username VARCHAR(80), points FLOAT, global_leaderboard_enabled BOOLEAN)"))
            connection.execute(text("INSERT INTO users VALUES (1, 'Demo Coder', 'demo_coder', 42.5, FALSE)"))
            connection.execute(text("CREATE TABLE solves (id INTEGER PRIMARY KEY, user_id INTEGER, title_slug VARCHAR(200), solved_at TIMESTAMP, points_earned FLOAT, is_daily BOOLEAN)"))
            connection.execute(text("INSERT INTO solves VALUES (1, 1, 'synthetic-daily', '2026-01-01 00:00:00', 21.5, TRUE), (2, 1, 'image-overlap', '2026-01-02 00:00:00', 8, FALSE)"))
            connection.execute(text("CREATE TABLE daily_activity (id INTEGER PRIMARY KEY, user_id INTEGER, date DATE, problems_solved INTEGER)"))
            connection.execute(text("INSERT INTO daily_activity VALUES (1, 1, '2026-01-01', 8)"))

    def test_fresh_database_and_repeated_start_preserve_user_choices(self):
        migrations.run_migrations(self.engine)
        with Session(self.engine) as db:
            db.add(User(id=1, name="Demo", leetcode_username="demo", email="demo@example.com"))
            db.commit()
        with self.engine.begin() as connection:
            connection.execute(text("UPDATE users SET points=42.5, show_global_leaderboard=FALSE, session_version=3 WHERE id=1"))
        migrations.run_migrations(self.engine)
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text("SELECT points, show_global_leaderboard, session_version FROM users")).one(), (42.5, 0, 3))
            self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM schema_migrations")).scalar_one(), 6)

    def test_legacy_upgrade_preserves_scores_dates_activity_and_daily_flags(self):
        self.legacy_database()
        migrations.run_migrations(self.engine)
        migrations.run_migrations(self.engine)
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text("SELECT points, created_at, show_global_leaderboard FROM users")).one(), (42.5, None, 0))
            self.assertEqual(connection.execute(text("SELECT points_earned, is_daily FROM solves ORDER BY id")).all(), [(21.5, 1), (8, 0)])
            self.assertEqual(connection.execute(text("SELECT problems_solved FROM daily_activity")).scalar_one(), 8)
            self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM daily_challenges")).scalar_one(), 0)
            self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM point_awards")).scalar_one(), 0)
            self.assertEqual(connection.execute(text("SELECT first_solve_at, first_solve_verified FROM solves WHERE id=1")).one(), (None, 0))
        # Future registrations still get an application-supplied date on SQLite.
        with Session(self.engine) as db:
            user = User(name="Another Demo", leetcode_username="another_demo", email="another@example.com")
            db.add(user)
            db.commit()
            self.assertIsNotNone(user.created_at)

    def test_failed_upgrade_rolls_back_ddl_and_versions_and_can_retry(self):
        self.legacy_database()
        original = migrations.migrate_tracking

        def fail_after_tracking(connection):
            original(connection)
            raise RuntimeError("synthetic migration failure")

        with patch.object(migrations, "migrate_tracking", side_effect=fail_after_tracking):
            with self.assertRaisesRegex(RuntimeError, "synthetic migration failure"):
                migrations.run_migrations(self.engine)
        self.assertNotIn("schema_migrations", inspect(self.engine).get_table_names())
        self.assertNotIn("created_at", {c["name"] for c in inspect(self.engine).get_columns("users")})
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text("SELECT points FROM users")).scalar_one(), 42.5)
        migrations.run_migrations(self.engine)

    def test_failed_fresh_bootstrap_leaves_no_partial_tables(self):
        with patch.object(migrations, "migrate_tracking", side_effect=RuntimeError("synthetic failure")):
            with self.assertRaises(RuntimeError):
                migrations.run_migrations(self.engine)
        self.assertEqual(inspect(self.engine).get_table_names(), [])
        migrations.run_migrations(self.engine)

    def test_concurrent_fresh_starts_share_one_complete_sequence(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _: migrations.run_migrations(self.engine), range(4)))
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM schema_migrations")).scalar_one(), 6)

    def test_recorded_versions_do_not_hide_schema_drift(self):
        migrations.run_migrations(self.engine)
        with self.engine.begin() as connection:
            connection.execute(text("ALTER TABLE users DROP COLUMN leetcode_history_state"))
        with self.assertRaisesRegex(RuntimeError, "Incomplete schema for users"):
            migrations.run_migrations(self.engine)

    def test_importing_app_does_not_connect_or_create_a_database(self):
        filename = Path(self.directory.name) / "import-only.db"
        env = {**os.environ, "DATABASE_URL": "sqlite:///" + str(filename)}
        result = subprocess.run(
            [sys.executable, "-c", "from app.main import app"],
            cwd=Path(__file__).resolve().parents[1], env=env,
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(filename.exists())

    def test_startup_readiness_shutdown_and_restart_without_bulk_repairs(self):
        self.legacy_database()
        with patch.object(main, "engine", self.engine), patch.object(main, "start_scheduler", return_value=Mock()) as start:
            for _ in range(2):
                with TestClient(main.app) as client:
                    self.assertEqual(client.get("/api/ready").status_code, 200)
                    self.assertEqual(client.get("/api/health").status_code, 200)
                self.assertFalse(main.app.state.schema_ready)
            self.assertEqual(start.call_count, 2)
            self.assertEqual(start.return_value.shutdown.call_count, 2)
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text("SELECT points, created_at FROM users")).one(), (42.5, None))
            self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM daily_challenges")).scalar_one(), 0)

    def test_startup_failure_never_starts_scheduler_or_reports_ready(self):
        with patch.object(main, "run_migrations", side_effect=RuntimeError("synthetic failure")), patch.object(main, "start_scheduler") as start:
            with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
                with TestClient(main.app):
                    self.fail("Failed startup must not enter the serving context")
            start.assert_not_called()
        self.assertFalse(main.app.state.schema_ready)

    def test_readiness_distinguishes_liveness_and_hides_database_errors(self):
        # TestClient without a context deliberately does not run startup.
        client = TestClient(main.app)
        try:
            main.app.state.schema_ready = False
            self.assertEqual(client.get("/api/health").status_code, 200)
            self.assertEqual(client.get("/api/ready").status_code, 503)
            main.app.state.schema_ready = True
            with patch.object(main.engine, "connect", side_effect=OperationalError("synthetic-private-diagnostic", {}, Exception())):
                response = client.get("/api/ready")
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("synthetic-private-diagnostic", response.text)
        finally:
            main.app.state.schema_ready = False
            client.close()


class SchedulerStartupTests(unittest.IsolatedAsyncioTestCase):
    async def test_start_does_not_schedule_immediate_provider_work(self):
        from datetime import datetime, timezone
        before = datetime.now(timezone.utc)
        instance = scheduler.start_scheduler()
        try:
            jobs = {job.id: job for job in instance.get_jobs()}
            self.assertEqual(set(jobs), {"poll_all_users", "refresh_zerotrac_dataset"})
            self.assertGreaterEqual(jobs["poll_all_users"].next_run_time, before + timedelta(minutes=scheduler.POLL_INTERVAL_MINUTES))
            self.assertGreaterEqual(jobs["refresh_zerotrac_dataset"].next_run_time, before + timedelta(weeks=1))
        finally:
            instance.shutdown(wait=False)
            await asyncio.sleep(0)
