"""T-0064: the repository is its own Claude Code marketplace; the plugin carries the package's version."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_the_plugin_carries_the_package_version_and_the_marketplace_none():
    package = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    plugin = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    marketplace = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert plugin["name"] == "graphe"
    assert plugin["version"] == package
    [entry] = marketplace["plugins"]
    assert entry["name"] == "graphe" and entry["source"] == "."
    assert "version" not in entry and "version" not in marketplace.get("metadata", {})


def test_the_skill_allows_the_graphe_command_for_its_turn():
    skill = (REPO / "skills" / "graphe" / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = skill.split("---")[1]
    assert "allowed-tools: Bash(graphe *) PowerShell(graphe *)" in frontmatter
