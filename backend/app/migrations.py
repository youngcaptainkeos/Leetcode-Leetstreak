"""Versioned, additive authentication migration; never touches solve awards."""
from sqlalchemy import Column, MetaData, String, Table, inspect, text

metadata = MetaData()
versions = Table("schema_migrations", metadata, Column("version", String(80), primary_key=True))


def migrate_auth(engine):
    metadata.create_all(engine)
    with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(72635001)"))
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
    metadata.create_all(engine)
    with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(72635001)"))
        version = "20261105-global-display-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return
        columns = {column["name"] for column in inspect(connection).get_columns("users")}
        if "show_global_leaderboard" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN show_global_leaderboard BOOLEAN NOT NULL DEFAULT TRUE"))
        connection.execute(text("UPDATE users SET show_global_leaderboard = COALESCE(global_leaderboard_enabled, TRUE)"))
        connection.execute(versions.insert().values(version=version))
