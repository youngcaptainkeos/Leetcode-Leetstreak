"""Public Codeforces metadata only; no passwords, API keys, or source code."""
import asyncio
import math
import re
import time
from typing import Optional

import httpx


class CodeforcesError(Exception):
    pass


_request_lock = asyncio.Lock()
_last_request = 0.0


async def codeforces_request(method: str, params: dict):
    global _last_request
    # Shared by profile checks and all sync jobs (CF permits 1 call / 2 seconds).
    async with _request_lock:
        wait = 2.1 - (time.monotonic() - _last_request)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_request = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=25) as client:
                response = await client.get(f"https://codeforces.com/api/{method}", params=params)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise CodeforcesError("Codeforces is unavailable. Automatic syncing will retry later.") from error
        if data.get("status") != "OK":
            raise CodeforcesError("Codeforces could not return this public account. Check the handle or try again later.")
        return data.get("result")


def normalize_handle(value: str) -> str:
    handle = value.strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,24}", handle):
        raise CodeforcesError("Enter your Codeforces handle, not a profile URL or display name.")
    return handle


async def fetch_profile(handle: str) -> dict:
    result = await codeforces_request("user.info", {"handles": normalize_handle(handle), "checkHistoricHandles": "false"})
    if not isinstance(result, list) or len(result) != 1 or not result[0].get("handle"):
        raise CodeforcesError("This public Codeforces account was not found.")
    return {"handle": result[0]["handle"]}


async def fetch_accepted_history(handle: str, since: Optional[int] = None) -> list[dict]:
    """Read every public submission and keep the earliest final AC per problem.

    A complete scan also reconciles rejudgements and keeps reruns idempotent.
    Pages overlap to tolerate new submissions arriving during pagination.
    """
    handle = normalize_handle(handle)
    accepted = {}
    seen_submissions = {}
    offset = 1
    page_size = 1000 if since is None else 100
    for _ in range(500):
        rows = await codeforces_request("user.status", {"handle": handle, "from": offset, "count": page_size})
        if not isinstance(rows, list):
            raise CodeforcesError("Codeforces returned an invalid submission list. Saved scores are unchanged.")
        for row in rows:
            if (not isinstance(row, dict) or type(row.get("id")) is not int or row["id"] <= 0
                    or type(row.get("creationTimeSeconds")) is not int
                    or not 0 < row["creationTimeSeconds"] <= time.time() + 300):
                raise CodeforcesError("Codeforces returned an invalid submission. Saved scores are unchanged.")
            if row["id"] in seen_submissions:
                if seen_submissions[row["id"]] != row:
                    raise CodeforcesError("Codeforces history changed during import. Automatic syncing will retry later.")
                continue
            seen_submissions[row["id"]] = row
            if row.get("verdict") != "OK" or row.get("testset") != "TESTS":
                continue
            author = row.get("author", {})
            if not isinstance(author, dict):
                raise CodeforcesError("Codeforces returned invalid author evidence.")
            members = author.get("members", [])
            if (not isinstance(members, list) or not members
                    or any(not isinstance(member, dict) or not isinstance(member.get("handle"), str) for member in members)):
                raise CodeforcesError("Codeforces returned invalid author evidence.")
            if (author.get("ghost") or author.get("teamId") or len(members) != 1
                    or members[0]["handle"].lower() != handle.lower()):
                continue
            problem = row.get("problem", {})
            if not isinstance(problem, dict):
                raise CodeforcesError("Codeforces returned invalid problem evidence.")
            contest_id, index = problem.get("contestId"), problem.get("index")
            timestamp = row.get("creationTimeSeconds")
            if type(contest_id) is not int or contest_id <= 0 or not isinstance(index, str) or not re.fullmatch(r"[A-Za-z0-9]+", index):
                raise CodeforcesError("Codeforces returned an unsupported problem identity. Saved history is unchanged.")
            key = f"cf-{contest_id}-{index.lower()}"
            previous = accepted.get(key)
            event = {"submission_id": row["id"], "timestamp": timestamp}
            if previous:
                previous["accepted_submissions"].append(event)
                if (previous["timestamp"], previous["submission_id"]) <= (timestamp, row["id"]):
                    continue
            rating = problem.get("rating")
            accepted[key] = {
                "slug": key, "title": str(problem.get("name") or f"{contest_id}{index}")[:300],
                "url": f"https://codeforces.com/{'gym' if contest_id >= 100000 else 'contest'}/{contest_id}/problem/{index}",
                "rating": rating if type(rating) in (int, float) and math.isfinite(rating) and 800 <= rating <= 5000 else None,
                "timestamp": timestamp, "submission_id": row["id"],
                "accepted_submissions": previous["accepted_submissions"] if previous else [event],
            }
        if len(rows) < page_size or (since is not None and rows and min(r.get("creationTimeSeconds", int(time.time())) for r in rows) < since):
            for problem in accepted.values():
                problem["accepted_submissions"].sort(key=lambda event: (event["timestamp"], event["submission_id"]))
            return sorted(accepted.values(), key=lambda problem: problem["slug"])
        offset += page_size - page_size // 10
        # Busy accounts catch up in large pages after the inexpensive head
        # check, rather than making ten rate-limited calls per 1,000 entries.
        page_size = 1000
    raise CodeforcesError("This account needs a larger history import. Saved scores are unchanged.")
