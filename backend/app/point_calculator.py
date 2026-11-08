"""Runtime entry point for the stored-component calculator.

Daily challenge names/dates are never evidence of an earned daily award.
Reconciliation locks existing credit and adds new components in one transaction.
"""
from .reconciliation import reconcile_user


def recalculate_user_points(user, db, today_daily_slug=None, *, revision_windows=None, daily_solve_ids=None):
    # Preserve the old call signature during the pre-launch migration. The slug
    # alone cannot mint a bonus. The server sync supplies new live daily IDs.
    return reconcile_user(user, db, revision_windows=revision_windows, daily_solve_ids=daily_solve_ids)


async def recalculate_all_users_points(db):
    raise RuntimeError("Use a reviewed bounded reconciliation job; bulk startup revaluation is disabled")
