"""Opt-in PostgreSQL checks. Only a dedicated local test database is allowed."""
import os
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker

from app.migrations import migrate_auth, migrate_display_preference, migrate_tracking


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

    def test_concurrent_full_acceptance_batches_link_one_question_and_one_first_proof(self):
        from app.tracking import ProviderAcceptance, ingest_acceptances
        from app.models import AcceptedSubmission, Solve, User
        from datetime import datetime
        with self.sessions.begin() as session:
            session.query(User).filter_by(id=1).update({User.codeforces_username: "demo_cf"})
            session.add(Solve(user_id=1, title_slug="cf-100-a", source_handle="demo_cf",
                platform="codeforces", solved_at=datetime(2026, 1, 1)))

        def ingest(_):
            with self.sessions.begin() as session:
                ingest_acceptances(session, 1, platform="codeforces", account_version=0,
                    expected_handle="demo_cf", complete_history=True, submissions=[
                        ProviderAcceptance("100", "cf-100-a", datetime(2026, 1, 1)),
                        ProviderAcceptance("101", "cf-100-a", datetime(2026, 1, 8))])

        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(ingest, range(4)))
        with self.sessions() as session:
            solve = session.query(Solve).one()
            self.assertEqual(solve.first_solve_at, datetime(2026, 1, 1))
            self.assertTrue(solve.first_solve_verified)
            self.assertEqual(session.query(AcceptedSubmission).count(), 2)
            self.assertEqual(session.query(AcceptedSubmission).filter_by(first_solve_verified=True).count(), 1)
            self.assertTrue(all(row.solve_id == solve.id for row in session.query(AcceptedSubmission)))

    def test_acceptance_batch_respects_caller_rollback(self):
        from app.tracking import ProviderAcceptance, ingest_acceptances
        from app.models import AcceptedSubmission
        from datetime import datetime
        with self.sessions() as session:
            ingest_acceptances(session, 1, platform="leetcode", account_version=0,
                expected_handle="demo_coder", submissions=[ProviderAcceptance("100", "synthetic-question", datetime(2026, 1, 1))])
            session.rollback()
        with self.sessions() as session:
            self.assertEqual(session.query(AcceptedSubmission).count(), 0)

    def test_concurrent_reconciliation_preserves_one_baseline_and_disjoint_credit(self):
        from app.models import AccountCredit, PointAward, ScoreSnapshot, Solve, User
        from app.reconciliation import reconcile_user
        from datetime import datetime
        with self.sessions.begin() as session:
            session.query(User).filter_by(id=1).update({User.easy_count: 1})
            session.add(Solve(user_id=1, platform="leetcode", source_handle="demo_coder",
                title_slug="synthetic-unknown", solved_at=datetime(2026, 1, 1), points_earned=10))

        def reconcile(_):
            with self.sessions.begin() as session:
                user = session.get(User, 1)
                return reconcile_user(user, session)

        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(list(pool.map(reconcile, range(4))), [10, 10, 10, 10])
        with self.sessions() as session:
            self.assertEqual(session.query(AccountCredit).one().points, 0)
            self.assertEqual(session.query(PointAward).one().points, 10)
            self.assertEqual(session.query(ScoreSnapshot).count(), 1)

    def test_concurrent_revision_reconciliation_awards_the_acceptance_once(self):
        from app.models import PointAward, Solve, User
        from app.reconciliation import reconcile_user
        from app.tracking import ProviderAcceptance, ingest_acceptances
        from datetime import datetime
        with self.sessions.begin() as session:
            user = session.get(User, 1)
            user.codeforces_username = "demo_cf"
            session.add(Solve(user_id=1, platform="codeforces", source_handle="demo_cf", title_slug="cf-100-a",
                              solved_at=datetime(2026, 1, 1), problem_rating=800))
            session.flush()
            ingest_acceptances(session, 1, platform="codeforces", account_version=0, expected_handle="demo_cf", complete_history=True,
                submissions=[ProviderAcceptance("100", "cf-100-a", datetime(2026, 1, 1)),
                             ProviderAcceptance("101", "cf-100-a", datetime(2026, 1, 8))])
            reconcile_user(user, session)

        def reconcile(_):
            with self.sessions.begin() as session:
                return reconcile_user(session.get(User, 1), session, revision_windows={"codeforces": datetime(2026, 1, 2)})

        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(list(pool.map(reconcile, range(4))), [10.0267] * 4)
        with self.sessions() as session:
            self.assertEqual(session.query(PointAward).filter_by(kind="revision").count(), 1)
            self.assertEqual(session.query(Solve).count(), 1)


