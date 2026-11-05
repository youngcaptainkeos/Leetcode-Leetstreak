import hashlib
import json
import os
import unittest
import zipfile

import test_access as fixtures
from app.main import app
from app.release_metadata import (
    SEMANTIC_VERSION,
    MIN_SUPPORTED_VERSION,
    RELEASE_NOTES,
    DOWNLOAD_URL,
    get_release_metadata,
    find_served_zip_path,
    compute_file_checksums,
)
from app.releases import RELEASE_NOTICES


class ReleaseMetadataTests(unittest.TestCase):
    setUp = fixtures.AccessTests.setUp
    tearDown = fixtures.AccessTests.tearDown
    headers = fixtures.AccessTests.headers

    def test_extension_version_endpoint_serves_canonical_metadata(self):
        response = self.client.get("/api/extension/version")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["latest_version"], SEMANTIC_VERSION)
        self.assertEqual(data["min_supported_version"], MIN_SUPPORTED_VERSION)
        self.assertEqual(data["download_url"], DOWNLOAD_URL)
        self.assertEqual(data["release_notes"], RELEASE_NOTES)
        self.assertIn("channel", data)
        self.assertIn("update_instructions", data)
        self.assertTrue(len(data.get("latest_commit", "")) >= 7)

        # Checksums validation
        checksums = data.get("checksums", {})
        self.assertEqual(checksums.get("filename"), "leetstreak.zip")
        self.assertEqual(len(checksums.get("sha256", "")), 64)
        self.assertEqual(len(checksums.get("md5", "")), 32)
        self.assertGreater(checksums.get("size_bytes", 0), 1000)

        # Checksum must match actual file on disk
        zip_path = find_served_zip_path()
        self.assertIsNotNone(zip_path)
        actual = compute_file_checksums(zip_path)
        self.assertEqual(checksums["sha256"], actual["sha256"])
        self.assertEqual(checksums["md5"], actual["md5"])
        self.assertEqual(checksums["size_bytes"], actual["size_bytes"])

    def test_app_config_endpoint_serves_canonical_version(self):
        response = self.client.get("/api/config/app")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["version"], SEMANTIC_VERSION)

    def test_updates_xml_endpoint_returns_410_gone(self):
        response = self.client.get("/api/extension/updates.xml")
        self.assertEqual(response.status_code, 410)
        self.assertIn("retired", response.json().get("detail", "").lower())

    def test_download_endpoint_serves_valid_zip(self):
        response = self.client.get("/downloads/leetstreak.zip")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), "application/zip")
        self.assertGreater(len(response.content), 1000)

        # Verify zip structure
        zip_path = find_served_zip_path()
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            self.assertIn("manifest.json", names)
            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
            self.assertEqual(manifest.get("version"), SEMANTIC_VERSION)

    def test_release_notices_registry(self):
        self.assertIn("integration-2026-11-05", RELEASE_NOTICES)
        self.assertIn(f"v{SEMANTIC_VERSION}", RELEASE_NOTICES)
        notice = RELEASE_NOTICES[f"v{SEMANTIC_VERSION}"]
        self.assertEqual(notice.notes, RELEASE_NOTES)
        self.assertEqual(notice.download_url, DOWNLOAD_URL)

    def test_all_four_zip_mirrors_are_byte_identical(self):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        zip_copies = [
            os.path.join(repo_root, "leetstreak.zip"),
            os.path.join(repo_root, "leetstreak_dist.zip"),
            os.path.join(repo_root, "extension", "leetstreak.zip"),
            os.path.join(repo_root, "backend", "app", "leetstreak.zip"),
        ]

        md5s = []
        for path in zip_copies:
            self.assertTrue(os.path.isfile(path), f"Missing zip copy at {path}")
            with open(path, "rb") as f:
                md5s.append(hashlib.md5(f.read()).hexdigest())

        # All 4 copies must have identical md5
        self.assertEqual(len(set(md5s)), 1, f"Zip mirrors diverged: {md5s}")

    def test_version_comparison_logic(self):
        """Simulates client-side version check algorithm."""
        def check_status(current_ver, latest_ver, min_ver):
            c_parts = [int(x) for x in current_ver.split(".")]
            l_parts = [int(x) for x in latest_ver.split(".")]
            m_parts = [int(x) for x in min_ver.split(".")]

            max_len_l = max(len(c_parts), len(l_parts))
            is_newer = False
            for i in range(max_len_l):
                c = c_parts[i] if i < len(c_parts) else 0
                l = l_parts[i] if i < len(l_parts) else 0
                if l > c:
                    is_newer = True
                    break
                if l < c:
                    is_newer = False
                    break

            max_len_m = max(len(c_parts), len(m_parts))
            is_unsupported = False
            for i in range(max_len_m):
                c = c_parts[i] if i < len(c_parts) else 0
                m = m_parts[i] if i < len(m_parts) else 0
                if m > c:
                    is_unsupported = True
                    break
                if m < c:
                    is_unsupported = False
                    break

            return is_newer, is_unsupported

        # Older client v1.0.0 with server at v1.1.0, min supported 1.0.0
        newer, unsupported = check_status("1.0.0", "1.1.0", "1.0.0")
        self.assertTrue(newer)
        self.assertFalse(unsupported)

        # Current client v1.1.0 with server at v1.1.0
        newer, unsupported = check_status("1.1.0", "1.1.0", "1.0.0")
        self.assertFalse(newer)
        self.assertFalse(unsupported)

        # Unsupported client v0.9.0 with server at v1.1.0, min supported 1.0.0
        newer, unsupported = check_status("0.9.0", "1.1.0", "1.0.0")
        self.assertTrue(newer)
        self.assertTrue(unsupported)

        # Future client v1.2.0 (e.g. dev build)
        newer, unsupported = check_status("1.2.0", "1.1.0", "1.0.0")
        self.assertFalse(newer)
        self.assertFalse(unsupported)
