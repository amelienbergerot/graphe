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
    assert project["scripts"] == {"graphe": "graphe:main"}  # T-0084: the hook without graphe.cli's imports


def test_installing_the_plugin_installs_the_hook():
    """T-0077: hooks/hooks.json, the plugin's default hooks file (code.claude.com/docs/en/plugins-reference)."""
    hooks = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    [entry] = hooks["PreToolUse"]
    assert set(entry["matcher"].split("|")) == {"Grep", "Bash", "PowerShell"}
    [command] = entry["hooks"]
    # Exit 2 would block the tool: graphe 0.1.1 answers an unknown command with it. `; exit 0` holds in Git Bash and
    # PowerShell, the shells a command hook runs in.
    assert command["type"] == "command" and command["command"] == "graphe hook; exit 0" and "args" not in command


def test_every_agent_manifest_names_graphe_and_the_skills_folder_is_the_default():
    """T-0078: the Agent Plugins manifest (Codex, Copilot, Cursor) and Gemini CLI's extension, each found where its
    agent looks; every one discovers skills/ by default, so none names it. The versions: test_release."""
    portable = json.loads((REPO / "plugin.json").read_text(encoding="utf-8"))
    gemini = json.loads((REPO / "gemini-extension.json").read_text(encoding="utf-8"))
    codex = json.loads((REPO / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
    assert portable["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert portable["name"] == gemini["name"] == "graphe"
    # Copilot's reference (docs.github.com/en/copilot/reference/cli-plugin-reference) forbids component path fields
    assert "skills" not in portable and "hooks" not in portable
    [entry] = codex["plugins"]
    assert entry["name"] == "graphe" and entry["source"] == {"source": "local", "path": "./"}
    assert "version" not in entry


def test_the_skill_allows_the_graphe_command_for_its_turn():
    skill = (REPO / "skills" / "graphe" / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = skill.split("---")[1]
    assert "allowed-tools: Bash(graphe *) PowerShell(graphe *)" in frontmatter
