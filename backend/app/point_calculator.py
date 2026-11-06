"""Runtime entry point for the stored-component calculator.

Daily challenge names/dates are never evidence of an earned daily award.
Reconciliation owns base revaluation and retained components in one transaction.
"""
from .reconciliation import reconcile_user


def recalculate_user_points(user, db, today_daily_slug=None, *, revision_windows=None):
    # Preserve the old call signature during the pre-launch migration. The slug
    # deliberately cannot mint a bonus. Future live awards require first-solve proof.
    return reconcile_user(user, db, revision_windows=revision_windows)


async def recalculate_all_users_points(db):
    raise RuntimeError("Use a reviewed bounded reconciliation job; bulk startup revaluation is disabled")
