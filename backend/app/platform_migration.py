"""Additive migration for existing PostgreSQL and local SQLite installations."""
from .migrations import migrate_platforms

__all__ = ["migrate_platforms"]
