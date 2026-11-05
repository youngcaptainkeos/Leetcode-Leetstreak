"""Opt-in PostgreSQL checks. Only a dedicated local test database is allowed."""
import os
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from app.migrations import migrate_auth, migrate_display_preference


class PostgresMigrationTests(unittest.TestCase):
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
