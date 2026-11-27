"""The readers and what they receive (docs/contribution.md), without networkx: a build where two readers have files
runs each in a process of its own, which imports this module and the readers, not the rest of graphe (T-0088)."""

from __future__ import annotations

import copy
import functools
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from graphe import generic, godot, js, python
from graphe import root as graphe_root
from graphe.root import ROOT

if TYPE_CHECKING:
    import networkx as nx

# Each reader under the name of its graphe.toml section: the key of its configuration and of its coverage.
READERS = {"python": python.contribute, "godot": godot.contribute, "js": js.contribute,
           "go": functools.partial(generic.contribute, generic.GO),
           "rust": functools.partial(generic.contribute, generic.RUST),
           "java": functools.partial(generic.contribute, generic.JVM),
           "c": functools.partial(generic.contribute, generic.C),
           "csharp": functools.partial(generic.contribute, generic.CSHARP),
           "ruby": functools.partial(generic.contribute, generic.RUBY),
           "swift": functools.partial(generic.contribute, generic.SWIFT),
           "php": functools.partial(generic.contribute, generic.PHP)}
# The suffixes each reader takes: which readers have files in a build.
SUFFIXES = {"python": (".py",), "godot": (".gd",), "js": tuple(js.PARSERS),
            **{name: tuple(r.args[0].grammars) for name, r in READERS.items() if isinstance(r, functools.partial)}}


class Project:
    """What `contribute(project)` receives: the root, the host's files, the configuration section of the one who
    contributes and the graph already assembled (a networkx graph, None for a reader's: still empty), copied on
    reading (docs/contribution.md)."""

    def __init__(self, configuration: dict, graph: nx.DiGraph | None, checking: bool, listed: set[str]) -> None:
        self.root = ROOT
        self.configuration = configuration
        self.checking = checking
        self._graph = graph
        self._listed = listed  # the build's one walk of the host (T-0087)

    def files(self, suffix: str) -> list[Path]:
        return graphe_root.files(suffix, self.root, self._listed)

    @cached_property
    def graph(self) -> dict:
        if self._graph is None:
            return {"nodes": {}, "links": []}
        return {"nodes": {n: copy.deepcopy(d) for n, d in self._graph.nodes(data=True)},
                "links": [{"source": s, "target": t, **copy.deepcopy({**d, "relations": sorted(d["relations"])})}
                          for s, t, d in self._graph.edges(data=True)]}


def run_reader(name: str, configuration: dict, checking: bool, listed: set[str]) -> dict:
    """A reader's contribution, in the build's process or a pool's: sent by its name, so a reader need not pickle."""
    return READERS[name](Project(configuration, None, checking, listed))
