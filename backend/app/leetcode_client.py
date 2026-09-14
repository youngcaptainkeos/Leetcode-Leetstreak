"""
Client for LeetCode's public GraphQL endpoint.

Fetches:
- Recent AC submissions (`recentAcSubmissionList`)
- User profile (`avatar`, `realName`)
- Problem difficulty stats (`submitStatsGlobal`)
- Complete submission calendar & streak (`userCalendar`)
"""
import json
import logging
from datetime import datetime, date, timezone, timedelta
from typing import Optional, Dict, Any, List
import httpx

IST = timezone(timedelta(hours=5, minutes=30))

logger = logging.getLogger("codestreak.leetcode")

GRAPHQL_URL = "https://leetcode.com/graphql"

HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}

DAILY_CHALLENGE_QUERY = """
query questionOfToday {
  activeDailyCodingChallengeQuestion {
    date
    question {
      title
      titleSlug
    }
  }
}
"""

RECENT_AC_QUERY = """
query recentAcSubmissions($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    id
    title
    titleSlug
    timestamp
  }
}
"""

async def fetch_today_daily_challenge_slug() -> Optional[str]:
    """Fetches today's official LeetCode Daily Challenge titleSlug."""
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.post(
                GRAPHQL_URL,
                headers=HEADERS,
                json={"query": DAILY_CHALLENGE_QUERY},
            )
            if resp.status_code == 200:
                data = resp.json()
                q = (data.get("data") or {}).get("activeDailyCodingChallengeQuestion") or {}
                question = q.get("question") or {}
                return question.get("titleSlug")
    except Exception as e:
        logger.warning("Failed to fetch LeetCode Daily Challenge slug: %s", e)
    return None


MONTHLY_DAILY_CHALLENGES_QUERY = """
query dailyCodingChallengeV2($year: Int!, $month: Int!) {
  dailyCodingChallengeV2(year: $year, month: $month) {
    challenges {
      date
      question {
        titleSlug
        title
      }
    }
  }
}
"""


async def fetch_monthly_daily_challenges(year: int, month: int) -> Dict[str, str]:
    """Fetches full monthly archive of LeetCode Daily Challenge titleSlugs mapped by 'YYYY-MM-DD'."""
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            resp = await client.post(
                GRAPHQL_URL,
                headers=HEADERS,
                json={"query": MONTHLY_DAILY_CHALLENGES_QUERY, "variables": {"year": year, "month": month}},
            )
            if resp.status_code == 200:
                data = resp.json()
                challenges = (data.get("data") or {}).get("dailyCodingChallengeV2", {}).get("challenges") or []
                res = {}
                for c in challenges:
                    dt = c.get("date")
                    q = c.get("question") or {}
                    slug = q.get("titleSlug")
                    if dt and slug:
                        res[dt] = slug.strip().lower()
                return res
    except Exception as e:
        logger.warning("Failed to fetch monthly daily challenges for %d-%d: %s", year, month, e)
    return {}

USER_FULL_PROFILE_QUERY = """
query userFullProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      realName
      userAvatar
    }
    submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
      }
    }
    userCalendar {
      activeYears
      streak
      totalActiveDays
      submissionCalendar
    }
  }
}
"""


class LeetCodeError(Exception):
    pass


async def get_recent_ac_submissions(username: str, limit: int = 20) -> list[dict]:
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        resp = await client.post(
            GRAPHQL_URL,
            headers=HEADERS,
            json={
                "query": RECENT_AC_QUERY,
                "variables": {"username": username, "limit": limit},
            },
        )
    resp.raise_for_status()
    data = resp.json()
    if data.get("errors"):
        raise LeetCodeError(str(data["errors"]))
    submissions = (data.get("data") or {}).get("recentAcSubmissionList")
    if submissions is None:
        raise LeetCodeError(f"No such user or profile not public: {username}")
    return submissions


