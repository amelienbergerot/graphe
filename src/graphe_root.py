"""The host project's root (T-0003) and its files (T-0004).

The root: GRAPHE_ROOT, else the git repository of the current directory,
else that directory. GRAPHE_ROOT serves a host's reference test (its frozen
tree), and the tool's tests.

The files: those git tracks, plus untracked files that are not ignored,
minus those that `exclude` (graphe.toml, at the root, optional) designates.
Each goes to the reader of its extension; a file no reader takes is ignored.

An external program a reader runs (T-0005): the `executable` key of the
reader's section (`[godot]`), relative to the root; else the PATH; else
nothing, with a warning that names the key.

The other keys of graphe.toml (T-0009): `displayed_text`, the pattern of the
call that displays a text, and `[documents]`, `patterns` and `identifier`
(T-0010, graphe_core); `[communities]`, `separate` and `strip_prefixes`
(graphe.py); `[[extensions]]` (docs/contribution.md).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path, PurePosixPath

def root() -> Path:
    if os.environ.get("GRAPHE_ROOT"):
        return Path(os.environ["GRAPHE_ROOT"]).resolve()
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip()).resolve()
    except (OSError, subprocess.SubprocessError):
        pass
    return Path.cwd().resolve()


ROOT = root()
OUTPUT = ROOT / "graphe"  # the output: never read
CONFIGURATION = "graphe.toml"


def configuration(root: Path = ROOT) -> dict:
    path = root / CONFIGURATION
    return tomllib.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def designates(rel: str, patterns: list[str]) -> bool:
    """True if one of the patterns designates `rel`: `build`, the build/ folder at the root; `**/tests`, any tests/
    folder. Serves `exclude` and `[documents] patterns`."""
    p = PurePosixPath(rel)
    return any(p.full_match(m) or p.full_match(f"{m}/**") for m in patterns)


def files(suffix: str, root: Path = ROOT) -> list[Path]:
    """The host's files that end with `suffix` (`.py`), sorted."""
    r = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root,
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    if r.returncode:
        raise RuntimeError(f"{root} is not a git repository: graphe reads the files git tracks\n{r.stderr}")
    patterns = [OUTPUT.name, *configuration(root).get("exclude", [])]
    # Sorted Paths, like the old rglob: the reading order does not change.
    return sorted(root / rel for rel in set(r.stdout.split("\0"))
                  if rel.endswith(suffix) and not designates(rel, patterns) and (root / rel).is_file())


def executable(section: str, name: str, root: Path = ROOT) -> Path | None:
    """A reader's program `name`: `[section] executable` of graphe.toml, else the PATH, else None."""
    given = configuration(root).get(section, {}).get("executable")
    if given:
        if (path := root / given).is_file():  # an absolute path stays absolute
            return path
        print(f"graphe: {path} not found ([{section}] executable, {CONFIGURATION})", file=sys.stderr)
    if found := shutil.which(name):
        return Path(found)
    print(f"graphe: {name} not found, neither by [{section}] executable in {CONFIGURATION} nor in the PATH:"
          f" the reader goes on without it", file=sys.stderr)
    return None
