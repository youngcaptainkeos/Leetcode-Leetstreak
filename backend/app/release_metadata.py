"""Authoritative release metadata for LeetStreak.

Single source of truth for semantic versioning, client/backend compatibility,
source revision tracking, release notes, and artifact checksums.
"""
from dataclasses import dataclass
import hashlib
import json
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ==============================================================================
# 🎯 AUTHORITATIVE CANONICAL RELEASE SPECIFICATION
# ==============================================================================
SEMANTIC_VERSION = "1.1.0"
MIN_SUPPORTED_VERSION = "1.0.0"
RELEASE_TAG = "v1.1.0"
DEFAULT_SOURCE_REVISION = "2fd7c77"  # Recorded stable Git commit
RELEASE_DATE = "2026-11-06"
RELEASE_NOTES = (
    "LeetStreak v1.1.0: Full Codeforces multi-platform tracking, ZeroTrac contest problem "
    "ratings, custom study plans & Striver sheet import, coding-account ownership verification, "
    "and direct friendships leaderboards."
)
DOWNLOAD_URL = "https://codestreak-api.onrender.com/downloads/leetstreak.zip"
UPDATE_CHANNEL = "unpacked_zip"
UPDATE_INSTRUCTIONS = (
    "For manually loaded unpacked extensions: download leetstreak.zip, extract it to your "
    "extension directory, and click the Reload button (🔄) in chrome://extensions."
)

POSSIBLE_ZIP_PATHS = [
    os.path.join(os.path.dirname(__file__), "leetstreak.zip"),
    os.path.join(os.path.dirname(__file__), "..", "leetstreak.zip"),
    os.path.join(os.path.dirname(__file__), "..", "..", "leetstreak.zip"),
    "/app/app/leetstreak.zip",
    "/app/leetstreak.zip",
]


def get_source_revision() -> str:
    """Returns current git commit hash if in a git repo, otherwise fallback to recorded revision."""
    env_rev = os.environ.get("SOURCE_VERSION") or os.environ.get("GIT_COMMIT")
    if env_rev:
        return env_rev[:7]
    try:
        rev = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2.0
        ).strip()
        if rev:
            return rev
    except Exception:
        pass
    return DEFAULT_SOURCE_REVISION


def compute_file_checksums(file_path: str) -> Dict[str, Any]:
    """Computes SHA-256 and MD5 checksums for a file along with its size in bytes."""
    if not os.path.isfile(file_path):
        return {}
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    size = os.path.getsize(file_path)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
            md5.update(chunk)
    return {
        "filename": os.path.basename(file_path),
        "sha256": sha256.hexdigest(),
        "md5": md5.hexdigest(),
        "size_bytes": size,
    }


def find_served_zip_path() -> Optional[str]:
    """Finds the path to the downloadable leetstreak.zip on disk."""
    for p in POSSIBLE_ZIP_PATHS:
        if os.path.isfile(p):
            return p
    return None


def get_release_metadata() -> Dict[str, Any]:
    """Returns canonical release metadata payload for the extension version endpoint."""
    zip_path = find_served_zip_path()
    checksums = compute_file_checksums(zip_path) if zip_path else {}

    return {
        "latest_version": SEMANTIC_VERSION,
        "latest_commit": get_source_revision(),
        "min_supported_version": MIN_SUPPORTED_VERSION,
        "release_notes": RELEASE_NOTES,
        "download_url": DOWNLOAD_URL,
        "channel": UPDATE_CHANNEL,
        "update_instructions": UPDATE_INSTRUCTIONS,
        "checksums": checksums,
    }
