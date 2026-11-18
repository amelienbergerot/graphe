"""The host's PHP in the code graph.

A rough reader, by patterns, like the GDScript one:
- a node per file, one per function (`function lire(`);
- in an entry point with actions (`switch ($action)`), a node per
  `case 'x':` - kind « action »; two `case` in a row share a body: the
  first leads to the second, which bears it;
- the calls between our functions, by their name; those outside any body (a router at the top of the file,
  T-0023) are the file's.

What sends to these actions, from another language, falls to a local
extension of the host (T-0009).
"""

from __future__ import annotations

import re
from pathlib import Path

from graphe_core import extent, lines_without_comments
import graphe_root
from graphe_root import ROOT

FUNCTION = re.compile(r"^function\s+(\w+)\s*\(")
ACTION = re.compile(r"^\s*case\s+'(\w+)'\s*:\s*$")
CALL = re.compile(r"\b(\w+)\s*\(")


def files(root: Path = ROOT) -> list[Path]:
    return graphe_root.files(".php", root)


def _id(path: Path, root: Path) -> str:
    return re.sub(r"\W", "_", path.relative_to(root).with_suffix("").as_posix()).lower()


def contribute(project) -> dict:
    """The PHP reader's contribution (docs/contribution.md): neither classified calls, nor sites."""
    reader = Reader(project.files(".php"), project.root)
    return {"nodes": reader.nodes, "links": reader.links}


def action_id(file_id: str, action: str) -> str:
    return f"{file_id}_action_{action.lower()}"


class Reader:
    def __init__(self, paths: list[Path] | None = None, root: Path = ROOT) -> None:
        self.nodes: list[dict] = []
        self.links: list[dict] = []
        defined: dict[str, str] = {}
        bodies: list[tuple[str, str, int, list[str]]] = []  # (id, file, line, lines of the body)
        for path in files(root) if paths is None else paths:
            rel = path.relative_to(root).as_posix()
            fid = _id(path, root)
            lines = path.read_bytes().decode("utf-8", "replace").splitlines()
            self._node(fid, path.name, "file", rel, 1, rel)
            previous = ""  # an action without a body, which leads to the next one
            covered: set[int] = set()  # the lines of the bodies, signatures included
            for i, line in enumerate(lines, start=1):
                f, a = FUNCTION.match(line), ACTION.match(line)
                if not (f or a):
                    continue
                if f:
                    nid = f"{fid}_{f.group(1).lower()}"
                    defined[f.group(1)] = nid
                    self._node(nid, f"{f.group(1)}()", "function", rel, i, f.group(1))
                else:
                    nid = action_id(fid, a.group(1))
                    self._node(nid, a.group(1), "action", rel, i, a.group(1))
                    if previous:
                        self._link(previous, nid, "dispatches", rel, i)
                self._link(fid, nid, "contains", rel, i)
                end = extent(lines, i)
                previous = nid if a and end == i else ""
                bodies.append((nid, rel, i, lines_without_comments(lines[i:end])))
                covered.update(range(i, end + 1))
            top = [text for k, text in enumerate(lines, start=1) if k not in covered]
            bodies.append((fid, rel, 1, lines_without_comments(top)))
        for nid, rel, i, body_lines in bodies:
            seen = set()
            for text in body_lines:
                for m in CALL.finditer(text):
                    target = defined.get(m.group(1))
                    if target and target != nid and target not in seen:
                        seen.add(target)
                        self._link(nid, target, "calls", rel, i)

    def _node(self, nid: str, label: str, kind: str, rel: str, line: int, name: str) -> None:
        self.nodes.append({"id": nid, "label": label, "kind": kind, "source_file": rel,
                           "source_location": f"L{line}", "name": name})

    def _link(self, source: str, target: str, relation: str, rel: str, line: int) -> None:
        self.links.append({"source": source, "target": target, "relation": relation, "confidence": "EXTRACTED",
                           "source_file": rel, "source_location": f"L{line}", "context": ""})
