"""
LeetCode Contest Rating dataset lookup.
Provides contest Elo ratings for algorithm problems from Weekly/Biweekly contests.
Ratings typically range from ~800 to 3500+.
Loads local zerotrac_ratings.json and automatically updates weekly from ZeroTrac.
"""
import os
import json
import logging
from typing import Optional, Dict
import httpx

logger = logging.getLogger("codestreak.ratings")

CONTEST_RATINGS: Dict[str, float] = {}

_json_path = os.path.join(os.path.dirname(__file__), "zerotrac_ratings.json")
ZEROTRAC_DATA_URL = "https://zerotrac.github.io/leetcode_problem_rating/data.json"


def load_local_ratings() -> int:
    global CONTEST_RATINGS
    if os.path.exists(_json_path):
        try:
            with open(_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                CONTEST_RATINGS.update(data)
            logger.info("Loaded %d ZeroTrac contest ratings from zerotrac_ratings.json.", len(CONTEST_RATINGS))
            return len(CONTEST_RATINGS)
        except Exception as e:
            logger.warning("Failed to load zerotrac_ratings.json: %s", e)
    return len(CONTEST_RATINGS)


# Load local cache on module import
load_local_ratings()


async def refresh_zerotrac_dataset() -> int:
    """
    Fetches the latest contest ratings from ZeroTrac's dataset URL,
    updates CONTEST_RATINGS in memory, and persists to zerotrac_ratings.json.
    """
    global CONTEST_RATINGS
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(ZEROTRAC_DATA_URL)
            if resp.status_code == 200:
                items = resp.json()
                new_ratings = {}
                for x in items:
                    slug = x.get("TitleSlug")
                    rating = x.get("Rating")
                    if slug and rating is not None:
                        new_ratings[slug.strip().lower()] = round(float(rating), 2)

                if new_ratings:
                    CONTEST_RATINGS.update(new_ratings)
                    try:
                        with open(_json_path, "w", encoding="utf-8") as f:
                            json.dump(CONTEST_RATINGS, f, indent=2)
                    except Exception as err:
                        logger.warning("Failed to save zerotrac_ratings.json: %s", err)
                    logger.info("Successfully refreshed %d ZeroTrac ratings.", len(new_ratings))
                    return len(new_ratings)
    except Exception as e:
        logger.warning("Failed to refresh ZeroTrac dataset: %s", e)
    return len(CONTEST_RATINGS)


def get_contest_rating(title_slug: str) -> Optional[float]:
    """
    Returns the contest Elo rating for a title slug if known.
    """
    if not title_slug:
        return None
    slug = title_slug.strip().lower()
    return CONTEST_RATINGS.get(slug)
