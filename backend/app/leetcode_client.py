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
from datetime import datetime, date, timezone
import httpx

logger = logging.getLogger("codestreak.leetcode")

GRAPHQL_URL = "https://leetcode.com/graphql"

HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}

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
                d = datetime.fromtimestamp(ts, tz=timezone.utc).date()
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

