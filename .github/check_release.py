"""T-0067: fail the release when the tag, pyproject.toml's version and the agents' manifests' versions differ.

Usage, from the repository root: python .github/check_release.py v0.1.0
"""

import json
import sys
import tomllib
from pathlib import Path

# Claude Code's plugin, the Agent Plugins manifest (Codex, Copilot, Cursor), Gemini CLI's extension (T-0078).
MANIFESTS = (".claude-plugin/plugin.json", "plugin.json", "gemini-extension.json")


def mismatch(tag: str, root: Path = Path(".")) -> str | None:
    """Why the tag, pyproject.toml and the manifests disagree, or None when they agree."""
    package = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    versions = {m: json.loads((root / m).read_text(encoding="utf-8"))["version"] for m in MANIFESTS}
    if tag == f"v{package}" and set(versions.values()) == {package}:
        return None
    named = ", ".join(f"{m}'s {v}" for m, v in versions.items())
    return f"the tag {tag}, pyproject.toml's version {package} and the manifests' versions ({named}) differ"


if __name__ == "__main__":
    tag = sys.argv[1]
    if error := mismatch(tag):
        sys.exit(error)
    print(f"{tag}: pyproject.toml and the manifests agree")
