"""Check that the release version is the same everywhere it is written.

A release carries one version number, written in four places:

- custom_components/growatt_thor_cloud/manifest.json: the integration's version, shown by
  Home Assistant and HACS. card.py also appends it to the Wallbox card's URL
  (`?v=<version>`), so browsers fetch the new card after an update.
- frontend/package.json: the card's version. The build embeds it in the card, which logs
  it in the browser console ("THOR-WALLBOX-CARD 0.8.2").
- frontend/package-lock.json: npm's copy of the same field (`npm version` updates both).
- CHANGELOG.md: the first "## <version>" heading, i.e. the notes of the latest release.

A release updates all four together. This test fails when one is left behind; its message
lists what each file says, so the stale one stands out.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Files whose top-level "version" field holds the release version.
JSON_FILES = (
    "custom_components/growatt_thor_cloud/manifest.json",
    "frontend/package.json",
    "frontend/package-lock.json",
)


def test_versions_match() -> None:
    """Every copy of the version equals the latest CHANGELOG entry."""
    # The first level-two heading of the changelog, e.g. "## 0.8.2".
    latest = re.search(r"^## (\S+)$", (ROOT / "CHANGELOG.md").read_text(), re.MULTILINE)
    assert latest, "CHANGELOG.md has no '## <version>' heading"

    versions = {path: json.loads((ROOT / path).read_text())["version"] for path in JSON_FILES}
    versions["CHANGELOG.md"] = latest.group(1)

    assert len(set(versions.values())) == 1, f"versions differ: {versions}"
