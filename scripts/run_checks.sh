#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Default test environment
PYTHON="${PYTHON:-python3}"
if [ -f "$REPO_ROOT/test_env/bin/python" ]; then
    PYTHON="$REPO_ROOT/test_env/bin/python"
fi

export PYTHONPATH="backend:backend/tests"
export JWT_SECRET="${JWT_SECRET:-test-secret-value-for-ci-and-testing-only-12345}"

echo "=========================================================="
echo "🚀 LeetStreak Continuous Verification Suite"
echo "=========================================================="

echo -e "\n[1/7] Secret and Artifact Hygiene..."
"$PYTHON" scripts/check_hygiene.py

echo -e "\n[2/7] TypeScript Check (Website)..."
npm --prefix web run check

echo -e "\n[3/7] Client Unit Tests..."
node --test extension/tests/*.test.mjs

echo -e "\n[4/7] Build Website & Package Extension..."
npm --prefix web run build
"$PYTHON" scripts/sync_release.py --package

echo -e "\n[5/7] Release Consistency & Checksums..."
"$PYTHON" scripts/sync_release.py --verify

echo -e "\n[6/7] Backend Unit Tests (125 tests)..."
"$PYTHON" -m unittest discover -s backend/tests -p "test_*.py"

# Optional: PostgreSQL tests if configured
if [ -z "${LEETSTREAK_TEST_POSTGRES_URL:-}" ] && [ -f "$REPO_ROOT/private-audit/m1-postgres-config.json" ]; then
    LEETSTREAK_TEST_POSTGRES_URL="$(grep -o '"url": *"[^"]*"' "$REPO_ROOT/private-audit/m1-postgres-config.json" | cut -d'"' -f4)"
fi

if [ -n "${LEETSTREAK_TEST_POSTGRES_URL:-}" ]; then
    echo -e "\n[7/7] Native PostgreSQL Migration Checks..."
    LEETSTREAK_TEST_POSTGRES_URL="$LEETSTREAK_TEST_POSTGRES_URL" "$PYTHON" -m unittest backend/tests/test_postgres_migrations.py
else
    echo -e "\n[7/7] Native PostgreSQL Tests: SKIPPED (LEETSTREAK_TEST_POSTGRES_URL not set)"
fi

# Optional: Browser smoke test
CHROME_BIN="${LEETSTREAK_CHROME_EXECUTABLE:-/opt/google/chrome/chrome}"
if [ -x "$CHROME_BIN" ] && [ -f "$REPO_ROOT/backend/tests/browser_smoke.py" ]; then
    echo -e "\n[Bonus] Headless Chrome Browser Smoke Test..."
    LEETSTREAK_CHROME_EXECUTABLE="$CHROME_BIN" "$PYTHON" backend/tests/browser_smoke.py
fi

echo -e "\n=========================================================="
echo "🎉 ALL CONTINUOUS CHECKS PASSED SUCCESSFULLY!"
echo "=========================================================="