class PostgresStartupTests(LocalPostgresTests):
    def setUp(self):
        self.schema = "startup_test_" + uuid.uuid4().hex
        with self.root_engine.begin() as connection:
            connection.execute(text(f"CREATE SCHEMA {self.schema}"))
        self.engine = create_engine(self.root_engine.url, connect_args={"options": f"-csearch_path={self.schema}"})

    def tearDown(self):
        self.engine.dispose()
        with self.root_engine.begin() as connection:
            connection.execute(text(f"DROP SCHEMA {self.schema} CASCADE"))

    def legacy_database(self):
        from test_migrations import StartupMigrationTests
        StartupMigrationTests.legacy_database(self)

    def test_legacy_upgrade_preserves_awards_and_unknown_registration_dates(self):
        from app.migrations import run_migrations
        self.legacy_database()
        with self.engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD CONSTRAINT users_leetcode_username_key UNIQUE (leetcode_username)"))
            connection.execute(text("CREATE UNIQUE INDEX ix_users_leetcode_username ON users (leetcode_username)"))
        run_migrations(self.engine)
        run_migrations(self.engine)
        with self.engine.begin() as connection:
            self.assertEqual(connection.execute(text("SELECT points, created_at, show_global_leaderboard FROM users")).one(), (42.5, None, False))
            self.assertEqual(connection.execute(text("SELECT points_earned, is_daily FROM solves ORDER BY id")).all(), [(21.5, True), (8, False)])
            self.assertEqual(connection.execute(text("SELECT problems_solved FROM daily_activity")).scalar_one(), 8)
            self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM point_awards")).scalar_one(), 0)
            # The new default must date future rows without backdating legacy ones.
            connection.execute(text("INSERT INTO users (id, name, leetcode_username) VALUES (2, 'Another Demo', 'demo_coder')"))
            self.assertIsNotNone(connection.execute(text("SELECT created_at FROM users WHERE id=2")).scalar_one())

    def test_full_sequence_rollback_after_late_failure_and_retry(self):
        from unittest.mock import patch
        from app import migrations
        self.legacy_database()
        original = migrations.migrate_tracking

        def fail_after_tracking(connection):
            original(connection)
            raise RuntimeError("synthetic migration failure")

        with patch.object(migrations, "migrate_tracking", side_effect=fail_after_tracking):
            with self.assertRaisesRegex(RuntimeError, "synthetic migration failure"):
                migrations.run_migrations(self.engine)
        self.assertNotIn("schema_migrations", inspect(self.engine).get_table_names())
        self.assertNotIn("created_at", {column["name"] for column in inspect(self.engine).get_columns("users")})
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text("SELECT points FROM users")).scalar_one(), 42.5)
        migrations.run_migrations(self.engine)

    def test_concurrent_full_sequence_from_separate_processes(self):
        import subprocess
        import sys
        from pathlib import Path
        # Each subprocess owns a different pool/connection; only the database
        # advisory lock can serialize their first bootstrap/version creation.
        script = """
import os
from sqlalchemy import create_engine
from app.migrations import run_migrations
engine = create_engine(os.environ['LEETSTREAK_TEST_POSTGRES_URL'],
    connect_args={'options': '-csearch_path=' + os.environ['LEETSTREAK_TEST_SCHEMA']})
try:
    run_migrations(engine)
finally:
    engine.dispose()
"""
        env = {**os.environ, "LEETSTREAK_TEST_SCHEMA": self.schema,
               "JWT_SECRET": "synthetic-process-test-key-" + "x" * 40}
        backend = Path(__file__).resolve().parents[1]
        processes = [subprocess.Popen([sys.executable, "-c", script], cwd=backend, env=env,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                     for _ in range(3)]
        try:
            for process in processes:
                stdout, stderr = process.communicate(timeout=30)
                self.assertEqual(process.returncode, 0, stderr)
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill()
                    process.communicate()
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM schema_migrations")).scalar_one(), 9)

    def test_previously_applied_auth_step_is_retained(self):
        from app.database import Base
        from app.migrations import run_migrations
        from app.models import User
        Base.metadata.create_all(self.engine)
        migrate_auth(self.engine)
        with sessionmaker(bind=self.engine).begin() as session:
            session.add(User(id=1, name="Demo", leetcode_username="demo", email="demo@example.com", session_version=7))
        run_migrations(self.engine)
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text("SELECT session_version FROM users")).scalar_one(), 7)
            self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM schema_migrations")).scalar_one(), 9)

    def test_new_credit_and_calendar_tables_default_to_private_data_api_access(self):
        from app.migrations import run_migrations
        run_migrations(self.engine)
        with self.engine.connect() as connection:
            flags = connection.execute(text("SELECT c.relname, c.relrowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=:schema AND c.relname IN ('account_credits','provider_calendar')"), {"schema": self.schema}).all()
            self.assertEqual(dict(flags), {"account_credits": True, "provider_calendar": True})
            self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM pg_policies WHERE schemaname=:schema AND tablename IN ('account_credits','provider_calendar')"), {"schema": self.schema}).scalar_one(), 0)
