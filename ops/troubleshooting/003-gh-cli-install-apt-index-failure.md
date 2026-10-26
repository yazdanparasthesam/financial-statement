# Troubleshooting episode 003 — GitHub CLI install via APT did not complete

**Date:** 2026-10-26\
**Status:** direct verified-package installation requested; not yet confirmed.\
**Evidence handling:** terminal output was supplied as text; no failure screenshot retained.

## What happened

The official GitHub CLI keyring download completed, and the APT source/keyring files were written. The subsequent package-index refresh did not complete and was interrupted by the owner. Therefore `gh` is not installed yet. No authentication or issue creation has occurred.

The owner reports Ubuntu Jammy, Python 3.10.12, and PyYAML 6.0.3. The tracker importer's nested-quote f-string in the current local copy is not compatible with Python 3.10; fix that before invoking the non-dry-run importer. The final workspace bundle has a compatible implementation and correctly marks issues 008–013 open.

## Safe next step

Use the official GitHub CLI v2.103.2 amd64 `.deb` release asset directly, verify SHA-256 against the published release checksum, then install it with `dpkg`. Do not retry a full package-index refresh as part of this step. Official release page: <https://github.com/cli/cli/releases>.

Expected asset:

- `gh_2.103.2_linux_amd64.deb`
- SHA-256: `30463d8e1fdce73f178f76b0082b7ab0657b0740b87274890e831def647ca979`

If the architecture is not `amd64`, stop and select the matching official release asset. If `dpkg -i` reports missing dependencies, stop and report the exact error; do not attempt package changes blindly.
