"""Versioned, additive schema foundations; never revalue solve awards."""
from sqlalchemy import Column, MetaData, String, Table, inspect, text
from contextlib import contextmanager

metadata = MetaData()
versions = Table("schema_migrations", metadata, Column("version", String(80), primary_key=True))


@contextmanager
def migration_connection(engine):
    """Lock before creating the version registry, including on a fresh database."""
    with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(72635001)"))
        metadata.create_all(connection)
        yield connection


def migrate_auth(engine):
    with migration_connection(engine) as connection:
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


def migrate_display_preference(engine):
    with migration_connection(engine) as connection:
        version = "20261105-global-display-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return
        columns = {column["name"] for column in inspect(connection).get_columns("users")}
        if "show_global_leaderboard" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN show_global_leaderboard BOOLEAN NOT NULL DEFAULT TRUE"))
        connection.execute(text("UPDATE users SET show_global_leaderboard = COALESCE(global_leaderboard_enabled, TRUE)"))
        connection.execute(versions.insert().values(version=version))


def migrate_tracking(engine):
    """Add evidence/award storage without revaluing or inventing legacy awards."""
    from .models import AcceptedSubmission, PointAward, ScoreSnapshot
    with migration_connection(engine) as connection:
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
