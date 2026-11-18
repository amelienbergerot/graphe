"""The tests marked `grid_zero` read the real Grid Zero, next to this repository.

The readers fix their root at import: GRAPHE_ROOT is set before.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

GRID_ZERO = Path(__file__).resolve().parents[2] / "grid_zero"
os.environ.setdefault("GRAPHE_ROOT", str(GRID_ZERO))

grid_zero = pytest.mark.skipif(not (GRID_ZERO / "simulation").is_dir(), reason=f"{GRID_ZERO} absent")
