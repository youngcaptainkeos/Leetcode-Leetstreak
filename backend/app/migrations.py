import threading
from contextlib import contextmanager
from sqlalchemy import Column, MetaData, String, Table, inspect, text
from sqlalchemy.engine import Connection, Engine

metadata = MetaData()
versions = Table("schema_migrations", metadata, Column("version", String(80), primary_key=True))
_local_migration_lock = threading.RLock()


@contextmanager
def migration_connection(target):
    """
    Lock before creating the version registry, including on a fresh database.
    Supports either an Engine (begins a transaction with advisory lock on PostgreSQL)
    or an existing Connection (executes within the current transaction).
    """
    if isinstance(target, Engine):
        if target.dialect.name == "postgresql":
            with target.begin() as connection:
                connection.execute(text("SELECT pg_advisory_xact_lock(72635001)"))
                metadata.create_all(connection, checkfirst=True)
                yield connection
        else:
            with _local_migration_lock:
                with target.begin() as connection:
                    metadata.create_all(connection, checkfirst=True)
                    yield connection
    elif isinstance(target, Connection):
        if target.dialect.name == "postgresql":
            target.execute(text("SELECT pg_advisory_xact_lock(72635001)"))
            metadata.create_all(target, checkfirst=True)
            yield target
        else:
            with _local_migration_lock:
                metadata.create_all(target, checkfirst=True)
                yield target
    else:
        raise TypeError(f"Expected Engine or Connection, got {type(target)}")


def migrate_core(target):
    """
    Initial core tables and schema baseline.
    Version: 20261105-core-v1
    """
    from .database import Base
    with migration_connection(target) as connection:
        version = "20261105-core-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return

        Base.metadata.create_all(connection, checkfirst=True)

        existing_users = {column["name"] for column in inspect(connection).get_columns("users")}
        user_additions = {
            "name": "VARCHAR(80) DEFAULT 'Coder'",
            "leetcode_username": "VARCHAR(80)",
            "email": "VARCHAR(120)",
            "password_hash": "VARCHAR(200)",
            "reset_otp": "VARCHAR(6)",
            "otp_expires_at": "TIMESTAMP",
            "points": "DOUBLE PRECISION DEFAULT 0.0",
            "last_notified_commit": "VARCHAR(40) DEFAULT 'legacy'",
            "global_leaderboard_enabled": "BOOLEAN DEFAULT TRUE",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        }
        for column, definition in user_additions.items():
            if column not in existing_users:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {column} {definition}"))

        existing_solves = {column["name"] for column in inspect(connection).get_columns("solves")}
        solve_additions = {
            "points_earned": "DOUBLE PRECISION DEFAULT 0.0",
            "difficulty": "VARCHAR(20)",
            "ac_rate": "DOUBLE PRECISION",
            "is_daily": "BOOLEAN DEFAULT FALSE",
        }
        for column, definition in solve_additions.items():
            if column not in existing_solves:
                connection.execute(text(f"ALTER TABLE solves ADD COLUMN {column} {definition}"))

        if connection.dialect.name == "postgresql":
            connection.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_leetcode_username_key"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_users_leetcode_username ON users (leetcode_username)"))

        connection.execute(versions.insert().values(version=version))


def migrate_platforms(target):
    """
    Multi-platform (Codeforces) schema extensions and indices.
    Version: 20261105-platforms-v1
    """
    with migration_connection(target) as connection:
        version = "20261105-platforms-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return
        columns = {
            "users": {
                "codeforces_username": "VARCHAR(80)",
                "codeforces_linked_at": "TIMESTAMP",
                "codeforces_last_sync": "TIMESTAMP",
                "codeforces_last_full_sync": "TIMESTAMP",
                "codeforces_sync_error": "VARCHAR(300)",
            },
            "solves": {
                "platform": "VARCHAR(20) NOT NULL DEFAULT 'leetcode'",
                "source_handle": "VARCHAR(80)",
                "source_submission_id": "BIGINT",
                "problem_rating": "DOUBLE PRECISION",
                "problem_url": "VARCHAR(500)",
                "scoring_version": "VARCHAR(40) NOT NULL DEFAULT 'leetcode-v1'",
            },
        }
        for table, additions in columns.items():
            existing = {column["name"] for column in inspect(connection).get_columns(table)}
            for name, definition in additions.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_solves_platform ON solves (platform)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_solves_user_platform ON solves (user_id, platform)"))
        if connection.dialect.name == "postgresql":
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_codeforces_handle ON users (lower(codeforces_username)) WHERE codeforces_username IS NOT NULL"))
        connection.execute(text("UPDATE solves SET source_handle = (SELECT leetcode_username FROM users WHERE users.id = solves.user_id) WHERE platform = 'leetcode' AND source_handle IS NULL"))
        connection.execute(versions.insert().values(version=version))


