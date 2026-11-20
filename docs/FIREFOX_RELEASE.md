# Firefox release 1.0.6

## Reproduce the package

Prerequisites: Node.js 22 with npm, Python 3. No environment variables or secrets are needed.
From the repository root (or extracted source archive root):

```sh
npm ci --prefix extension
python3 extension/scripts/package_firefox.py ./firefox-output
```

Outputs: `leetstreak-firefox-1.0.6.zip` (runtime package) and
`leetstreak-firefox-1.0.6-sources.zip` (unminified source for Mozilla review).
ZIP timestamps may differ between builds. The script builds directly from source,
without modifying Chrome manifests, bundles, dist directories, or release archives.

## Firefox-specific changes

- MV3 nonpersistent background script instead of Chrome's service worker.
- Firefox 140+ on desktop, with built-in installation consent for account identifiers,
  authentication information, imported question content, and solve activity.
- Native Firefox promise APIs for background storage and optional website access.
- Removed localhost host access from this production package.
- The existing Gecko extension ID is retained; it is a public identifier, not a login.
- Uses the same production API and account data as Chrome.

## Submit and install

Upload the runtime ZIP to https://addons.mozilla.org/developers/ and select a public
listing. Upload the sources ZIP when requested, pointing reviewers to these build
instructions. Supply the existing privacy policy and reviewer credentials privately
in Mozilla's reviewer notes; do not add credentials to either ZIP or the repository.

The ZIP is unsigned. Normal permanent installation requires Mozilla signing.
For local evaluation, extract it, open `about:debugging#/runtime/this-firefox`, select
**Load Temporary Add-on**, and choose the extracted `manifest.json`.
Temporary installs disappear after restarting Firefox.

The package has not yet been exercised in a running Firefox browser or approved by
Mozilla. Before public release, check login, manual Sync, group switching, profile
details, study-plan persistence, optional import permissions, and LeetCode history
access in Firefox. Chrome publication and deployment do not publish a Firefox build.

References:
- https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/background
- https://extensionworkshop.com/documentation/develop/firefox-builtin-data-consent/
- https://extensionworkshop.com/documentation/publish/submitting-an-add-on/