async def fetch_leetcode_user_data(username: str) -> dict:
    """
    Fetches comprehensive user data from LeetCode:
    - User profile (avatar, username)
    - Problem solve counts (Easy, Medium, Hard)
    - Complete submission calendar mapped to Python date objects
    - Official LeetCode streak and total active days
    - Recent accepted submissions
    """
    async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
        p_resp = await client.post(
            GRAPHQL_URL,
            headers=HEADERS,
            json={"query": USER_FULL_PROFILE_QUERY, "variables": {"username": username}},
        )
        p_resp.raise_for_status()
        p_data = p_resp.json()

        if p_data.get("errors"):
            raise LeetCodeError(str(p_data["errors"]))

        matched = (p_data.get("data") or {}).get("matchedUser")
        if not matched:
            raise LeetCodeError(f"LeetCode user '{username}' was not found or profile is private.")

        profile_info = matched.get("profile") or {}
        avatar_url = profile_info.get("userAvatar")
        real_name = profile_info.get("realName")

        # Parse difficulty breakdown
        difficulty_counts = {"Easy": 0, "Medium": 0, "Hard": 0}
        stats_list = (matched.get("submitStatsGlobal") or {}).get("acSubmissionNum") or []
        for row in stats_list:
            if row.get("difficulty") in difficulty_counts:
                difficulty_counts[row["difficulty"]] = row.get("count", 0)

        # Parse calendar
        calendar_info = matched.get("userCalendar") or {}
        official_streak = calendar_info.get("streak", 0)
        total_active_days = calendar_info.get("totalActiveDays", 0)
        raw_calendar_str = calendar_info.get("submissionCalendar") or "{}"

        parsed_calendar = {}
        try:
            raw_cal_map = json.loads(raw_calendar_str)
            for ts_str, count in raw_cal_map.items():
                ts = int(ts_str)
                d = datetime.fromtimestamp(ts, tz=IST).date()
                parsed_calendar[d] = count
        except Exception as e:
            logger.warning("Error parsing submissionCalendar for %s: %s", username, e)

        # Recent AC submissions for the solves ledger
        recent_submissions = []
        try:
            ac_resp = await client.post(
                GRAPHQL_URL,
                headers=HEADERS,
                json={"query": RECENT_AC_QUERY, "variables": {"username": username, "limit": 20}},
            )
            if ac_resp.status_code == 200:
                ac_data = ac_resp.json()
                recent_submissions = (ac_data.get("data") or {}).get("recentAcSubmissionList") or []
        except Exception as e:
            logger.warning("Recent AC submissions query failed for %s: %s", username, e)

        return {
            "username": matched.get("username", username),
            "avatar_url": avatar_url,
            "real_name": real_name,
            "difficulty_counts": difficulty_counts,
            "official_streak": official_streak,
            "total_active_days": total_active_days,
            "submission_calendar": parsed_calendar,
            "recent_submissions": recent_submissions,
        }


PROBLEM_INFO_QUERY = """
query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    title
    titleSlug
    difficulty
    stats
  }
}
"""

_PROBLEM_INFO_CACHE: Dict[str, dict] = {}


async def fetch_problem_info(title_slug: str) -> dict:
    """
    Fetches difficulty ('Easy', 'Medium', 'Hard') and ac_rate (float 0..100) for a titleSlug.
    Caches results in memory to minimize GraphQL calls.
    """
    if not title_slug:
        return {"difficulty": "Medium", "ac_rate": None}

    slug = title_slug.strip().lower()
    if slug in _PROBLEM_INFO_CACHE:
        return _PROBLEM_INFO_CACHE[slug]

    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            resp = await client.post(
                GRAPHQL_URL,
                headers=HEADERS,
                json={"query": PROBLEM_INFO_QUERY, "variables": {"titleSlug": slug}},
            )
            if resp.status_code == 200:
                data = resp.json()
                q = (data.get("data") or {}).get("question")
                if q:
                    diff = q.get("difficulty") or "Medium"
                    ac_rate = None
                    stats_raw = q.get("stats")
                    if stats_raw:
                        try:
                            stats_dict = json.loads(stats_raw)
                            ac_str = str(stats_dict.get("acRate", "")).replace("%", "").strip()
                            if ac_str:
                                ac_rate = float(ac_str)
                        except Exception:
                            pass
                    info = {"difficulty": diff, "ac_rate": ac_rate}
                    _PROBLEM_INFO_CACHE[slug] = info
                    return info
    except Exception as e:
        logger.warning("Failed to fetch problem info for %s: %s", slug, e)

    default_info = {"difficulty": "Medium", "ac_rate": None}
    _PROBLEM_INFO_CACHE[slug] = default_info
    return default_info


