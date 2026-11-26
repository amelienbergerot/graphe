"""T-0067: fail the release when the tag, pyproject.toml's version and the plugin's version differ.

Usage, from the repository root: python .github/check_release.py v0.1.0
"""

import json
import sys
import tomllib
from pathlib import Path


def mismatch(tag: str, root: Path = Path(".")) -> str | None:
    """Why the tag, pyproject.toml and plugin.json disagree, or None when they agree."""
    package = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    plugin = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    if tag == f"v{package}" and plugin == package:
        return None
    return f"the tag {tag}, pyproject.toml's version {package} and plugin.json's version {plugin} differ"


if __name__ == "__main__":
    tag = sys.argv[1]
    if error := mismatch(tag):
        sys.exit(error)
    print(f"{tag}: pyproject.toml and plugin.json agree")
