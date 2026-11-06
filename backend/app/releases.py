"""Reviewed announcement records. Operators cannot inject arbitrary mail links/copy."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ReleaseNotice:
    notes: str
    download_url: str


RELEASE_NOTICES = {
    "integration-2026-11-05": ReleaseNotice(
        notes="Codeforces account integration and extension study-plan tracking are available. Update the extension and sign in again if requested.",
        download_url="https://codestreak-api.onrender.com/downloads/leetstreak.zip",
    ),
}
