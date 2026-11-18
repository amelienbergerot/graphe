"""La racine du projet hote (T-0003) et ses fichiers (T-0004).

La racine : GRAPHE_ROOT, sinon le depot git du repertoire courant, sinon ce
repertoire. GRAPHE_ROOT sert au test de reference d'un hote (son arbre
fige), et aux tests de l'outil.

Les fichiers : ceux que git suit, plus les non suivis non ignores, moins ceux
que `exclude` (graphe.toml, a la racine, facultatif) designe. Chacun va au
lecteur de son extension ; un fichier qu'aucun lecteur ne prend est ignore.

Un programme externe qu'un lecteur lance (T-0005) : la cle `executable` de la
section du lecteur (`[godot]`), relative a la racine ; sinon le PATH ; sinon
rien, avec un avertissement qui nomme la cle.

Les autres cles de graphe.toml (T-0009) : `displayed_text`, le motif de
l'appel qui affiche un texte, et `[documents]`, `patterns` et `identifier`
(T-0010, graphe_enrichir) ; `[communities]`, `separate` et
`strip_prefixes` (graphe.py) ; `[[extensions]]` (docs/contribution.md).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path, PurePosixPath

def racine() -> Path:
    if os.environ.get("GRAPHE_ROOT"):
        return Path(os.environ["GRAPHE_ROOT"]).resolve()
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip()).resolve()
    except (OSError, subprocess.SubprocessError):
        pass
    return Path.cwd().resolve()


RACINE = racine()
SORTIE = RACINE / "graphe"  # la sortie : jamais lue
CONFIGURATION = "graphe.toml"


def configuration(racine: Path = RACINE) -> dict:
    chemin = racine / CONFIGURATION
    return tomllib.loads(chemin.read_text(encoding="utf-8")) if chemin.is_file() else {}


def designe(rel: str, motifs: list[str]) -> bool:
    """Vrai si un des motifs designe `rel` : `build`, le dossier build/ de la racine ; `**/tests`, tout dossier tests/.
    Sert a `exclude` et a `[documents] patterns`."""
    p = PurePosixPath(rel)
    return any(p.full_match(m) or p.full_match(f"{m}/**") for m in motifs)


def fichiers(suffixe: str, racine: Path = RACINE) -> list[Path]:
    """Les fichiers de l'hote qui finissent par `suffixe` (`.py`), tries."""
    r = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=racine,
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    if r.returncode:
        raise RuntimeError(f"{racine} is not a git repository: graphe reads the files git tracks\n{r.stderr}")
    motifs = [SORTIE.name, *configuration(racine).get("exclude", [])]
    # Des Path tries, comme l'ancien rglob : l'ordre de lecture ne change pas.
    return sorted(racine / rel for rel in set(r.stdout.split("\0"))
                  if rel.endswith(suffixe) and not designe(rel, motifs) and (racine / rel).is_file())


def executable(section: str, nom: str, racine: Path = RACINE) -> Path | None:
    """Le programme `nom` d'un lecteur : `[section] executable` du graphe.toml, sinon le PATH, sinon None."""
    donne = configuration(racine).get(section, {}).get("executable")
    if donne:
        if (chemin := racine / donne).is_file():  # un chemin absolu reste absolu
            return chemin
        print(f"graphe: {chemin} not found ([{section}] executable, {CONFIGURATION})", file=sys.stderr)
    if trouve := shutil.which(nom):
        return Path(trouve)
    print(f"graphe: {nom} not found, neither by [{section}] executable in {CONFIGURATION} nor in the PATH:"
          f" the reader goes on without it", file=sys.stderr)
    return None
