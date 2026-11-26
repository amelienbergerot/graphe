"""T-0003: the host's root is the current git repository, not the tool's location."""

from __future__ import annotations

import subprocess
from pathlib import Path

from graphe import root


def test_the_root_is_the_git_repository_of_the_current_directory(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("GRAPHE_ROOT", raising=False)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "a" / "b").mkdir(parents=True)
    monkeypatch.chdir(tmp_path / "a" / "b")
    assert root.root() == tmp_path.resolve()
    monkeypatch.setenv("GRAPHE_ROOT", str(tmp_path / "a"))  # the frozen tree of the reference test
    assert root.root() == (tmp_path / "a").resolve()
