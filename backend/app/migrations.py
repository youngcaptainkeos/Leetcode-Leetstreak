"""Versioned, additive schema foundations; never revalue solve awards."""
from sqlalchemy import Column, MetaData, String, Table, inspect, text
from sqlalchemy.engine import Connection
from contextlib import contextmanager

metadata = MetaData()
versions = Table("schema_migrations", metadata, Column("version", String(80), primary_key=True))


@contextmanager
def migration_connection(bind):
    """Serialize migrations before inspecting schema; nested steps share one transaction."""
    if isinstance(bind, Connection):
        if not bind.in_transaction():
            raise RuntimeError("Migration steps require an active transaction")
        yield bind
        return
    with bind.begin() as connection:
        if connection.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(72635001)"))
        elif connection.dialect.name == "sqlite":
            # sqlite3 legacy mode does not begin a transaction for DDL. Begin
            # explicitly so schema and version markers roll back together.
            connection.exec_driver_sql("BEGIN IMMEDIATE")
        else:
            raise RuntimeError("Migrations support PostgreSQL and SQLite only")
        metadata.create_all(connection)
        yield connection


def migrate_core(engine):
    """Replace legacy import/startup DDL without guessing historical data."""
    with migration_connection(engine) as connection:
        version = "20261106-core-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return
        additions = {
            "users": {
                "email": "VARCHAR(120)", "password_hash": "VARCHAR(200)",
                "reset_otp": "VARCHAR(6)", "otp_expires_at": "TIMESTAMP",
                "avatar_url": "VARCHAR(500)",
                "easy_count": "INTEGER DEFAULT 0", "medium_count": "INTEGER DEFAULT 0",
                "hard_count": "INTEGER DEFAULT 0", "official_streak": "INTEGER DEFAULT 0",
                "points": "DOUBLE PRECISION DEFAULT 0.0",
                "last_notified_commit": "VARCHAR(40) DEFAULT 'legacy'",
                "global_leaderboard_enabled": "BOOLEAN DEFAULT TRUE",
                # Adding a now() default here would invent legacy registration dates.
                "created_at": "TIMESTAMP",
            },
            "solves": {
                "title": "VARCHAR(300)", "difficulty": "VARCHAR(20)",
                "ac_rate": "DOUBLE PRECISION", "is_daily": "BOOLEAN NOT NULL DEFAULT FALSE",
                "points_earned": "DOUBLE PRECISION DEFAULT 0.0",
            },
        }
        for table, columns in additions.items():
            existing = {column["name"] for column in inspect(connection).get_columns(table)}
            for column, definition in columns.items():
                if column not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
        if connection.dialect.name == "postgresql":
            # This default applies only to future inserts; existing NULLs stay unknown.
            connection.execute(text("ALTER TABLE users ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP"))
            connection.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_leetcode_username_key"))
        elif any(constraint["column_names"] == ["leetcode_username"]
                 for constraint in inspect(connection).get_unique_constraints("users")):
            raise RuntimeError("Legacy SQLite handle uniqueness requires an explicit table migration")
        # Normalize the historical standalone unique index to a non-unique lookup.
        for index in inspect(connection).get_indexes("users"):
            if index["name"] == "ix_users_leetcode_username" and index["unique"]:
                connection.execute(text("DROP INDEX ix_users_leetcode_username"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_users_leetcode_username ON users (leetcode_username)"))
        connection.execute(versions.insert().values(version=version))


def run_migrations(engine):
    """Apply the entire startup schema sequence atomically, without provider I/O.

    Keep existing step versions stable: installations may already have applied
    auth/display/tracking separately. Unrecorded steps and their markers commit
    together; a failed step aborts startup and leaves the prior schema intact.
    """
    from .database import Base
    from . import models  # Register every table before bootstrapping a fresh DB.
    from .platform_migration import migrate_platforms

    with migration_connection(engine) as connection:
        bootstrap_version = "20261106-bootstrap-v1"
        if not connection.execute(versions.select().where(versions.c.version == bootstrap_version)).first():
            Base.metadata.create_all(connection)
            connection.execute(versions.insert().values(version=bootstrap_version))
        for step in (migrate_core, migrate_platforms, migrate_auth, migrate_display_preference, migrate_tracking, migrate_credits, migrate_calendar, migrate_credit_privacy, migrate_progress, migrate_sync_jobs, migrate_sync_recovery, migrate_review_accounts, migrate_database_first):
            step(connection)
        # A recorded version is not permission to serve an incomplete schema.
        inspector = inspect(connection)
        for table in Base.metadata.sorted_tables:
            existing = {column["name"] for column in inspector.get_columns(table.name)}
            missing = set(table.columns.keys()) - existing
            if missing:
                raise RuntimeError(f"Incomplete schema for {table.name}: {', '.join(sorted(missing))}")


def migrate_database_first(engine):
    """Repair recorded LC dates without changing awards or account balances."""
    with migration_connection(engine) as connection:
        version = "20261108-database-first-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return
        existing = {column["name"] for column in inspect(connection).get_columns("solves")}
        if "first_solve_basis" not in existing:
            connection.execute(text("ALTER TABLE solves ADD COLUMN first_solve_basis VARCHAR(30) NOT NULL DEFAULT 'unknown'"))
        connection.execute(text("UPDATE solves SET first_solve_basis = 'provider_full' WHERE first_solve_verified = TRUE"))
        connection.execute(text("""
            WITH first_events AS (
                SELECT s.id, MIN(a.accepted_at) AS accepted_at
                FROM solves s JOIN users u ON u.id = s.user_id
                JOIN accepted_submissions a ON a.solve_id = s.id
                    AND a.user_id = s.user_id AND a.platform = s.platform
                    AND a.account_version = s.account_version AND a.title_slug = s.title_slug
                WHERE s.platform = 'leetcode' AND s.first_solve_verified = FALSE
                    AND s.account_version = u.leetcode_account_version
                    AND (LOWER(s.source_handle) = LOWER(u.leetcode_username)
                        OR (s.source_handle IS NULL AND s.account_version = 0))
                    AND a.accepted_at <= CURRENT_TIMESTAMP AND s.solved_at <= CURRENT_TIMESTAMP
                GROUP BY s.id
            )
            UPDATE solves SET first_solve_basis = 'database_first',
                first_solve_at = CASE
                    WHEN solved_at < (SELECT accepted_at FROM first_events WHERE first_events.id = solves.id)
                    THEN solved_at ELSE (SELECT accepted_at FROM first_events WHERE first_events.id = solves.id) END,
                source_handle = COALESCE(source_handle, (SELECT leetcode_username FROM users WHERE users.id = solves.user_id))
            WHERE id IN (SELECT id FROM first_events) AND first_solve_basis = 'unknown'
        """))
        # Every question already present at policy cutover keeps its prior
        # credit. Only later inserts can earn a new database-first base award.
        from .models import AccountCredit, Solve
        for credit in connection.execute(AccountCredit.__table__.select().where(
                AccountCredit.kind == "locked_balance", AccountCredit.platform == "leetcode")).mappings():
            state = dict(credit["input_snapshot"])
            present = connection.execute(Solve.__table__.select().with_only_columns(Solve.title_slug).where(
                Solve.user_id == credit["user_id"], Solve.platform == "leetcode",
                Solve.account_version == credit["account_version"])).scalars()
            state["covered"] = sorted(set(state["covered"]) | set(present))
            state["first_policy"] = "database-first-v1"
            connection.execute(AccountCredit.__table__.update().where(AccountCredit.id == credit["id"]).values(input_snapshot=state))
        connection.execute(versions.insert().values(version=version))


def migrate_review_accounts(engine):
    with migration_connection(engine) as connection:
        version = "20261108-review-accounts-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return
        existing = {column["name"] for column in inspect(connection).get_columns("users")}
        if "is_reviewer" not in existing:
            connection.execute(text("ALTER TABLE users ADD COLUMN is_reviewer BOOLEAN NOT NULL DEFAULT FALSE"))
        connection.execute(versions.insert().values(version=version))


def migrate_progress(engine):
    from .models import AccountProgress
    with migration_connection(engine) as connection:
        version = "20261107-account-progress-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return
        AccountProgress.__table__.create(connection, checkfirst=True)
        if connection.dialect.name == "postgresql":
            connection.execute(text("ALTER TABLE account_progress ENABLE ROW LEVEL SECURITY"))
            connection.execute(text("REVOKE ALL ON TABLE account_progress FROM PUBLIC"))
            for role in connection.execute(text("SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')")).scalars():
                connection.execute(text(f"REVOKE ALL ON TABLE account_progress FROM {role}"))
        connection.execute(versions.insert().values(version=version))


def migrate_credits(engine):
    from .models import AccountCredit
    with migration_connection(engine) as connection:
        version = "20261106-credits-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return
        AccountCredit.__table__.create(connection, checkfirst=True)
        connection.execute(versions.insert().values(version=version))


def migrate_calendar(engine):
    from .models import ProviderCalendar
    with migration_connection(engine) as connection:
        version = "20261106-provider-calendar-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return
        ProviderCalendar.__table__.create(connection, checkfirst=True)
        connection.execute(versions.insert().values(version=version))


def migrate_credit_privacy(engine):
    """Custom-auth API owns access; do not expose new tables through the Data API."""
    with migration_connection(engine) as connection:
        version = "20261106-credit-privacy-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return
        if connection.dialect.name == "postgresql":
            for table in ("account_credits", "provider_calendar"):
                connection.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
            connection.execute(text("REVOKE ALL ON TABLE account_credits, provider_calendar FROM PUBLIC"))
            roles = connection.execute(text("SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')")).scalars().all()
            for role in roles:
                connection.execute(text(f"REVOKE ALL ON TABLE account_credits, provider_calendar FROM {role}"))
        connection.execute(versions.insert().values(version=version))


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


def migrate_sync_jobs(engine):
    from .models import UserSyncJob
    with migration_connection(engine) as connection:
        version = "20261107-sync-jobs-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return
        UserSyncJob.__table__.create(connection, checkfirst=True)
        if connection.dialect.name == "postgresql":
            connection.execute(text("ALTER TABLE user_sync_jobs ENABLE ROW LEVEL SECURITY"))
            connection.execute(text("REVOKE ALL ON TABLE user_sync_jobs FROM PUBLIC"))
            for role in connection.execute(text("SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')")).scalars():
                connection.execute(text(f"REVOKE ALL ON TABLE user_sync_jobs FROM {role}"))
        connection.execute(versions.insert().values(version=version))


def migrate_sync_recovery(engine):
    """Add ownership/attempt tracking without replacing existing queued jobs."""
    with migration_connection(engine) as connection:
        version = "20261108-sync-recovery-v1"
        if connection.execute(versions.select().where(versions.c.version == version)).first():
            return
        columns = {column["name"] for column in inspect(connection).get_columns("user_sync_jobs")}
        for column, definition in {"worker_token": "VARCHAR(36)",
                                   "attempts": "INTEGER NOT NULL DEFAULT 0"}.items():
            if column not in columns:
                connection.execute(text(f"ALTER TABLE user_sync_jobs ADD COLUMN {column} {definition}"))
        connection.execute(versions.insert().values(version=version))
