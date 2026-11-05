"""Tests for versioned, atomic schema migrations and safe startup/shutdown."""
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text

from app.main import app
from app.migrations import (
    migrate_auth,
    migrate_core,
    migrate_display_preference,
    migrate_platforms,
    migrate_tracking,
    migration_connection,
    run_all_migrations,
    versions,
)


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db")
        self.engine = create_engine(f"sqlite:///{self.temp_file.name}")

    def tearDown(self):
        self.engine.dispose()
        self.temp_file.close()

    def test_run_all_migrations_fresh_database(self):
        run_all_migrations(self.engine)
        with self.engine.connect() as conn:
            tables = set(inspect(conn).get_table_names())
            expected_tables = {
                "schema_migrations",
                "users",
                "solves",
                "daily_activity",
                "platform_activity",
                "groups",
                "group_members",
                "kudos",
                "daily_challenges",
                "admin_operations",
                "accepted_submissions",
                "point_awards",
                "score_snapshots",
                "user_progress",
                "user_custom_plans",
                "friendships",
            }
            self.assertTrue(expected_tables.issubset(tables))

            recorded_versions = {
                row[0]
                for row in conn.execute(text("SELECT version FROM schema_migrations"))
            }
            expected_versions = {
                "20261105-core-v1",
                "20261105-platforms-v1",
                "20261105-auth-v1",
                "20261105-global-display-v1",
                "20261105-tracking-v1",
                "20261106-progress-v1",
                "20261106-verification-v1",
                "20261106-friendships-v1",
            }
            self.assertEqual(recorded_versions, expected_versions)

    def test_run_all_migrations_is_idempotent(self):
        run_all_migrations(self.engine)
        # Running a second time should be a clean no-op
        run_all_migrations(self.engine)
        with self.engine.connect() as conn:
            count = conn.execute(
                text("SELECT COUNT(*) FROM schema_migrations")
            ).scalar_one()
            self.assertEqual(count, 8)


    def test_migration_connection_accepts_connection_and_engine(self):
        # Test passing an Engine
        with migration_connection(self.engine) as conn1:
            self.assertIsNotNone(conn1)
        # Test passing an active Connection
        with self.engine.begin() as conn2:
            with migration_connection(conn2) as conn3:
                self.assertIs(conn2, conn3)

    def test_migration_connection_rejects_invalid_type(self):
        with self.assertRaises(TypeError):
            with migration_connection("not-an-engine-or-connection"):
                pass

    def test_failed_migration_fails_closed_and_rolls_back(self):
        # If a migration fails mid-stream, the transaction must roll back and not record the version
        with self.assertRaises(RuntimeError):
            with migration_connection(self.engine) as conn:
                conn.execute(versions.insert().values(version="20261105-fail-test"))
                raise RuntimeError("Simulated failure during migration")

        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT version FROM schema_migrations WHERE version='20261105-fail-test'")
            ).first()
            self.assertIsNone(row)

    def test_platform_migration_is_versioned_and_runs_once(self):
        migrate_core(self.engine)
        migrate_platforms(self.engine)
        with self.engine.connect() as conn:
            version_row = conn.execute(
                text(
                    "SELECT version FROM schema_migrations WHERE version='20261105-platforms-v1'"
                )
            ).first()
            self.assertIsNotNone(version_row)

        # Subsequent call does not execute re-update
        migrate_platforms(self.engine)

    def test_concurrent_migrations_on_engine(self):
        def run(_):
            run_all_migrations(self.engine)

        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(run, range(3)))

        with self.engine.connect() as conn:
            count = conn.execute(
                text("SELECT COUNT(*) FROM schema_migrations")
            ).scalar_one()
            self.assertEqual(count, 8)


class StartupShutdownTests(unittest.TestCase):
    def test_startup_and_shutdown_lifecycle(self):
        with patch("app.main.engine", create_engine("sqlite:///:memory:")):
            with TestClient(app) as client:
                res = client.get("/api/health")
                self.assertEqual(res.status_code, 200)
                self.assertEqual(res.json(), {"status": "ok"})
                import app.main as main_mod

                self.assertIsNotNone(main_mod._scheduler)
                self.assertTrue(main_mod._scheduler.running)
            # After exiting context, on_shutdown should have stopped the scheduler
            self.assertIsNone(main_mod._scheduler)

    def test_startup_fails_closed_on_migration_error(self):
        with patch("app.main.run_all_migrations", side_effect=RuntimeError("Database migration failed")):
            with self.assertRaises(RuntimeError):
                with TestClient(app):
                    pass
