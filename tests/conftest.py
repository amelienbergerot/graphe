"""Les tests marques `grid_zero` lisent le vrai Grid Zero, a cote de ce depot.

Les lecteurs fixent leur racine a l'import : GRAPHE_ROOT est pose avant.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

GRID_ZERO = Path(__file__).resolve().parents[2] / "grid_zero"
os.environ.setdefault("GRAPHE_ROOT", str(GRID_ZERO))

grid_zero = pytest.mark.skipif(not (GRID_ZERO / "simulation").is_dir(), reason=f"{GRID_ZERO} absent")
