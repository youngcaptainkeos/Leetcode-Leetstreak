#!/usr/bin/env python3
"""Release synchronization and artifact verification tool for LeetStreak.

Ensures that versions across metadata, extension manifest, package.json files,
and all 4 distributed zip copies are 100% consistent and byte-identical.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
METADATA_PATH = os.path.join(REPO_ROOT, "backend", "app", "release_metadata.py")
MANIFEST_PATH = os.path.join(REPO_ROOT, "extension", "manifest.json")
EXT_PACKAGE_PATH = os.path.join(REPO_ROOT, "extension", "package.json")
WEB_PACKAGE_PATH = os.path.join(REPO_ROOT, "web", "package.json")

ZIP_COPIES = [
    os.path.join(REPO_ROOT, "leetstreak.zip"),
    os.path.join(REPO_ROOT, "leetstreak_dist.zip"),
    os.path.join(REPO_ROOT, "extension", "leetstreak.zip"),
    os.path.join(REPO_ROOT, "backend", "app", "leetstreak.zip"),
]


def extract_metadata_version() -> str:
    """Reads SEMANTIC_VERSION from release_metadata.py."""
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("SEMANTIC_VERSION ="):
                return line.split("=")[1].strip().strip('"').strip("'")
    raise ValueError(f"Could not find SEMANTIC_VERSION in {METADATA_PATH}")


def read_json_version(path: str) -> str:
    """Reads version property from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("version", "")


def write_json_version(path: str, version: str) -> None:
    """Updates version property in a JSON file while preserving indent."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["version"] = version
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def compute_file_hash(path: str) -> tuple[str, str, int]:
    """Computes (sha256, md5, size_bytes) for a file."""
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
            md5.update(chunk)
    return sha256.hexdigest(), md5.hexdigest(), size


def sync_versions(target_version: str) -> None:
    """Synchronizes target_version into manifest.json and package.json files."""
    print(f"Synchronizing version {target_version} to manifests and packages...")
    write_json_version(MANIFEST_PATH, target_version)
    write_json_version(EXT_PACKAGE_PATH, target_version)
    write_json_version(WEB_PACKAGE_PATH, target_version)
    print("Version sync complete.")


def package_extension() -> None:
    """Builds the extension and packages dist into the 4 mirrored zip copies."""
    print("Building extension...")
    subprocess.check_call(["npm", "--prefix", "extension", "run", "build"], cwd=REPO_ROOT)

    dist_dir = os.path.join(REPO_ROOT, "extension", "dist")
    if not os.path.isdir(dist_dir):
        raise RuntimeError(f"dist directory not found at {dist_dir}")

    manifest_in_dist = os.path.join(dist_dir, "manifest.json")
    if not os.path.isfile(manifest_in_dist):
        raise RuntimeError(f"manifest.json missing from dist at {manifest_in_dist}")

    primary_zip = ZIP_COPIES[0]
    print(f"Packaging {primary_zip} from {dist_dir}...")
    with zipfile.ZipFile(primary_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(dist_dir):
            for file in sorted(files):
                abs_file = os.path.join(root, file)
                rel_path = os.path.relpath(abs_file, dist_dir)
                zf.write(abs_file, arcname=rel_path)

    sha256, md5, size = compute_file_hash(primary_zip)
    print(f"Primary zip created: {size} bytes, SHA256={sha256[:16]}..., MD5={md5}")

    for copy_path in ZIP_COPIES[1:]:
        print(f"Mirroring to {os.path.relpath(copy_path, REPO_ROOT)}...")
        os.makedirs(os.path.dirname(copy_path), exist_ok=True)
        shutil.copy2(primary_zip, copy_path)

    print("All 4 ZIP packages synchronized successfully.")


def verify_all() -> bool:
    """Verifies all versions and zip copies agree."""
    canonical_version = extract_metadata_version()
    print(f"Authoritative Canonical Version: {canonical_version}")

    errors = []

    # 1. Verify JSON file versions
    for name, path in [
        ("extension/manifest.json", MANIFEST_PATH),
        ("extension/package.json", EXT_PACKAGE_PATH),
        ("web/package.json", WEB_PACKAGE_PATH),
    ]:
        v = read_json_version(path)
        if v != canonical_version:
            errors.append(f"Version mismatch in {name}: found '{v}', expected '{canonical_version}'")
        else:
            print(f"  [OK] {name}: {v}")

    # 2. Verify all 4 zip copies exist and are byte-identical
    zip_hashes = []
    for copy_path in ZIP_COPIES:
        rel = os.path.relpath(copy_path, REPO_ROOT)
        if not os.path.isfile(copy_path):
            errors.append(f"Missing ZIP archive: {rel}")
            continue
        sha256, md5, size = compute_file_hash(copy_path)
        zip_hashes.append((rel, sha256, md5, size))

    if zip_hashes:
        first_rel, first_sha, first_md5, first_size = zip_hashes[0]
        print(f"  [OK] Primary archive {first_rel}: {first_size} bytes, MD5={first_md5}")
        for rel, sha, md5, size in zip_hashes[1:]:
            if sha != first_sha or md5 != first_md5 or size != first_size:
                errors.append(f"ZIP divergence: {rel} ({md5}, {size}B) differs from {first_rel} ({first_md5}, {first_size}B)")
            else:
                print(f"  [OK] Byte-identical mirror: {rel}")

        # 3. Verify manifest.json exists inside the primary zip and matches canonical version
        try:
            with zipfile.ZipFile(ZIP_COPIES[0], "r") as zf:
                if "manifest.json" not in zf.namelist():
                    errors.append(f"Root manifest.json missing inside {first_rel}")
                else:
                    manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
                    zip_manifest_v = manifest_data.get("version")
                    if zip_manifest_v != canonical_version:
                        errors.append(
                            f"Version mismatch inside {first_rel} manifest.json: found '{zip_manifest_v}', expected '{canonical_version}'"
                        )
                    else:
                        print(f"  [OK] manifest.json inside {first_rel} contains version {zip_manifest_v}")
        except Exception as e:
            errors.append(f"Could not inspect {first_rel}: {e}")

    if errors:
        print("\nVerification Failures:")
        for err in errors:
            print(f"  ❌ {err}")
        return False

    print("\n✅ All release metadata, manifests, and artifact copies are 100% verified!")
    return True


def main():
    parser = argparse.ArgumentParser(description="LeetStreak Release Synchronization Tool")
    parser.add_argument("--sync", action="store_true", help="Sync metadata version to manifests and packages")
    parser.add_argument("--package", action="store_true", help="Build extension and mirror all 4 zip archives")
    parser.add_argument("--verify", action="store_true", help="Verify all versions and zip copies agree")

    args = parser.parse_args()

    if not (args.sync or args.package or args.verify):
        args.verify = True

    canonical_version = extract_metadata_version()

    if args.sync:
        sync_versions(canonical_version)

    if args.package:
        package_extension()

    if args.verify:
        success = verify_all()
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