def migrate_auth(target):
    with migration_connection(target) as connection:
        version = "20261105-auth-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return
        existing = {column["name"] for column in inspect(connection).get_columns("users")}
        additions = {
            "session_version": "INTEGER NOT NULL DEFAULT 0",
            "reset_otp_hash": "VARCHAR(64)", "otp_request_id": "VARCHAR(64)",
            "otp_attempts": "INTEGER NOT NULL DEFAULT 0", "otp_last_requested_at": "TIMESTAMP",
        }
        for column, definition in additions.items():
            if column not in existing:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {column} {definition}"))
        # Legacy plaintext reset codes cannot survive this protocol change.
        connection.execute(text("UPDATE users SET reset_otp = NULL, otp_expires_at = NULL WHERE reset_otp IS NOT NULL"))
        connection.execute(versions.insert().values(version=version))


def migrate_display_preference(target):
    with migration_connection(target) as connection:
        version = "20261105-global-display-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return
        columns = {column["name"] for column in inspect(connection).get_columns("users")}
        if "show_global_leaderboard" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN show_global_leaderboard BOOLEAN NOT NULL DEFAULT TRUE"))
        connection.execute(text("UPDATE users SET show_global_leaderboard = COALESCE(global_leaderboard_enabled, TRUE)"))
        connection.execute(versions.insert().values(version=version))


def migrate_tracking(target):
    """Add evidence/award storage without revaluing or inventing legacy awards."""
    from .models import AcceptedSubmission, PointAward, ScoreSnapshot
    with migration_connection(target) as connection:
        version = "20261105-tracking-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return
        additions = {
            "users": {
                "leetcode_account_version": "INTEGER NOT NULL DEFAULT 0",
                "codeforces_account_version": "INTEGER NOT NULL DEFAULT 0",
                "leetcode_last_sync": "TIMESTAMP",
                "leetcode_history_state": "VARCHAR(30) NOT NULL DEFAULT 'partial'",
                "leetcode_history_gap": "BOOLEAN NOT NULL DEFAULT TRUE",
            },
            "solves": {
                "account_version": "INTEGER NOT NULL DEFAULT 0",
                "first_solve_at": "TIMESTAMP",
                "first_solve_verified": "BOOLEAN NOT NULL DEFAULT FALSE",
                "score_components_state": "VARCHAR(30) NOT NULL DEFAULT 'legacy'",
            },
        }
        for table, columns in additions.items():
            existing = {column["name"] for column in inspect(connection).get_columns(table)}
            for column, definition in columns.items():
                if column not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
        for model in (AcceptedSubmission, PointAward, ScoreSnapshot):
            model.__table__.create(connection, checkfirst=True)
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_solves_first_solve_at ON solves (first_solve_at)"))
        connection.execute(versions.insert().values(version=version))


def migrate_progress(target):
    """
    User progress and custom study plans/playlists persistence.
    Version: 20261106-progress-v1
    """
    from .models import UserProgress, UserCustomPlan
    with migration_connection(target) as connection:
        version = "20261106-progress-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return
        for model in (UserProgress, UserCustomPlan):
            model.__table__.create(connection, checkfirst=True)
        connection.execute(versions.insert().values(version=version))


def run_all_migrations(target):
    """
    Run all pending migrations in an atomic transaction under advisory lock on PostgreSQL.
    Fails closed if any migration fails.
    """
    with migration_connection(target) as connection:
        migrate_core(connection)
        migrate_platforms(connection)
        migrate_auth(connection)
        migrate_display_preference(connection)
        migrate_tracking(connection)
        migrate_progress(connection)

