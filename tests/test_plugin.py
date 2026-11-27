"""T-0064: the repository is its own Claude Code marketplace; the plugin carries the package's version."""

from __future__ import annotations

import importlib.util
import json
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("check_release", REPO / ".github" / "check_release.py")
check_release = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_release)  # the release workflow's check: one comparison of the versions


def test_the_plugin_carries_the_package_version_and_the_marketplace_none():
    package = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    plugin = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    marketplace = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert plugin["name"] == "graphe"
    assert check_release.mismatch(f"v{package}", REPO) is None
    [entry] = marketplace["plugins"]
    assert entry["name"] == "graphe" and entry["source"] == "."
    assert "version" not in entry and "version" not in marketplace.get("metadata", {})


def test_the_distribution_is_graphe_code_and_its_command_graphe():
    project = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["name"] == "graphe-code"
    assert project["scripts"] == {"graphe": "graphe.cli:main"}


def test_installing_the_plugin_installs_the_hook():
    """T-0077: hooks/hooks.json, the plugin's default hooks file (code.claude.com/docs/en/plugins-reference)."""
    hooks = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    [entry] = hooks["PreToolUse"]
    assert set(entry["matcher"].split("|")) == {"Grep", "Bash", "PowerShell"}
    [command] = entry["hooks"]
    assert command["type"] == "command" and command["command"] == "graphe hook"


def test_the_skill_allows_the_graphe_command_for_its_turn():
    skill = (REPO / "skills" / "graphe" / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = skill.split("---")[1]
    assert "allowed-tools: Bash(graphe *) PowerShell(graphe *)" in frontmatter
