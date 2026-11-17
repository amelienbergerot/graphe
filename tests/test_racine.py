"""T-0003 : la racine de l'hote est le depot git courant, pas l'emplacement de l'outil."""

from __future__ import annotations

import subprocess
from pathlib import Path

import graphe_racine


def test_la_racine_est_le_depot_git_du_repertoire_courant(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("GRAPHE_RACINE", raising=False)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "a" / "b").mkdir(parents=True)
    monkeypatch.chdir(tmp_path / "a" / "b")
    assert graphe_racine.racine() == tmp_path.resolve()
    monkeypatch.setenv("GRAPHE_RACINE", str(tmp_path / "a"))  # l'arbre fige du test de reference
    assert graphe_racine.racine() == (tmp_path / "a").resolve()
