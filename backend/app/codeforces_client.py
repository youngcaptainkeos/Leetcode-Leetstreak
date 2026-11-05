"""Public Codeforces metadata only; no passwords, API keys, or source code."""
import asyncio
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
    accepted = {}
    seen_submissions = set()
    offset = 1
    for _ in range(500):
        rows = await codeforces_request("user.status", {"handle": handle, "from": offset, "count": 1000})
        if not isinstance(rows, list):
            raise CodeforcesError("Codeforces returned an invalid submission list. Saved scores are unchanged.")
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), int):
                raise CodeforcesError("Codeforces returned an invalid submission. Saved scores are unchanged.")
            if row["id"] in seen_submissions:
                continue
            seen_submissions.add(row["id"])
            if row.get("verdict") != "OK" or row.get("testset") != "TESTS":
                continue
            author = row.get("author", {})
            members = author.get("members", [])
            if author.get("ghost") or author.get("teamId") or len(members) != 1 or members[0].get("handle", "").lower() != handle.lower():
                continue
            problem = row.get("problem", {})
            contest_id, index = problem.get("contestId"), problem.get("index")
            timestamp = row.get("creationTimeSeconds")
            if not isinstance(contest_id, int) or not isinstance(index, str) or not re.fullmatch(r"[A-Za-z0-9]+", index) or not isinstance(timestamp, int) or timestamp <= 0 or timestamp > time.time() + 300:
                continue
            key = f"cf-{contest_id}-{index.lower()}"
            previous = accepted.get(key)
            if previous and previous["timestamp"] <= timestamp:
                continue
            rating = problem.get("rating")
            accepted[key] = {
                "slug": key, "title": str(problem.get("name") or f"{contest_id}{index}")[:300],
                "url": f"https://codeforces.com/{'gym' if contest_id >= 100000 else 'contest'}/{contest_id}/problem/{index}",
                "rating": rating if isinstance(rating, (int, float)) and 800 <= rating <= 5000 else None,
                "timestamp": timestamp, "submission_id": row["id"],
            }
        if len(rows) < 1000 or (since is not None and rows and min(r.get("creationTimeSeconds", int(time.time())) for r in rows) < since):
            return list(accepted.values())
        offset += 900
    raise CodeforcesError("This account needs a larger history import. Saved scores are unchanged.")
