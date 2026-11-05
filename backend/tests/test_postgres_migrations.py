"""Opt-in PostgreSQL checks. Only a dedicated local test database is allowed."""
import os
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker

from app.migrations import (
    migrate_auth,
    migrate_display_preference,
    migrate_tracking,
    migrate_core,
    migrate_platforms,
    run_all_migrations,
)


class LocalPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value = os.environ.get("LEETSTREAK_TEST_POSTGRES_URL")
        if not value:
            raise unittest.SkipTest("Dedicated local PostgreSQL URL not supplied")
        url = make_url(value)
        if url.host not in {"127.0.0.1", "localhost", "::1"} or not (url.database or "").startswith("leetstreak_test_"):
            raise RuntimeError("PostgreSQL verification requires a dedicated local test database")
        cls.root_engine = create_engine(url)

    @classmethod
    def tearDownClass(cls):
        cls.root_engine.dispose()


class PostgresMigrationTests(LocalPostgresTests):
    def setUp(self):
        self.schema = "migration_test_" + uuid.uuid4().hex
        with self.root_engine.begin() as connection:
            connection.execute(text(f"CREATE SCHEMA {self.schema}"))
        self.engine = create_engine(self.root_engine.url, connect_args={"options": f"-csearch_path={self.schema}"})
        with self.engine.begin() as connection:
            connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, password_hash VARCHAR(200), reset_otp VARCHAR(6), otp_expires_at TIMESTAMP, global_leaderboard_enabled BOOLEAN, points DOUBLE PRECISION)"))
            connection.execute(text("INSERT INTO users VALUES (1, 'synthetic-hash', '123456', NULL, FALSE, 17.5), (2, 'synthetic-hash', NULL, NULL, TRUE, 8), (3, 'synthetic-hash', NULL, NULL, NULL, 0)"))
            connection.execute(text("CREATE TABLE solves (id INTEGER PRIMARY KEY, user_id INTEGER, points_earned DOUBLE PRECISION)"))
            connection.execute(text("INSERT INTO solves VALUES (1, 1, 17.5)"))

    def tearDown(self):
        self.engine.dispose()
        with self.root_engine.begin() as connection:
            connection.execute(text(f"DROP SCHEMA {self.schema} CASCADE"))

    def test_additive_auth_preserves_accounts_and_awards(self):
        migrate_auth(self.engine)
        with self.engine.begin() as connection:
            rows = connection.execute(text("SELECT id, password_hash, reset_otp, session_version, points FROM users ORDER BY id")).all()
            self.assertEqual(rows[0], (1, "synthetic-hash", None, 0, 17.5))
            self.assertEqual(connection.execute(text("SELECT points_earned FROM solves")).scalar_one(), 17.5)
            connection.execute(text("UPDATE users SET session_version=4 WHERE id=1"))
        migrate_auth(self.engine)
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text("SELECT session_version FROM users WHERE id=1")).scalar_one(), 4)

    def test_display_preferences_migrate_once(self):
        migrate_display_preference(self.engine)
        with self.engine.begin() as connection:
            values = connection.execute(text("SELECT show_global_leaderboard FROM users ORDER BY id")).scalars().all()
            self.assertEqual(values, [False, True, True])
            connection.execute(text("UPDATE users SET show_global_leaderboard=TRUE WHERE id=1"))
        migrate_display_preference(self.engine)
        with self.engine.connect() as connection:
            self.assertIs(connection.execute(text("SELECT show_global_leaderboard FROM users WHERE id=1")).scalar_one(), True)

    def test_concurrent_migrations_share_one_registry_and_version(self):
        def migrate(_):
            migrate_auth(self.engine)
            migrate_display_preference(self.engine)
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(migrate, range(4)))
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM schema_migrations")).scalar_one(), 2)

    def test_failed_migration_rolls_back_and_can_retry(self):
        with self.engine.begin() as connection:
            connection.execute(text("ALTER TABLE users RENAME COLUMN reset_otp TO previous_reset_otp"))
        with self.assertRaises(DBAPIError):
            migrate_auth(self.engine)
        self.assertNotIn("session_version", {column["name"] for column in inspect(self.engine).get_columns("users")})
        self.assertNotIn("schema_migrations", inspect(self.engine).get_table_names())
        with self.engine.begin() as connection:
            connection.execute(text("ALTER TABLE users RENAME COLUMN previous_reset_otp TO reset_otp"))
        migrate_auth(self.engine)

    def test_tracking_storage_does_not_reconstruct_or_revalue_legacy_data(self):
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(lambda _: migrate_tracking(self.engine), range(3)))
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text("SELECT points_earned FROM solves")).scalar_one(), 17.5)
            self.assertEqual(connection.execute(text("SELECT points FROM users WHERE id=1")).scalar_one(), 17.5)
            row = connection.execute(text("SELECT first_solve_at, first_solve_verified, score_components_state FROM solves")).one()
            self.assertEqual(row, (None, False, "legacy"))
            self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM point_awards")).scalar_one(), 0)
            self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM accepted_submissions")).scalar_one(), 0)

    def test_run_all_migrations_concurrently_under_advisory_lock(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _: run_all_migrations(self.engine), range(4)))
        with self.engine.connect() as connection:
            version_count = connection.execute(text("SELECT COUNT(*) FROM schema_migrations")).scalar_one()
            self.assertEqual(version_count, 10)
            user_cols = {c["name"] for c in inspect(self.engine).get_columns("users")}
            self.assertIn("session_version", user_cols)
            self.assertIn("show_global_leaderboard", user_cols)
            self.assertIn("codeforces_username", user_cols)
            self.assertIn("leetcode_account_version", user_cols)
            self.assertIn("leetcode_verified_at", user_cols)
            self.assertIn("codeforces_verified_at", user_cols)
            solve_cols = {c["name"] for c in inspect(self.engine).get_columns("solves")}
            self.assertIn("platform", solve_cols)
            self.assertIn("first_solve_at", solve_cols)


