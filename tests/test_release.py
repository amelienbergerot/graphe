"""T-0067: the release workflow stops before the upload when the tag, the package and the plugin differ."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CHECK = REPO / ".github" / "check_release.py"


def check(tag: str, root: Path = REPO) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(CHECK), tag], capture_output=True, text=True, cwd=root)


def test_the_tag_of_the_package_version_passes():
    assert check("v0.1.0").returncode == 0


def test_a_tag_other_than_the_package_version_fails_naming_both():
    result = check("v0.2.0")
    assert result.returncode != 0
    assert "v0.2.0" in result.stderr and "0.1.0" in result.stderr


def test_a_plugin_version_other_than_the_package_fails(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.1.0"\n', encoding="utf-8")
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "plugin.json").write_text('{"version": "0.0.9"}', encoding="utf-8")
    result = check("v0.1.0", tmp_path)
    assert result.returncode != 0
    assert "0.0.9" in result.stderr
