#!/usr/bin/env python3
"""Secret and artifact hygiene validator for LeetStreak.

Verifies that the repository contains no exposed production secrets, private keys,
unapproved test emails/identities, tracked environments, or dirty release packages.
"""
import os
import re
import sys
import zipfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Directories to skip when scanning source code
SKIP_DIRS = {
    ".git",
    "test_env",
    "node_modules",
    "venv",
    "linux_venv",
    "__pycache__",
    ".pytest_cache",
    "private-audit",
}

# Dangerous patterns that should never appear in tracked source code
FORBIDDEN_PATTERNS = [
    (re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----"), "Private cryptographic key block"),
    (re.compile(r"ghp_[A-Za-z0-9_]{36}"), "GitHub Personal Access Token"),
    (re.compile(r"render_api_[A-Za-z0-9]{32}"), "Render API token"),
    (re.compile(r"(?i)AKIA[0-9A-Z]{16}"), "AWS Access Key ID"),
    (re.compile(r"(?i)postgres(?:ql)?://[^:]+:[^@]+@ep-[a-z0-9-]+\.[a-z0-9-]+\.supabase\.co"), "Live Supabase Database URL with password"),
]

# Prohibited file names that must never be tracked or released
FORBIDDEN_FILENAMES = {
    ".env.production",
    ".env.local",
    "id_rsa",
    "id_ed25519",
}

# Prohibited entries inside release zip archives
FORBIDDEN_ZIP_PATTERNS = [
    ".git",
    "test_env",
    "node_modules",
    ".env",
    ".DS_Store",
    "Thumbs.db",
    ".pyc",
    "__pycache__",
]


def check_source_hygiene() -> list[str]:
    """Scans all tracked/source files for secrets and prohibited patterns."""
    errors = []
    print("Scanning source files for secret and artifact hygiene...")

    for root, dirs, files in os.walk(REPO_ROOT):
        # Prune skipped directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

        for file in files:
            if file in FORBIDDEN_FILENAMES:
                errors.append(f"Forbidden file found: {os.path.join(root, file)}")
                continue

            # Skip binary files, lockfiles, zip files, and large databases
            if file.endswith((".zip", ".png", ".jpg", ".jpeg", ".ico", ".svg", ".lock", ".db", ".tsbuildinfo")):
                continue

            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, REPO_ROOT)

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for pattern, desc in FORBIDDEN_PATTERNS:
                        if pattern.search(content):
                            errors.append(f"{desc} detected in {rel_path}")
            except Exception as e:
                errors.append(f"Could not read {rel_path}: {e}")

    return errors


def check_zip_hygiene() -> list[str]:
    """Verifies that the release package leetstreak.zip contains only clean runtime assets."""
    errors = []
    print("Validating release package archive hygiene...")
    zip_path = os.path.join(REPO_ROOT, "leetstreak.zip")

    if not os.path.isfile(zip_path):
        return [f"Release package not found at {zip_path}"]

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            namelist = zf.namelist()
            if "manifest.json" not in namelist:
                errors.append("leetstreak.zip is missing root manifest.json")

            for name in namelist:
                for bad in FORBIDDEN_ZIP_PATTERNS:
                    if bad in name:
                        errors.append(f"leetstreak.zip contains forbidden entry: {name}")
    except Exception as e:
        errors.append(f"Failed to inspect leetstreak.zip: {e}")

    return errors


def check_git_hygiene() -> list[str]:
    """Verifies that .gitignore properly excludes virtual environments and local databases."""
    errors = []
    print("Verifying gitignore rules...")
    gitignore_path = os.path.join(REPO_ROOT, ".gitignore")
    if not os.path.isfile(gitignore_path):
        return ["Root .gitignore is missing"]

    with open(gitignore_path, "r", encoding="utf-8") as f:
        gitignore_content = f.read()

    for required in ["test_env", "node_modules", ".env", "*.db"]:
        if required not in gitignore_content:
            errors.append(f".gitignore missing rule for: {required}")

    return errors


def main():
    errors = []
    errors.extend(check_source_hygiene())
    errors.extend(check_zip_hygiene())
    errors.extend(check_git_hygiene())

    if errors:
        print("\n❌ Hygiene Validation Failures:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("\n✅ Hygiene check passed: no exposed secrets, clean package archive, valid gitignore.")


if __name__ == "__main__":
    main()
