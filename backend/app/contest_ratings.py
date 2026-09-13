"""
LeetCode Contest Rating dataset lookup.
Provides contest Elo ratings for algorithm problems from Weekly/Biweekly contests.
Ratings typically range from ~800 to 3500+.
"""
import os
import json
import logging
from typing import Optional

logger = logging.getLogger("codestreak.ratings")

CONTEST_RATINGS: dict[str, float] = {}

# Load complete ZeroTrac dataset from zerotrac_ratings.json (2,584 contest problems)
_json_path = os.path.join(os.path.dirname(__file__), "zerotrac_ratings.json")
if os.path.exists(_json_path):
    try:
        with open(_json_path, "r", encoding="utf-8") as f:
            CONTEST_RATINGS = json.load(f)
        logger.info("Loaded %d ZeroTrac contest ratings from zerotrac_ratings.json.", len(CONTEST_RATINGS))
    except Exception as e:
        logger.warning("Failed to load zerotrac_ratings.json: %s", e)


def get_contest_rating(title_slug: str) -> Optional[float]:
    """
    Returns the contest Elo rating for a title slug if known.
    """
    if not title_slug:
        return None
    slug = title_slug.strip().lower()
    return CONTEST_RATINGS.get(slug)
