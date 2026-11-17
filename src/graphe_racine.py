"""La racine du projet hote (T-0003) et ses fichiers (T-0004).

La racine : GRAPHE_RACINE, sinon le depot git du repertoire courant, sinon ce
repertoire. GRAPHE_RACINE sert au test de reference de Grid Zero (son arbre
fige), et aux tests de l'outil.

Les fichiers : ceux que git suit, plus les non suivis non ignores, moins ceux
que `exclure` (graphe.toml, a la racine, facultatif) designe. Chacun va au
lecteur de son extension ; un fichier qu'aucun lecteur ne prend est ignore.
"""

from __future__ import annotations

import os
import subprocess
import tomllib
from pathlib import Path, PurePosixPath

def racine() -> Path:
    if os.environ.get("GRAPHE_RACINE"):
        return Path(os.environ["GRAPHE_RACINE"]).resolve()
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


def _exclu(rel: str, motifs: list[str]) -> bool:
    """`build` exclut le dossier build/ de la racine, `**/tests` tout dossier tests/."""
    p = PurePosixPath(rel)
    return any(p.full_match(m) or p.full_match(f"{m}/**") for m in motifs)


def fichiers(suffixe: str, racine: Path = RACINE) -> list[Path]:
    """Les fichiers de l'hote qui finissent par `suffixe` (`.py`), tries."""
    r = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=racine,
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    if r.returncode:
        raise RuntimeError(f"{racine} n'est pas un depot git : le graphe lit les fichiers que git suit\n{r.stderr}")
    motifs = [SORTIE.name, *configuration(racine).get("exclure", [])]
    # Des Path tries, comme l'ancien rglob : l'ordre de lecture ne change pas.
    return sorted(racine / rel for rel in set(r.stdout.split("\0"))
                  if rel.endswith(suffixe) and not _exclu(rel, motifs) and (racine / rel).is_file())
