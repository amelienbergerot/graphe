"""La racine du projet hote (T-0003) : GRAPHE_RACINE, sinon le depot git du
repertoire courant, sinon ce repertoire.

GRAPHE_RACINE sert au test de reference de Grid Zero : son arbre fige n'est
pas un depot git, et git y trouverait un depot parent s'il en a un.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


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
