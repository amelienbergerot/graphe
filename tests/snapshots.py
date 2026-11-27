"""T-0072: the snapshots of the sample hosts' links. `python tests/snapshots.py` rewrites them all.

Each folder of `tests/fixtures/` is a sample host, built as a real host is: copied into a fresh git repository,
then `graphe build`. Its snapshot, `tests/fixtures/<host>.links`, holds one line per link and relation, sorted:
`source relation target sure|by name`.
"""

from __future__ import annotations

import difflib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def hosts() -> list[Path]:
    return sorted(p for p in FIXTURES.iterdir() if p.is_dir())


def _snapshot(host: Path) -> Path:
    return FIXTURES / f"{host.name}.links"


def committed(host: Path) -> str:
    path = _snapshot(host)
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def links(host: Path, work: Path) -> str:
    """The host's links once built, in `work` (an empty folder), one line per relation."""
    built = work / host.name
    shutil.copytree(host, built)
    subprocess.run(["git", "init", "-q", str(built)], check=True)
    subprocess.run(["git", "add", "-A"], cwd=built, check=True)
    # The root is fixed at import: a separate process. A PATH reduced to git: no Godot, whatever the machine.
    env = {**os.environ, "GRAPHE_ROOT": str(built), "PATH": str(Path(shutil.which("git")).parent)}
    r = subprocess.run([sys.executable, "-c", "import sys, graphe.cli; sys.exit(graphe.cli.main(sys.argv[1:]))",
                        "build", "--quiet"], cwd=built, env=env, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise RuntimeError(f"{host.name}: the build failed\n{r.stderr}")
    data = json.loads((built / "graphe" / "graphe.json").read_bytes())
    # shortcut: a link's locations and contexts (a keyed link's key) are not in the snapshot, so a link that moves
    # line passes; add them if a reader regresses on them.
    lines = sorted(f"{e['source']} {relation} {e['target']} {'sure' if e['confidence'] == 'EXTRACTED' else 'by name'}"
                   for e in data["links"] for relation in e["relations"])
    return "".join(f"{line}\n" for line in lines)


def difference(name: str, built: str, snapshot: str) -> str | None:
    """None when the built links are the snapshot; otherwise the lines that differ, under the host's name."""
    if built == snapshot:
        return None
    diff = [line for line in difflib.ndiff(snapshot.splitlines(), built.splitlines()) if line[:1] in "+-"]
    return (f"{name}: the links differ from {name}.links (- in the snapshot, + built); if the change is meant, "
            "run `python tests/snapshots.py` and give its reason in the commit\n" + "\n".join(diff))


def orphans() -> list[Path]:
    """The snapshots whose host folder is gone."""
    return sorted(p for p in FIXTURES.glob("*.links") if not (FIXTURES / p.stem).is_dir())


def main() -> int:
    for path in orphans():
        path.unlink()
        print(f"removed {path.name}")
    with tempfile.TemporaryDirectory() as work:
        for host in hosts():
            path = _snapshot(host)
            path.write_text(links(host, Path(work)), encoding="utf-8", newline="\n")
            print(path.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
