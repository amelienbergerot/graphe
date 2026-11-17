"""T-0004 : la commande `graphe` sur un mini-projet hote temoin.

Les fichiers lus sont ceux que git suit, plus les non suivis non ignores,
chacun au lecteur de son extension ; `graphe.toml` exclut des dossiers.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

APPELANT = "from outils import aider\n\n\ndef travailler():\n    return aider()\n"
APPELE = "def aider():\n    return 1\n"


def _graphe(hote: Path, *arguments: str, env: dict | None = None) -> subprocess.CompletedProcess:
    # La racine est fixee a l'import : un processus a part, sur l'hote temoin (pas sur Grid Zero, cf. conftest).
    env = {**(env or os.environ), "GRAPHE_RACINE": str(hote)}
    return subprocess.run([sys.executable, "-c", "import sys, graphe; sys.exit(graphe.main(sys.argv[1:]))",
                           *arguments], cwd=hote, env=env, capture_output=True, text=True, encoding="utf-8")


def _hote(tmp_path: Path, fichiers: dict[str, str], suivi: str = "outils.py") -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for rel, texte in fichiers.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(texte, encoding="utf-8")
    subprocess.run(["git", "add", suivi], cwd=tmp_path, check=True)  # le reste n'est pas suivi
    return tmp_path


def _fichiers_lus(hote: Path) -> set[str]:
    donnees = json.loads((hote / "graphe" / "graphe.json").read_bytes())
    return {n["source_file"] for n in donnees["noeuds"]}


def test_un_hote_sans_configuration_se_construit_et_repond(tmp_path: Path):
    hote = _hote(tmp_path, {"outils.py": APPELE, "travail.py": APPELANT})
    r = _graphe(hote, "construire")
    assert r.returncode == 0, r.stderr
    assert _fichiers_lus(hote) == {"outils.py", "travail.py"}
    r = _graphe(hote, "expliquer", "aider")
    assert r.returncode == 0, r.stderr
    assert "travailler" in r.stdout


def test_graphe_toml_exclut_des_dossiers_et_les_fichiers_sans_lecteur_sont_ignores(tmp_path: Path):
    hote = _hote(tmp_path, {
        "outils.py": APPELE, "travail.py": APPELANT,
        "graphe.toml": 'exclure = ["**/tests", "brouillon"]\n',
        "paquet/tests/test_outils.py": APPELANT, "tests/test_travail.py": APPELANT,
        "brouillon/essai.py": APPELANT, "paquet/brouillon/garde.py": APPELE,  # brouillon/ de la racine seulement
        "donnees/mesures.xml": "<mesures/>\n",
        ".gitignore": "ignore.py\n", "ignore.py": APPELANT,
    })
    r = _graphe(hote, "construire")
    assert r.returncode == 0, r.stderr
    assert _fichiers_lus(hote) == {"outils.py", "travail.py", "paquet/brouillon/garde.py"}


# T-0005 : un programme externe (Godot, pour le lecteur GDScript) se cherche dans graphe.toml, puis le PATH.
SCRIPT_GD = "extends Node\n\n\nfunc _ready():\n\tadd_child(Node.new())\n"


def _sans_godot() -> dict:
    """Un PATH reduit a git : Godot n'y est pas, quelle que soit la machine."""
    return {**os.environ, "PATH": str(Path(shutil.which("git")).parent)}


def _moteur(hote: Path) -> int:
    donnees = json.loads((hote / "graphe" / "graphe.json").read_bytes())
    return donnees["couverture"]["godot"].get("moteur", 0)


def test_sans_godot_le_lecteur_gdscript_continue_et_nomme_la_cle(tmp_path: Path):
    hote = _hote(tmp_path, {"godot/main.gd": SCRIPT_GD}, suivi="godot/main.gd")
    r = _graphe(hote, "construire", env=_sans_godot())
    assert r.returncode == 0, r.stderr
    assert "[godot]" in r.stderr and "executable" in r.stderr
    assert _moteur(hote) == 0
    assert not (hote / "graphe" / "extension_api.json").exists()  # rien en cache : la cle servira au prochain coup


def test_avec_la_cle_les_appels_au_moteur_sont_resolus(tmp_path: Path):
    # Un faux Godot : il ecrit une API ou Node a add_child, la ou on le lance.
    # shortcut: un .cmd, Windows seulement (hors perimetre de T-0001) ; un script Python si l'outil sort de Windows.
    api = '{"classes":[{"name":"Node","methods":[{"name":"add_child"}]}],' \
          '"builtin_classes":[],"utility_functions":[],"singletons":[]}'
    hote = _hote(tmp_path, {"godot/main.gd": SCRIPT_GD, "outils/godot.cmd": f"@echo {api}> extension_api.json\n",
                            "graphe.toml": '[godot]\nexecutable = "outils/godot.cmd"\n'}, suivi="godot/main.gd")
    r = _graphe(hote, "construire", env=_sans_godot())
    assert r.returncode == 0, r.stderr
    assert "introuvable" not in r.stderr
    assert _moteur(hote) >= 1
