"""Build Firefox artifacts without writing to the Chrome build or ZIPs.

Usage: python3 extension/scripts/package_firefox.py [output-directory]
Prerequisites: Python 3, Node.js, and `npm ci --prefix extension`.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
EXTENSION = ROOT / "extension"
OUTPUT = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path.home() / "Downloads"


def archive(destination, files):
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path, name in sorted(files, key=lambda item: item[1]):
            bundle.write(path, name)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((EXTENSION / "manifest.json").read_text())
    version = manifest["version"]
    manifest["background"] = {"scripts": ["background.js"], "persistent": False}
    manifest["browser_specific_settings"] = {"gecko": {
        "id": "leetstreak@example.com",
        "strict_min_version": "140.0",
        "data_collection_permissions": {"required": [
            "personallyIdentifyingInfo", "authenticationInfo", "websiteContent", "websiteActivity"
        ]},
    }}
    manifest["host_permissions"] = [
        origin for origin in manifest["host_permissions"] if "localhost" not in origin
    ]
    with tempfile.TemporaryDirectory(prefix="leetstreak-firefox-") as temp:
        stage = Path(temp)
        # Include only public runtime assets, never arbitrary workspace files.
        for asset in (EXTENSION / "public").iterdir():
            if asset.is_file() and asset.suffix.lower() in {".png", ".svg", ".jpg", ".jpeg", ".woff2"}:
                shutil.copyfile(asset, stage / asset.name)
        for name in ("history-bridge.js", "leetcode-listener.js"):
            shutil.copyfile(EXTENSION / "public" / name, stage / name)
        background = (EXTENSION / "public/background.js").read_text()
        # Firefox's native promise API handles the background's awaited storage calls.
        background = background.replace("chrome.storage.local", "browser.storage.local")
        (stage / "background.js").write_text(background)
        (stage / "index.html").write_bytes((EXTENSION / "index.html").read_bytes())
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        subprocess.run([
            str(EXTENSION / "node_modules/.bin/esbuild"), "src/main.tsx", "--bundle",
            f"--outfile={stage / 'index-main.js'}", "--loader:.tsx=tsx", "--loader:.ts=ts",
            "--loader:.css=css", "--jsx=automatic", "--minify",
            # Callback-based calls keep using Firefox's Chrome compatibility API.
            "--define:chrome.permissions.request=browser.permissions.request",
        ], cwd=EXTENSION, check=True)
        package = OUTPUT / f"leetstreak-firefox-{version}.zip"
        archive(package, [(p, p.relative_to(stage).as_posix()) for p in stage.rglob("*") if p.is_file()])

    # Explicit source allowlist: no backend, credentials, audit evidence, or node_modules.
    sources = []
    for directory in (EXTENSION / "src", ROOT / "shared", EXTENSION / "scripts"):
        sources.extend((p, p.relative_to(ROOT).as_posix()) for p in directory.rglob("*")
                       if p.is_file() and p.suffix in {".ts", ".tsx", ".css", ".json", ".py"})
    for name in ("manifest.json", "index.html", "package.json", "package-lock.json", "tsconfig.json"):
        p = EXTENSION / name
        sources.append((p, p.relative_to(ROOT).as_posix()))
    for p in (EXTENSION / "public").iterdir():
        if p.is_file() and p.name not in {"index-main.js", "index-main.css", "index.html", "manifest.json"}:
            if p.suffix.lower() in {".js", ".png", ".svg", ".jpg", ".jpeg", ".woff2"}:
                sources.append((p, p.relative_to(ROOT).as_posix()))
    instructions = ROOT / "docs/FIREFOX_RELEASE.md"
    sources.append((instructions, "docs/FIREFOX_RELEASE.md"))
    source_package = OUTPUT / f"leetstreak-firefox-{version}-sources.zip"
    archive(source_package, sources)
    print(f"Firefox package: {package}\nMozilla review sources: {source_package}")


if __name__ == "__main__":
    main()
