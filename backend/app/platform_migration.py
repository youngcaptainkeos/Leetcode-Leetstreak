"""Additive migration for existing PostgreSQL and local SQLite installations."""
from sqlalchemy import inspect, text


def migrate_platforms(engine):
    columns = {
        "users": {"codeforces_username": "VARCHAR(80)", "codeforces_linked_at": "TIMESTAMP", "codeforces_last_sync": "TIMESTAMP", "codeforces_last_full_sync": "TIMESTAMP", "codeforces_sync_error": "VARCHAR(300)"},
        "solves": {"platform": "VARCHAR(20) NOT NULL DEFAULT 'leetcode'", "source_handle": "VARCHAR(80)", "source_submission_id": "BIGINT", "problem_rating": "DOUBLE PRECISION", "problem_url": "VARCHAR(500)", "scoring_version": "VARCHAR(40) NOT NULL DEFAULT 'leetcode-v1'"},
    }
    with engine.begin() as conn:
        for table, additions in columns.items():
            existing = {column["name"] for column in inspect(conn).get_columns(table)}
            for name, definition in additions.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_solves_platform ON solves (platform)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_solves_user_platform ON solves (user_id, platform)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_codeforces_handle ON users (lower(codeforces_username)) WHERE codeforces_username IS NOT NULL"))
        conn.execute(text("UPDATE solves SET source_handle = (SELECT leetcode_username FROM users WHERE users.id = solves.user_id) WHERE platform = 'leetcode' AND source_handle IS NULL"))
