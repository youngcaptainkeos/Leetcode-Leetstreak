#!/usr/bin/env python3
"""Start one protected all-user poll from any computer with Python 3.

Requires the deployment's ADMIN_SECRET, read privately from a prompt or an
existing environment variable. Never stores it or includes it in command args.
"""
import getpass
import json
import os
import urllib.error
import urllib.request


def main():
    secret = os.environ.get("ADMIN_SECRET") or getpass.getpass("Render ADMIN_SECRET (hidden): ")
    if len(secret.encode()) < 32:
        raise SystemExit("A configured ADMIN_SECRET of at least 32 bytes is required.")
    request = urllib.request.Request(
        "https://codestreak-api.onrender.com/api/admin/poll-now",
        method="POST", headers={"X-Admin-Secret": secret},
    )
    print("Starting one all-user poll. This can take several minutes; no automatic retries.", flush=True)
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        try:
            detail = json.loads(error.read()).get("detail", "Request rejected")
        except (ValueError, AttributeError):
            detail = "Request rejected"
        raise SystemExit(f"HTTP {error.code}: {detail}. Check server logs before retrying.") from None
    except (urllib.error.URLError, TimeoutError):
        raise SystemExit("No completion response received. The server may still be processing; check logs before retrying.") from None
    print(f"Poll response: {result.get('status', 'unknown')}; accounts checked: {result.get('accounts_polled', 'unknown')}.")
    print("Check provider warnings in Render logs; a completed poll does not prove every provider request succeeded.")


if __name__ == "__main__":
    main()
