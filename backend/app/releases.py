"""Reviewed announcement records. Operators cannot inject arbitrary mail links/copy."""
from dataclasses import dataclass
from app.release_metadata import (
    DOWNLOAD_URL,
    RELEASE_NOTES,
    RELEASE_TAG,
    SEMANTIC_VERSION,
)


@dataclass(frozen=True)
class ReleaseNotice:
    notes: str
    download_url: str


RELEASE_NOTICES = {
    "integration-2026-11-05": ReleaseNotice(
        notes="Codeforces account integration and extension study-plan tracking are available. Update the extension and sign in again if requested.",
        download_url="https://codestreak-api.onrender.com/downloads/leetstreak.zip",
    ),
    RELEASE_TAG: ReleaseNotice(
        notes=RELEASE_NOTES,
        download_url=DOWNLOAD_URL,
    ),
    f"v{SEMANTIC_VERSION}": ReleaseNotice(
        notes=RELEASE_NOTES,
        download_url=DOWNLOAD_URL,
    ),
}