class PostgresTrackingTests(LocalPostgresTests):
    def setUp(self):
        from app.database import Base
        from app.models import User
        self.schema = "tracking_test_" + uuid.uuid4().hex
        with self.root_engine.begin() as connection:
            connection.execute(text(f"CREATE SCHEMA {self.schema}"))
        self.engine = create_engine(self.root_engine.url, connect_args={"options": f"-csearch_path={self.schema}"})
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        with self.sessions.begin() as session:
            session.add(User(id=1, name="Demo Coder", email="coder@example.com", leetcode_username="demo_coder", points=17.5))

    def tearDown(self):
        self.engine.dispose()
        with self.root_engine.begin() as connection:
            connection.execute(text(f"DROP SCHEMA {self.schema} CASCADE"))

    def test_concurrent_acceptance_replay_creates_one_event(self):
        from app.tracking import record_acceptance
        from app.models import AcceptedSubmission
        from datetime import datetime
        def record(_):
            with self.sessions.begin() as session:
                return record_acceptance(session, 1, platform="leetcode", account_version=0,
                    submission_id="100", title_slug="synthetic-question", accepted_at=datetime(2026, 1, 1),
                    evidence_kind="public_recent").id
        with ThreadPoolExecutor(max_workers=4) as pool:
            ids = list(pool.map(record, range(4)))
        self.assertEqual(len(set(ids)), 1)
        with self.sessions() as session:
            self.assertEqual(session.query(AcceptedSubmission).count(), 1)

    def test_concurrent_baselines_preserve_one_original_snapshot(self):
        from app.tracking import capture_score_baseline
        from app.models import ScoreSnapshot
        def capture(_):
            with self.sessions.begin() as session:
                return capture_score_baseline(session, 1).id
        with ThreadPoolExecutor(max_workers=4) as pool:
            ids = list(pool.map(capture, range(4)))
        self.assertEqual(len(set(ids)), 1)
        with self.sessions() as session:
            self.assertEqual(session.query(ScoreSnapshot).one().payload["points"], 17.5)
