"""Account identity and accepted first dates under the publisher's recording rule."""


def current_account(user, solve):
    handle = getattr(user, solve.platform + "_username", None)
    generation = getattr(user, solve.platform + "_account_version", None)
    return bool(handle and solve.account_version == generation and (
        (solve.source_handle and solve.source_handle.casefold() == handle.casefold())
        or (not solve.source_handle and generation == 0)))


def first_solve_date(user, solve):
    """A database-first LC date is an explicit assumption, not lifetime proof."""
    eligible = solve.first_solve_verified or (
        solve.platform == "leetcode" and solve.first_solve_basis == "database_first")
    return solve.first_solve_at if (eligible and current_account(user, solve)
                                   and solve.source_handle) else None
