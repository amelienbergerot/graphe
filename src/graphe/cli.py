"""graphe: the code graph of a host project - what calls what, what cites what.

    graphe build [--quiet]           graphe/: graphe.json, REPORT.md
    graphe view [X]                  graphe/graphe.html, opened (on X): the
                                     nodes laid out by community, on demand
    graphe check                     the coverage of each contribution
    graphe path A B [--undirected]   the shortest path from A to B
    graphe explain X [--all] [--source]   what X calls, what calls X (and its code)
    graphe callers X [--depth N]
                                     both say how many calls of X's name no
                                     reader could attribute: grep those
    graphe affected [REV] [--depth N]   what the working tree changes since it
                                     left REV (HEAD): the nodes touched, the
                                     definitions removed, the callers
    graphe search PATTERN            by name, then by displayed texts and comments
    graphe install [--remove]        the git hooks that rebuild it
    graphe hook                      Claude Code's PreToolUse hook (the plugin's): a
                                     grep for a node's name is pointed to explain

A node is designated by its id, its name (`help`, `Class.method`),
`file::name` (`tools.py::help`), a file by its path, or, in GDScript, by the
constant that preloads its script (`Script.function`).

The readers: graphe/python.py (the ast, calls resolved by types),
graphe/godot.py (GDScript, by patterns) and graphe/js.py
(`.js`, `.mjs`, `.jsx`, `.ts`, `.tsx`, the script and markup of `.svelte` and `.vue`, by tree-sitter: calls
resolved by the imports, by `new C()` or `f()` assigned, else by the name); generic.py reads
Go, Rust, Java/Kotlin, C/C++, C#, Ruby, Swift and PHP (with the actions of a
`switch ($action)`) by tree-sitter, a call linked by its name only when the
language (or family) defines it once (docs/readers.md lists every reader). The core, core.py, then
reads the text: the end of each function and class, the texts it displays
(the `displayed_text` pattern of graphe.toml), its comment, module variables
and who reads them, and the documents (the host's Markdown, `[documents]` of
graphe.toml) - who cites them, what they name. The fields of a class are
nodes (the Python reader). A keyed link (`[keys]` of graphe.toml: `names`,
`answers`, `parameters`) is a `sends` from the code that names a key (a
front's `api("zones")`) to the code that answers it (`'/api/zones'`).

Communities (`[communities]` of graphe.toml): `separate` gives kinds outside
the code their own community (kind -> name), after tickets, values and
documents; `strip_prefixes` removes prefixes from community names.

The contract (docs/contribution.md): readers and local extensions return a
contribution through `contribute(project)`. Assembly runs the readers, then
the core (core.py), then the extensions declared by `[[extensions]]`
in graphe.toml, in their order. A `with_readers` extension comes in with the
readers, before the core, and may take over their links.

Files read (root.py): those git tracks, plus untracked files that
are not ignored, each to the reader of its extension; `exclude`, in an
optional graphe.toml at the host root, removes folders.

Updates: `install` sets git hooks (post-commit, post-merge, post-checkout,
post-rewrite) that rebuild the graph in the background with the global
`graphe` command, and adds the output to the host's .gitignore; a query on a
graph older than the host's code or than the tool rebuilds it first.
"""

from __future__ import annotations

import copy
import functools
import importlib.util
import itertools
import json
import math
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
import webbrowser
from collections import Counter, defaultdict
from functools import cached_property
from pathlib import Path

import networkx as nx

from graphe import core, generic, godot, js, python
from graphe import root as graphe_root  # `root` is the host's path in this module's signatures
from graphe.root import CONFIGURATION, OUTPUT, ROOT

JSON = OUTPUT / "graphe.json"
HOOKS = ("post-commit", "post-merge", "post-checkout", "post-rewrite")
# (start, end) of the block set in a hook; the second, the one from before T-0011 (the host's relay, then the tool in
# French), is removed too.
BLOCKS = (("# >>> graphe code graph", "# <<< graphe code graph"), ("# >>> graphe du code", "# <<< graphe du code"))
# What leads from the caller to the callee.
CALLS = {"calls", "uses", "references", "indirect_call", "sends", "dispatches", "reads", "writes", "value"}
# T-0354: nodes that are not code, each their own community - a ticket, a value or a document links files that
# nothing else links, and would merge unrelated communities. The host adds some (`[communities] separate`).
SEPARATE = {"ticket": "tickets", "value": "values", "document": "documents"}
OFF_CODE_WEIGHT = 4


def _communities_config() -> tuple[dict[str, str], list[str]]:
    """`[communities]` of graphe.toml: the separate kinds (kind -> name), and the prefixes removed from names."""
    table = graphe_root.configuration().get("communities", {})
    return {**SEPARATE, **table.get("separate", {})}, table.get("strip_prefixes", [])


# ---------- build

def _sources() -> list[Path]:
    """T-0009: all the host's files, not only the readers' (an extension reads what it wants)."""
    return graphe_root.files("") + [p for p in [ROOT / CONFIGURATION]  # files() tests is_file already
                                    + [ROOT / e.get("path", "") for e in _declared_extensions()] if p.is_file()]


def _tool() -> list[Path]:
    """The tool's files (T-0006): a fixed reader makes every host's graph stale."""
    return sorted(Path(__file__).parent.glob("*.py"))


def _commit() -> str | None:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                           timeout=10)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


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
NODE_FIELDS = ("id", "label", "kind", "source_file", "source_location", "name")
LINK_FIELDS = ("source", "target", "relation", "confidence", "source_file", "source_location", "context")


class Project:
    """What `contribute(project)` receives: the root, the host's files, the configuration section of the one who
    contributes and the graph already assembled, copied on reading (docs/contribution.md)."""

    def __init__(self, configuration: dict, graph: nx.DiGraph, checking: bool) -> None:
        self.root = ROOT
        self.configuration = configuration
        self.checking = checking
        self._graph = graph

    def files(self, suffix: str) -> list[Path]:
        return graphe_root.files(suffix, self.root)

    @cached_property
    def graph(self) -> dict:
        return {"nodes": {n: copy.deepcopy(d) for n, d in self._graph.nodes(data=True)},
                "links": [{"source": s, "target": t, **copy.deepcopy({**d, "relations": sorted(d["relations"])})}
                          for s, t, d in self._graph.edges(data=True)]}


def _declared_extensions() -> list[dict]:
    return graphe_root.configuration().get("extensions", [])


def _extension(declaration: dict):
    """The `contribute` function of a local extension; an extension not found stops the build."""
    rel = declaration.get("path", "")
    file = ROOT / rel
    if not rel or not file.is_file():
        raise RuntimeError(f"local extension {rel!r} not found ([[extensions]] path, {CONFIGURATION})")
    spec = importlib.util.spec_from_file_location(f"graphe_extension_{file.stem}", file)
    if spec is None:
        raise RuntimeError(f"local extension {rel}: not a Python module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # a dataclass of the extension looks for its module here
    spec.loader.exec_module(module)
    if not callable(getattr(module, "contribute", None)):
        raise RuntimeError(f"local extension {rel}: no function contribute(project)")
    return module.contribute


def _insert(graph: nx.DiGraph, contributions: list[tuple[str, dict]], dangling: list[dict]) -> None:
    """The contributions into the graph: the nodes sorted by id (an id already there merges its attributes), then
    the links; one link per pair of nodes, which keeps its relations and its locations."""
    nodes = sorted(((who, n) for who, c in contributions for n in c.get("nodes", [])), key=lambda p: str(p[1].get("id")))
    for who, n in nodes:
        required = ("id",) if n.get("id") in graph else NODE_FIELDS
        if missing := [k for k in required if k not in n]:
            raise RuntimeError(f"{who}: node {n.get('id')!r} lacks {', '.join(missing)}")
        graph.add_node(n["id"], **n)
    for who, c in contributions:
        for e in c.get("links", []):
            if missing := [k for k in LINK_FIELDS if k not in e]:
                raise RuntimeError(f"{who}: link {e.get('source')!r} -> {e.get('target')!r} lacks "
                                   f"{', '.join(missing)}")
            s, target = e["source"], e["target"]
            if s not in graph or target not in graph:
                dangling.append(e)
                continue
            location = f"{e['source_file']}:{e['source_location'].lstrip('L')}"
            if graph.has_edge(s, target):
                d = graph[s][target]
                d["relations"].add(e["relation"])
                if location not in d["locations"]:
                    d["locations"].append(location)
                if e["confidence"] == "EXTRACTED":
                    d["confidence"] = "EXTRACTED"
                if e["context"] and e["context"] not in d["contexts"]:
                    d["contexts"].append(e["context"])
            else:
                graph.add_edge(s, target, relations={e["relation"]}, confidence=e["confidence"], locations=[location],
                               contexts=[e["context"]] if e["context"] else [])


def _take_over(contributions: list[tuple[str, dict]]) -> None:
    """The takeovers (`takeovers`), in their order: the links that leave `from` from the lines `lines`
    (bounds included) of `source_file` leave from `to`. A later takeover sees the earlier ones (a branch in a branch).
    Only the readers' links are taken over: an extension returns its own already in their place."""
    links = [e for who, c in contributions if who in READERS for e in c.get("links", [])]
    for who, c in contributions:
        for r in c.get("takeovers", []):
            if missing := [k for k in ("from", "to", "source_file", "lines") if k not in r]:
                raise RuntimeError(f"{who}: a takeover lacks {', '.join(missing)}")
            start, end = r["lines"]
            for e in links:
                line = int(str(e.get("source_location", "")).lstrip("L") or 0)
                if e.get("source") == r["from"] and e.get("source_file") == r["source_file"] and start <= line <= end:
                    e["source"] = r["to"]


def assemble(checking: bool = False) -> tuple[nx.DiGraph, dict, list[dict], dict[str, list[dict]]]:
    """The readers (and the `with_readers` extensions), then the core, then the other local extensions
    in the order of graphe.toml: the directed graph,
    the coverage, the dangling links and the sites of each contribution."""
    configuration = graphe_root.configuration()
    graph = nx.DiGraph()
    dangling: list[dict] = []
    # The readers together: their nodes come in sorted all at once, as before the contract (T-0007).
    readers = [(name, contribute(Project(configuration.get(name, {}), graph, checking)))
               for name, contribute in READERS.items()]
    # T-0008: a `with_readers` extension comes in with them, before the core, and may take over their links.
    with_, after = [], []
    for declaration in _declared_extensions():
        (with_ if declaration.get("with_readers") else after).append(declaration)
    readers += [(d.get("path", ""), _extension(d)(Project(d, graph, checking))) for d in with_]
    _take_over(readers)
    _insert(graph, readers, dangling)
    core.enrich(graph, ROOT)
    contributions = list(readers)
    for declaration in after:
        contribution = (declaration.get("path", ""), _extension(declaration)(Project(declaration, graph, checking)))
        if "takeovers" in contribution[1]:
            raise RuntimeError(f"{contribution[0]}: takeovers without with_readers = true ({CONFIGURATION})")
        _insert(graph, [contribution], dangling)
        contributions.append(contribution)
    # shortcut: a file declared twice that returns sites twice keeps only the last ones; to merge if an extension
    # needs both sides.
    sites = {who: c["sites"] for who, c in contributions if "sites" in c}
    coverage = {who: dict(Counter(s["verdict"] for s in site_list if "verdict" in s).most_common())
                for who, site_list in sites.items()}
    coverage["dangling"] = len(dangling)
    return _sorted(graph), coverage, dangling, sites


def _location_key(location: str) -> tuple[str, int]:
    file, _, line = location.rpartition(":")
    digits = re.match(r"\d*", line).group()
    return file, int(digits or 0)


def _sorted(graph: nx.DiGraph) -> nx.DiGraph:
    """T-0381: nodes, links and locations in the order of their content - that of the readers (and of hashing) moved graphe.html."""
    sorted_ = nx.DiGraph()
    sorted_.add_nodes_from(sorted(graph.nodes(data=True), key=lambda n: n[0]))
    for s, t, d in sorted(graph.edges(data=True), key=lambda e: (e[0], e[1])):
        sorted_.add_edge(s, t, **{**d, "locations": sorted(d["locations"], key=_location_key), "contexts": sorted(d["contexts"])})
    return sorted_


def communities(graph: nx.DiGraph) -> tuple[dict[str, int], dict[int, str]]:
    separate, prefixes = _communities_config()
    undirected = nx.Graph()
    undirected.add_nodes_from(n for n in graph.nodes if graph.nodes[n]["kind"] not in separate)
    for s, t, d in graph.edges(data=True):
        if s != t and s in undirected and t in undirected:
            weight = undirected[s][t]["weight"] if undirected.has_edge(s, t) else 0
            undirected.add_edge(s, t, weight=weight + len(d["locations"]))
    groups = nx.community.louvain_communities(undirected, weight="weight", seed=0)
    groups = sorted(groups, key=lambda g: (-len(g), min(g)))
    community_of, names, seen = {}, {}, Counter()
    for i, group in enumerate(groups):
        for n in group:
            community_of[n] = i
        files = Counter(graph.nodes[n]["source_file"] for n in sorted(group))  # ties: by the id
        (first, count), *rest = files.most_common(2)
        name = _short(first, prefixes)
        if rest and rest[0][1] * 3 >= count:
            name += " + " + _short(rest[0][0], prefixes)
        seen[name] += 1
        names[i] = name if seen[name] == 1 else f"{name} ({seen[name]})"
    for kind, name in separate.items():
        members = [n for n, d in graph.nodes(data=True) if d["kind"] == kind]
        if members:
            i = len(names)
            names[i] = name
            community_of.update(dict.fromkeys(members, i))
    return community_of, names


def _short(file: str, prefixes: list[str]) -> str:
    for prefix in prefixes:
        file = file.removeprefix(prefix)
    return file.rsplit(".", 1)[0]


# T-0016: above it, spring_layout costs minutes (Django: 270 s for 19 communities of 1000 to 4800 nodes). The
# hosts' communities stay below (Grid Zero: 539 at most): their layout does not move.
LARGE_COMMUNITY = 1000


def _sunflower(graph: nx.DiGraph, group: list[str]) -> dict[str, tuple[float, float]]:
    """The nodes on a sunflower spiral in the unit disc, in the order of their files: a file's nodes side by side."""
    ordered = sorted(group, key=lambda n: (graph.nodes[n]["source_file"], n))
    golden = math.pi * (3 - math.sqrt(5))
    return {n: (math.sqrt((k + 0.5) / len(ordered)) * math.cos(k * golden),
                math.sqrt((k + 0.5) / len(ordered)) * math.sin(k * golden)) for k, n in enumerate(ordered)}


def _first_free(placed: list[tuple[float, float, float]], radius: float, smallest: float,
                open_from: int) -> tuple[tuple[float, float], int]:
    """The first step of the spiral, from `open_from`, where a disc of `radius` overlaps none of those placed; and
    the new `open_from`. T-0016: numpy discards by batches the steps surely blocked (with a margin over its
    rounding), the others are decided by the exact test, in order: the place is the same. The steps blocked even
    for the `smallest` disc stay blocked for every disc to come (the radii only decrease): they are not walked
    again (Django's 919 communities: from 65 s to a few)."""
    import numpy as np  # here: the queries do not pay for it

    discs = np.array(placed)
    for start in itertools.count(open_from, 1024):
        steps = np.arange(start, start + 1024)
        distance = 2.0 * np.sqrt(steps + 1) * 3.0
        gap = np.hypot(distance * np.cos(steps * 0.5) - discs[:, 0, None],
                       distance * np.sin(steps * 0.5) - discs[:, 1, None]) - discs[:, 2, None]
        if start == open_from:
            forever = (gap < smallest + 1.0 - 1e-6).any(axis=0)
            open_from += 1024 if forever.all() else int(np.argmin(forever))
        for step in np.flatnonzero(~(gap < radius + 1.0 - 1e-6).any(axis=0)) + start:
            angle, distance = int(step) * 0.5, 2.0 * math.sqrt(int(step) + 1) * 3.0
            center = (distance * math.cos(angle), distance * math.sin(angle))
            if all(math.dist(center, (x, y)) >= r + radius + 1.0 for x, y, r in placed):
                return center, open_from
    raise AssertionError("unreachable: the spiral leaves every disc behind")


def layout(graph: nx.DiGraph, community_of: dict[str, int]) -> dict[str, tuple[float, float]]:
    """Each community laid out alone in a disc, the discs set in a spiral
    from the largest to the smallest: much faster than a whole layout
    (15 s for 2400 nodes), and without overlap."""
    members = defaultdict(list)
    for n, i in community_of.items():
        members[i].append(n)
    placed: list[tuple[float, float, float]] = []
    positions = {}
    smallest, open_from = math.sqrt(min(map(len, members.values()), default=1)) * 1.6 + 1.0, 0
    for i in sorted(members, key=lambda i: (-len(members[i]), i)):
        radius = math.sqrt(len(members[i])) * 1.6 + 1.0
        center = (0.0, 0.0)
        if placed:
            center, open_from = _first_free(placed, radius, smallest, open_from)
        placed.append((*center, radius))
        # T-0381: not graph.subgraph(), which walks its nodes in the order of a set (the luck of hashing)
        group = sorted(members[i])
        if len(group) > LARGE_COMMUNITY:
            local = _sunflower(graph, group)
        else:
            inside = set(group)
            sub = nx.Graph()
            sub.add_nodes_from(group)
            sub.add_edges_from((s, t) for s, t in graph.edges(group) if t in inside)
            local = nx.spring_layout(sub, seed=0, iterations=60) if len(members[i]) > 1 else {members[i][0]: (0, 0)}
        for n, (x, y) in local.items():
            positions[n] = (round(center[0] + x * radius * 0.92, 2), round(center[1] + y * radius * 0.92, 2))
    return positions


def _write(path: Path, text: str) -> None:
    """Writes alongside then replaces: two builds in a row never leave a
    half-written file."""
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False, suffix=".tmp") as f:
        f.write(text.encode("utf-8"))
    os.replace(f.name, path)


# T-0025: the verdicts of a call no link leads from: a name of ours, perhaps, but the reader could not tell which;
# T-0074: by cause (GLOSSARY.md, Unattributed call). `dynamic` has no name. shortcut: Python's bare `f()` the reader
# cannot attribute is `unknown`, counted as a receiver of unknown type, as GDScript's `unknown` on a known script
# that lacks the name; to split if an agent is misled by it.
CAUSES = {"ambiguous": "several", "common": "common", "unknown": "receiver", "member": "receiver",
          "attribute": "receiver", "external?": "outside", "absent": "outside"}


def _unattributed(graph: nx.DiGraph, sites: dict[str, list[dict]]) -> dict[str, dict[str, int]]:
    """The calls not attributed, by the name of a function or a method of ours (`filter`), then by cause: what grep
    would find and the graph does not."""
    ours = {graph.nodes[n]["name"].rsplit(".", 1)[-1] for n in graph if graph.nodes[n]["kind"] in ("function", "method")}
    counted = Counter((s["name"], CAUSES[s["verdict"]]) for site_list in sites.values() for s in site_list
                      if s.get("verdict") in CAUSES and s.get("name") in ours)
    by_name: dict[str, dict[str, int]] = defaultdict(dict)
    for (name, cause), count in sorted(counted.items()):
        by_name[name][cause] = count
    return dict(by_name)


def _missed(graph: nx.DiGraph, n: str) -> None:
    """T-0025, T-0074: the lines that tell the agent when to grep, by cause."""
    d = graph.nodes[n]
    name = d["name"].rsplit(".", 1)[-1]
    causes = graph.graph["unattributed"].get(name, {}) if d["kind"] in ("function", "method") else {}
    if not causes:
        return
    print(f"  + {sum(causes.values())} calls named `{name}` the graph could not attribute:")
    if causes.get("several"):
        # shortcut: the candidates by bare name, across languages and kinds where a reader sees its own language and
        # may keep to methods (JS's `x.f()`, `apart`); to take the reader's own candidates if one misleads an agent.
        candidates = sorted((c for c in graph if graph.nodes[c]["kind"] in ("function", "method")
                             and graph.nodes[c]["name"].rsplit(".", 1)[-1] == name),
                            key=lambda c: (graph.nodes[c]["source_file"], _line(graph, c)))
        listed = f": {', '.join(_designation(graph, c) for c in candidates)}" if len(candidates) <= 5 else ""
        print(f"    {causes['several']} between {len(candidates)} definitions{listed}")
    for cause, text in (("common", "on a common name"), ("receiver", "on a receiver of unknown type"),
                        ("outside", "to a definition outside the host")):
        if causes.get(cause):
            print(f"    {causes[cause]} {text}")


def build(quiet: bool = False) -> int:
    start = time.monotonic()
    OUTPUT.mkdir(exist_ok=True)
    graph, coverage, dangling, sites = assemble()
    community_of, names = communities(graph)
    data = {
        "built": time.strftime("%Y-%m-%d %H:%M:%S"), "built_s": time.time(), "commit": _commit(),
        "coverage": coverage, "communities": {str(i): name for i, name in names.items()},
        "unattributed": _unattributed(graph, sites),
        "nodes": [{**graph.nodes[n], "community": community_of[n]} for n in graph.nodes],
        "links": [{"source": s, "target": t, "relations": sorted(d["relations"]), "confidence": d["confidence"],
                   "locations": d["locations"], "contexts": d["contexts"]} for s, t, d in graph.edges(data=True)],
    }
    _write(JSON, json.dumps(data, ensure_ascii=False))
    _write(OUTPUT / "REPORT.md", report(graph, data, community_of, names))
    if not quiet:
        print(f"{graph.number_of_nodes()} nodes, {graph.number_of_edges()} links, {len(names)} communities, "
              f"{len(dangling)} dangling link(s) - {time.monotonic() - start:.1f} s -> {OUTPUT.relative_to(ROOT)}/")
        for e in dangling[:10]:
            print("  dangling", e["source"], "->", e["target"], e["relation"], e["source_file"], e["source_location"])
    return 0


# ---------- the report

def _location(graph: nx.DiGraph, n: str) -> str:
    d = graph.nodes[n]
    return f"{d['source_file']}:{d['source_location'].lstrip('L')}"


def report(graph: nx.DiGraph, data: dict, community_of: dict, names: dict) -> str:
    c = data["coverage"]
    kinds = Counter(d["kind"] for _, d in graph.nodes(data=True))
    lines = [
        "# The code graph", "",
        f"Built on {data['built']} (commit {data['commit']}, working tree included) "
        "by `graphe build`.", "",
        f"- {graph.number_of_nodes()} nodes: " + ", ".join(f"{n} {k}" for k, n in kinds.most_common()),
        f"- {graph.number_of_edges()} links, {len(names)} communities, {c['dangling']} dangling link(s)",
        f"- Python calls classified: {c['python']}",
        f"- GDScript calls classified: {c['godot']}",
        "", "`ours`: linked for sure; `ours?`: linked by name alone (INFERRED); `ambiguous`: a name that "
        "several of our functions bear, on an untyped receiver - not linked; `external`, `engine`: "
        "outside the repository. Details: `graphe check`.", "",
        "## Most connected", "",
    ]
    def real(links) -> int:  # without containment (file, class -> function)
        return sum(1 for *_, d in links if d["relations"] - {"contains", "method"})
    incoming = {n: real(graph.in_edges(n, data=True)) for n in graph.nodes}
    outgoing = {n: real(graph.out_edges(n, data=True)) for n in graph.nodes}
    central = sorted((n for n in graph.nodes if graph.nodes[n]["kind"] != "file"),
                     key=lambda n: (-incoming[n] - outgoing[n], n))[:20]
    for n in central:
        lines.append(f"- `{graph.nodes[n]['label']}` - {incoming[n]} incoming, "
                     f"{outgoing[n]} outgoing ({_location(graph, n)})")
    commands = sorted(n for n in graph.nodes if graph.nodes[n]["kind"] == "command")
    if commands:
        lines += ["", "## Commands", "", "Each command: who sends it, what it calls.", ""]
    for n in commands:
        senders = sorted({graph.nodes[s]["label"] for s in graph.predecessors(n)
                          if "sends" in graph[s][n]["relations"]})
        callees = sorted({graph.nodes[x]["label"] for x in graph.successors(n)})
        lines.append(f"- `{graph.nodes[n]['label']}`: sent by "
                     f"{', '.join(senders) or 'nobody'}; calls "
                     f"{', '.join(callees[:8]) or '-'}{' …' if len(callees) > 8 else ''}")
    imports = nx.DiGraph()
    for s, target, d in graph.edges(data=True):
        ss, tt = graph.nodes[s]["source_file"], graph.nodes[target]["source_file"]
        if "imports" in d["relations"] and graph.nodes[s]["kind"] == "file" and ss != tt:
            imports.add_edge(ss, tt)
    cycles = sorted((cy for cy in nx.simple_cycles(imports, length_bound=4)), key=lambda cy: (len(cy), cy))[:20]
    lines += ["", "## Import cycles (module level)", ""]
    lines += [f"- {' → '.join(cy + cy[:1])}" for cy in cycles] or ["None."]
    lines += ["", "## Communities", ""]
    members = defaultdict(list)
    for n, i in community_of.items():
        members[i].append(n)
    small = 0
    for i in sorted(members):
        if len(members[i]) < 4:
            small += 1
            continue
        top = sorted(members[i], key=lambda n: (-graph.degree(n), n))[:8]
        lines += [f"### {i} - {names[i]} ({len(members[i])} nodes)", "",
                  ", ".join(f"`{graph.nodes[n]['label']}`" for n in top), ""]
    lines += [f"{small} small communities (fewer than 4 nodes) not detailed.", "",
              "## What the graph does not see", "",
              "- dynamic calls: `getattr`, a callback stored in a variable, a receiver that nothing "
              "types (the `ambiguous` ones);",
              "- files that no reader takes, and those that `exclude` removes (graphe.toml).", ""]
    return "\n".join(lines)


# ---------- the page

def page(data: dict) -> str:
    nodes = data["nodes"]
    index = {n["id"]: i for i, n in enumerate(nodes)}
    compact = {
        "n": [[n["label"], n["source_file"], n["source_location"].lstrip("L"), n["community"], n["x"], n["y"],
               n["kind"], n["id"]] for n in nodes],
        "l": [[index[e["source"]], index[e["target"]], ",".join(e["relations"]), e["confidence"] == "EXTRACTED"]
              for e in data["links"]],
        "c": data["communities"], "t": data["built"], "k": data["commit"],
    }
    text = json.dumps(compact, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return PAGE.replace("__DATA__", text)


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Code graph</title>
<style>
:root{--bg:#f7f7f5;--text:#1d1d1b;--muted:#6b6b66;--panel:#ffffff;--border:#deded8;--link:rgba(60,60,60,.10);--pick:#d4572a}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--text:#e8e8e3;--muted:#9a9a93;--panel:#1f1f1d;--border:#34342f;--link:rgba(220,220,210,.09);--pick:#f08a5d}}
*{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--bg);color:var(--text);font:14px/1.4 system-ui,sans-serif}
#map{position:fixed;top:0;left:0;width:calc(100% - 340px);height:100%;cursor:grab;touch-action:none}#map.dragging{cursor:grabbing}
#side{position:fixed;top:0;right:0;bottom:0;width:340px;background:var(--panel);border-left:1px solid var(--border);display:flex;flex-direction:column;overflow-x:hidden}
#side header{padding:12px 14px;border-bottom:1px solid var(--border)}#side h1{font-size:15px;margin:0 0 6px}
#side input[type=search]{width:100%;padding:7px 9px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--text);font:inherit}
#side label{display:block;margin-top:8px;color:var(--muted);font-size:12px}
#card{padding:12px 14px;overflow:auto;flex:1}#card h2{font-size:15px;margin:0 0 2px;word-break:break-all}
#card .where{color:var(--muted);font-size:12px;margin-bottom:10px;word-break:break-all}#card h3{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:14px 0 4px}
#card a{color:var(--text);text-decoration:none;display:block;padding:2px 0;border-bottom:1px dotted transparent;cursor:pointer;word-break:break-all}
#card a:hover{color:var(--pick)}#card .rel{color:var(--muted);font-size:11px}
@media (max-width:760px){#map{width:100%;height:55vh}#side{top:auto;height:45vh;width:100%;border-left:0;border-top:1px solid var(--border)}}
</style></head><body>
<canvas id="map"></canvas>
<aside id="side"><header><h1>Code graph</h1><input id="search" type="search" list="names" placeholder="Search a function, a file…" autocomplete="off"><datalist id="names"></datalist>
<label><input id="contains" type="checkbox"> containment links (file → function)</label></header>
<div id="card"></div></aside>
<script id="data" type="application/json">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);
const N=D.n.map((n,i)=>({i,label:n[0],file:n[1],line:n[2],c:n[3],x:n[4],y:n[5],kind:n[6],id:n[7],outs:[],ins:[]}));
const L=D.l.map(l=>({s:l[0],t:l[1],rel:l[2],sure:l[3]}));
for(const l of L){N[l.s].outs.push(l);N[l.t].ins.push(l)}
for(const n of N){n.deg=n.outs.length+n.ins.length;n.r=1.2+Math.sqrt(n.deg)*0.45}
const hue=c=>`hsl(${(c*137.508)%360},55%,52%)`;
const cv=document.getElementById('map'),cx=cv.getContext('2d');
let fit=1,view={x:0,y:0,z:1},picked=null,neighbours=new Set(),showContains=false;
function resize(){const r=cv.getBoundingClientRect(),d=devicePixelRatio||1;cv.width=r.width*d;cv.height=r.height*d;cx.setTransform(d,0,0,d,0,0);draw()}
function frame(){let a=1e9,b=1e9,c=-1e9,e=-1e9;for(const n of N){a=Math.min(a,n.x);b=Math.min(b,n.y);c=Math.max(c,n.x);e=Math.max(e,n.y)}
const r=cv.getBoundingClientRect();view.z=fit=Math.min(r.width/(c-a+10),r.height/(e-b+10));view.x=r.width/2-(a+c)/2*view.z;view.y=r.height/2-(b+e)/2*view.z}
const screen=n=>[n.x*view.z+view.x,n.y*view.z+view.y];
function color(v){return getComputedStyle(document.documentElement).getPropertyValue(v)}
function draw(){const r=cv.getBoundingClientRect();cx.clearRect(0,0,r.width,r.height);
cx.lineWidth=1;cx.strokeStyle=color('--link');cx.beginPath();
for(const l of L){if(!showContains&&(l.rel==='contains'||l.rel==='method'))continue;const[a,b]=screen(N[l.s]),[c,d]=screen(N[l.t]);cx.moveTo(a,b);cx.lineTo(c,d)}cx.stroke();
if(picked){cx.strokeStyle=color('--pick');cx.lineWidth=1.5;cx.beginPath();for(const l of picked.outs.concat(picked.ins)){const[a,b]=screen(N[l.s]),[c,d]=screen(N[l.t]);cx.moveTo(a,b);cx.lineTo(c,d)}cx.stroke()}
for(const n of N){const[x,y]=screen(n);if(x<-20||y<-20||x>r.width+20||y>r.height+20)continue;const rr=Math.max(1.5,n.r*Math.sqrt(view.z));
cx.globalAlpha=picked&&!neighbours.has(n.i)&&n!==picked?0.25:1;cx.fillStyle=n===picked?color('--pick'):hue(n.c);cx.beginPath();cx.arc(x,y,rr,0,7);cx.fill()}
cx.globalAlpha=1;cx.fillStyle=color('--text');
// Labels that do not overlap: the most linked first.
const placed=[],free=(x,y,w)=>{for(const p of placed)if(x<p[2]&&x+w>p[0]&&y-11<p[3]&&y+3>p[1])return false;placed.push([x,y-11,x+w,y+3]);return true};
if(view.z>fit*2.5){cx.font='12px system-ui';const shown=N.filter(n=>{const[x,y]=screen(n);return x>0&&y>0&&x<r.width&&y<r.height&&(!picked||neighbours.has(n.i)||n===picked)});
shown.sort((a,b)=>(b===picked)-(a===picked)||b.deg-a.deg);for(const n of shown.slice(0,600)){const[x,y]=screen(n),w=cx.measureText(n.label).width;if(free(x+4,y-3,w))cx.fillText(n.label,x+4,y-3)}}
else{const centers={};for(const n of N){const c=centers[n.c]||(centers[n.c]={x:0,y:0,k:0});c.x+=n.x;c.y+=n.y;c.k++}
cx.font='600 12px system-ui';for(const c of Object.keys(centers).sort((a,b)=>centers[b].k-centers[a].k)){const v=centers[c];const w=cx.measureText(D.c[c]).width,x=(v.x/v.k)*view.z+view.x-w/2,y=(v.y/v.k)*view.z+view.y;if(free(x,y,w))cx.fillText(D.c[c],x,y)}}}
function link(n){return `<a data-i="${n.i}">${esc(n.label)} <span class="rel">${esc(n.file)}:${n.line}</span></a>`}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function group(list,end){const g={};for(const l of list){for(const r of l.rel.split(','))(g[r]=g[r]||[]).push(N[l[end]])}
return Object.keys(g).sort().map(r=>`<h3>${esc(r)} (${g[r].length})</h3>`+g[r].sort((a,b)=>a.label.localeCompare(b.label)).map(link).join('')).join('')}
function pick(n,center){picked=n;neighbours=new Set();if(n){for(const l of n.outs)neighbours.add(l.t);for(const l of n.ins)neighbours.add(l.s)}
const f=document.getElementById('card');
if(!n){f.innerHTML=`<p class="where">${N.length} nodes, ${L.length} links. Built on ${esc(D.t)} (commit ${esc(D.k)}).</p><p class="where">Wheel: zoom. Drag: move. Click: a node and its links.</p>`}
else{f.innerHTML=`<h2>${esc(n.label)}</h2><div class="where">${esc(n.kind)} · ${esc(n.file)}:${n.line} · ${esc(D.c[n.c])}<br>${esc(n.id)}</div><h3 style="color:var(--text)">What it calls</h3>${group(n.outs.filter(l=>l.rel!=='contains'&&l.rel!=='method'),'t')||'<p class=where>nothing</p>'}<h3 style="color:var(--text)">What calls it</h3>${group(n.ins.filter(l=>l.rel!=='contains'&&l.rel!=='method'),'s')||'<p class=where>nothing</p>'}`}
if(n&&center){const r=cv.getBoundingClientRect();view.z=Math.max(view.z,fit*6);view.x=r.width/2-n.x*view.z;view.y=r.height/2-n.y*view.z}draw()}
document.getElementById('card').addEventListener('click',e=>{const a=e.target.closest('a[data-i]');if(a)pick(N[+a.dataset.i],true)});
const dl=document.getElementById('names');dl.innerHTML=N.map(n=>`<option value="${esc(n.label)} — ${esc(n.file)}">`).join('');
document.getElementById('search').addEventListener('change',e=>{const v=e.target.value.split(' — ');const n=N.find(n=>n.label===v[0]&&(!v[1]||n.file===v[1]))||N.find(n=>n.label.toLowerCase().includes(v[0].toLowerCase()));if(n)pick(n,true)});
document.getElementById('contains').addEventListener('change',e=>{showContains=e.target.checked;draw()});
let drag=null,moved=false;
cv.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,vx:view.x,vy:view.y};moved=false;cv.classList.add('dragging');cv.setPointerCapture(e.pointerId)});
cv.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.abs(dx)+Math.abs(dy)>3)moved=true;view.x=drag.vx+dx;view.y=drag.vy+dy;draw()});
cv.addEventListener('pointerup',e=>{cv.classList.remove('dragging');if(!moved){const r=cv.getBoundingClientRect(),px=e.clientX-r.left,py=e.clientY-r.top;let m=null,dm=144;
for(const n of N){const[x,y]=screen(n),d=(x-px)**2+(y-py)**2;if(d<dm){dm=d;m=n}}pick(m,false)}drag=null});
cv.addEventListener('wheel',e=>{e.preventDefault();const r=cv.getBoundingClientRect(),px=e.clientX-r.left,py=e.clientY-r.top,f=Math.exp(-e.deltaY*0.0015);
view.x=px-(px-view.x)*f;view.y=py-(py-view.y)*f;view.z*=f;draw()},{passive:false});
addEventListener('resize',resize);resize();frame();pick(null);
// graphe.html#<id> opens that node.
const anchor=()=>{const n=N.find(n=>n.id===decodeURIComponent(location.hash.slice(1)));if(n)pick(n,true)};addEventListener('hashchange',anchor);anchor();
</script></body></html>
"""


# ---------- the queries

def load(as_is: bool = False) -> nx.DiGraph:
    """The graph; rebuilt first if it is older than the host's code or than the tool."""
    if not (as_is and JSON.exists()):
        # The sources first: outside a git repository, their one-line error comes before any rebuilding line (T-0069).
        newest = max((p.stat().st_mtime for p in _sources() + _tool()), default=0)
        if not JSON.exists() or newest > JSON.stat().st_mtime:
            print("(the graph is older than the code or the tool: rebuilding)", file=sys.stderr)
            build(quiet=True)
    data = json.loads(JSON.read_bytes())
    # T-0074: a graph built before the counts per cause; an upgrade may not leave the tool's files newer than it
    if any(isinstance(v, int) for v in data.get("unattributed", {}).values()):
        build(quiet=True)
        data = json.loads(JSON.read_bytes())
    graph = nx.DiGraph(communities=data["communities"], unattributed=data.get("unattributed", {}))
    for n in data["nodes"]:
        graph.add_node(n["id"], **n)
    for e in data["links"]:
        graph.add_edge(e["source"], e["target"], **{k: v for k, v in e.items() if k not in ("source", "target")})
    return graph


def _bare(label: str) -> str:
    return label.removesuffix("()").lstrip(".")


def _preloads(root: Path = ROOT) -> dict[str, set[str]]:
    """The constants that preload a GDScript script, and that script:
    `const Outils = preload("res://menu/outils.gd")` -> godot/menu/outils.gd (godot.GODOT)."""
    pattern = re.compile(r'^const\s+(\w+)\s*=\s*preload\("res://([^"]+\.gd)"\)', re.M)
    alias: dict[str, set[str]] = defaultdict(set)
    for script in godot.scripts():
        for name, target in pattern.findall(script.read_bytes().decode("utf-8", "replace")):
            alias[name].add(godot.res(target))
    return alias


def find(graph: nx.DiGraph, text: str) -> list[str]:
    if text in graph:
        return [text]
    file, _, name = text.rpartition("::")
    found = []
    for n, d in graph.nodes(data=True):
        if file and not (d["source_file"].endswith(file) or file in d["source_file"]):
            continue
        if name in (d["name"], _bare(d["label"]), d["label"]) or d["name"].endswith("." + name) \
                or (d["kind"] == "file" and name == d["source_file"]):  # T-0016: a file as the answers print it
            found.append(n)
    exact = [n for n in found if graph.nodes[n]["name"] == name]  # a method's label is `.cle()`: not exact
    if file and len(exact) == 1:  # T-0016: in a file, `cle` is the variable, not `Gabarit.cle` too
        return exact
    if not found and not file and "." in name:
        # `Outils.aider`: Outils preloads godot/menu/outils.gd.
        head, _, member = name.partition(".")
        scripts = _preloads().get(head, set())
        found = [n for n, d in graph.nodes(data=True)
                 if d["source_file"] in scripts and member in (d["name"], _bare(d["label"]))]
    return sorted(found)


def _one(graph: nx.DiGraph, text: str) -> str | None:
    found = find(graph, text)
    if len(found) == 1:
        return found[0]
    if not found:
        print(f"no node for {text!r} - try: graphe search {text}")
    else:
        print(f"{text!r} designates {len(found)} nodes; pick one:")
        for n in found[:20]:  # each designation scans the graph: Django has 972 `__init__`
            print(f"  {_designation(graph, n)}  {_location(graph, n)}")
        if len(found) > 20:
            print(f"  ... and {len(found) - 20} more: narrow it by file::name")
    return None


def _designation(graph: nx.DiGraph, n: str) -> str:
    """T-0016: the shortest text that designates n alone, `Class.method` or `file::name`; else its id."""
    d = graph.nodes[n]
    for text in (d["name"], f"{d['source_file']}::{d['name']}", f"{d['source_file']}::{_bare(d['label'])}"):
        if find(graph, text) == [n]:
            return text
    return n


def _line(graph: nx.DiGraph, n: str) -> int:
    return int(graph.nodes[n]["source_location"].lstrip("L") or 0)


def _by_file(graph: nx.DiGraph, nodes, suffix: dict[str, str] | None = None) -> list[str]:
    """T-0016: nodes as the agent designates them next, one line per file (`file: Class.method:line, ...`); the
    kinds outside the code (tickets, values) by their name alone, on one line."""
    separate, _ = _communities_config()
    suffix = suffix or {}
    off, files = [], defaultdict(list)
    for n in sorted(nodes, key=lambda n: (graph.nodes[n]["source_file"], _line(graph, n), n)):
        d = graph.nodes[n]
        if d["kind"] in separate:
            off.append(d["name"] + suffix.get(n, ""))
        else:
            files[d["source_file"]].append(("(file)" if d["kind"] == "file" else f"{d['name']}:{_line(graph, n)}")
                                           + suffix.get(n, ""))
    return ([", ".join(off)] if off else []) + [file if entries == ["(file)"] else f"{file}: {', '.join(entries)}"
                                                for file, entries in files.items()]


def _label(graph: nx.DiGraph, n: str) -> str:
    d = graph.nodes[n]
    return d["source_file"] if d["kind"] == "file" else f"{d['name']} ({_location(graph, n)})"


def path(graph: nx.DiGraph, a: str, b: str, undirected: bool) -> int:
    source, target = _one(graph, a), _one(graph, b)
    if source is None or target is None:
        return 2
    view = graph.to_undirected(as_view=True) if undirected else graph
    separate, _ = _communities_config()

    def weight(x: str, y: str, _d: dict) -> int:
        # T-0354: without the direction, a value or a ticket links everything
        # that writes it; it serves only for want of a path through the code.
        off_code = graph.nodes[x]["kind"] in separate or graph.nodes[y]["kind"] in separate
        return OFF_CODE_WEIGHT if undirected and off_code else 1

    try:
        steps = nx.shortest_path(view, source, target, weight=weight)
    except nx.NetworkXNoPath:
        print("no path" + ("" if undirected else " in the direction of the links (try --undirected)"))
        return 1
    print(f"{len(steps) - 1} step(s):")
    print(f"  {_label(graph, steps[0])}")
    for x, y in zip(steps, steps[1:], strict=False):
        direction, d = ("-->", graph[x][y]) if graph.has_edge(x, y) else ("<--", graph[y][x])
        sure = "" if d["confidence"] == "EXTRACTED" else " [by name]"
        print(f"    {direction} {','.join(d['relations'])}{sure}  {d['locations'][0]}")
        print(f"  {_label(graph, y)}")
    return 0


def source_text(graph: nx.DiGraph, n: str) -> str:
    """The node's lines, numbered; "" without a known extent."""
    d = graph.nodes[n]
    start, end = int(d["source_location"].lstrip("L") or 0), int(d.get("end", 0))
    if not end or not (ROOT / d["source_file"]).is_file():
        return ""
    lines = (ROOT / d["source_file"]).read_bytes().decode("utf-8", "replace").splitlines()
    return "\n".join(f"{i:5d}  {lines[i - 1]}" for i in range(start, min(end, len(lines)) + 1))


def view(graph: nx.DiGraph, x: str | None) -> int:
    """T-0046: the page, on demand only: the build no longer pays for the layout. Its positions are those the build
    gave: the graph read back from graphe.json keeps the order of its nodes and links (T-0381)."""
    n = _one(graph, x) if x else ""
    if n is None:
        return 2
    data = json.loads(JSON.read_bytes())
    positions = layout(graph, {m: d["community"] for m, d in graph.nodes(data=True)})
    for node in data["nodes"]:
        node["x"], node["y"] = positions[node["id"]]
    _write(OUTPUT / "graphe.html", page(data))
    webbrowser.open((OUTPUT / "graphe.html").resolve().as_uri() + (f"#{n}" if n else ""))
    return 0


def explain(graph: nx.DiGraph, x: str, all_: bool, code: bool = False) -> int:
    n = _one(graph, x)
    if n is None:
        return 2
    d = graph.nodes[n]
    end = f"-{d['end']}" if d.get("end") and d["end"] != int(d["source_location"].lstrip("L") or 0) else ""
    print(f"{d['label']}  [{d['kind']}]  {_location(graph, n)}{end}")
    print(f"  id: {n}")
    print(f"  community: {graph.graph['communities'][str(d['community'])]}")
    if d.get("notes"):
        print(f"  note: {d['notes'][:300]}")
    for text in d.get("texts", [])[:10]:
        print(f"  displays: {text}")
    if code:
        print("\n" + (source_text(graph, n) or "  (no known extent)"))
    limit = None if all_ else 25
    for title, pairs in (("what it calls", [(t, graph[n][t]) for t in graph.successors(n)]),
                         ("what calls it", [(s, graph[s][n]) for s in graph.predecessors(n)])):
        by_relation = defaultdict(list)
        for other, link in pairs:
            for r in link["relations"]:
                by_relation[r].append((other, link))
        print(f"\n{title}:" + ("" if by_relation else " nothing"))
        for r in sorted(by_relation):
            inferred = {other for other, link in by_relation[r] if link["confidence"] != "EXTRACTED"}
            every = len(inferred) == len(by_relation[r])  # the mark once, on the relation
            print(f"  {r} ({len(by_relation[r])})" + (" [by name]" if every else
                                                      f" [{len(inferred)} by name: ?]" if inferred else ""))
            shown = sorted(by_relation[r], key=lambda p: (graph.nodes[p[0]]["source_file"], _line(graph, p[0])))
            for line in _by_file(graph, [other for other, _ in shown[:limit]],
                                 {} if every else dict.fromkeys(inferred, "?")):
                print(f"    {line}")
            if limit and len(by_relation[r]) > limit:
                print(f"    ... and {len(by_relation[r]) - limit} more (--all)")
    _missed(graph, n)  # under "what calls it", the last
    return 0


def callers(graph: nx.DiGraph, x: str, depth: int) -> int:
    n = _one(graph, x)
    if n is None:
        return 2
    _callers(graph, n, depth)
    return 0


def _callers(graph: nx.DiGraph, n: str, depth: int) -> None:
    seen, front = {n}, [n]
    for level in range(1, depth + 1):
        following = []
        for y in front:
            for s in graph.predecessors(y):
                if s not in seen and CALLS & set(graph[s][y]["relations"]):
                    seen.add(s)
                    following.append(s)
        if not following:
            break
        # T-0075: a caller linked by name alone, marked as explain marks it: once on the level if every one is
        fronts = set(front)
        guessed = {s: "?" for s in following
                   if all(graph[s][y]["confidence"] != "EXTRACTED" for y in graph.successors(s) if y in fronts)}
        every = len(guessed) == len(following)
        print(f"level {level} ({len(following)})" + (" [by name]" if every else "") + ":")
        for line in _by_file(graph, following, {} if every else guessed):
            print(f"  {line}")
        front = following
    if len(seen) == 1:
        print("nothing calls it (in what the graph sees)")
    _missed(graph, n)


HUNK = re.compile(r"@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
# shortcut: a removed definition is seen by its keyword (Python, GDScript, JS functions, Go, Rust, Kotlin, Swift, PHP,
# Ruby); Java's, C#'s, C's and JS classes' methods have none and are not listed as removed; to parse the old file if an
# agent misses one. Its indentation: a method's, removed from its class.
DEFINITION = re.compile(r"^(\s*)(?:(?:export|default|pub(?:\(\w+\))?|async|static|private|public|protected|"
                        r"internal|open|override|suspend|data|final|abstract|sealed|class)\s+)*"
                        r"(?:def|func|function|fn|fun|class)\s+(?:\([^)]*\)\s*)?"
                        r"(?:self\.)?(\w+)")


def _git(*arguments: str) -> str:
    """Its output as git wrote it: in bytes, a lone `\\r` of the host's code stays inside its line."""
    r = subprocess.run(["git", "-c", "core.quotepath=false", *arguments], cwd=ROOT, capture_output=True)
    if r.returncode:
        error = r.stderr.decode("utf-8", "replace").strip().splitlines() or ["failed"]
        raise RuntimeError(f"git {arguments[0]}: {error[0]}")
    return r.stdout.decode("utf-8", "replace")


def _changes(rev: str) -> dict[str, list[tuple[int, list[str] | None, list[str]]]]:
    """The working tree against where it left `rev` (a branch's base: what the branch changes, not what `rev` did
    since), by file: each hunk's first new-side line, the lines it adds and those it removes; an untracked file, new
    as a whole, is one hunk whose added lines are None (to read)."""
    base = _git("merge-base", rev, "HEAD").strip()
    # shortcut: a path git C-quotes (a `"`, a `\`, a control character) matches no file; to unquote if a host has one.
    diff = _git("diff", "-U0", "--no-color", "--no-ext-diff", "--no-prefix", "--relative", base, "--")
    hunks = defaultdict(list)
    old = new = ""
    left = 0  # the lines of the current hunk still to read
    for line in diff.split("\n"):  # git ends each line with \n; splitlines() would split on a form feed too
        if left and line[:1] in ("+", "-"):
            left -= 1
            hunks[new or old][-1][1 if line[0] == "+" else 2].append(line[1:])
        elif line.startswith(("--- ", "+++ ")):
            path = line[4:].rstrip("\t")  # git ends a path that holds a space with a tab
            path = "" if path == "/dev/null" else path
            old, new = (path, new) if line[0] == "-" else (old, path)
        elif m := HUNK.match(line):
            left = int(m[1] or 1) + int(m[3] or 1)
            hunks[new or old].append((int(m[2]), [], []))
    for rel in filter(None, _git("ls-files", "-z", "--others", "--exclude-standard").split("\0")):
        hunks[rel].append((1, None, []))
    return hunks


def _called(graph: nx.DiGraph, n: str) -> bool:
    """Something calls n, or calls of its name went unattributed: what `_callers` would print."""
    d = graph.nodes[n]
    return any(CALLS & set(graph[s][n]["relations"]) for s in graph.predecessors(n)) or \
        (d["kind"] in ("function", "method") and d["name"].rsplit(".", 1)[-1] in graph.graph["unattributed"])


def _innermost(bodies: list[tuple[int, int, str]], whole: str | None, line: int) -> str | None:
    """The innermost node whose body holds the line (a method, not its class); else the file's."""
    holding = [(e - s, n) for s, e, n in bodies if s <= line <= e]
    return min(holding)[1] if holding else whole


def affected(graph: nx.DiGraph, rev: str, depth: int) -> int:
    """T-0075: the nodes a diff touches, the definitions it removes, then the callers of each touched node."""
    by_file = defaultdict(list)
    for n, d in graph.nodes(data=True):
        by_file[d["source_file"]].append(n)
    touched, gone = set(), defaultdict(set)
    for file, hunks in _changes(rev).items():
        nodes = by_file.get(file, [])
        bodies = [(_line(graph, n), int(graph.nodes[n]["end"]), n) for n in nodes if graph.nodes[n].get("end")]
        classes = [b for b in bodies if graph.nodes[b[2]]["kind"] == "class"]
        whole = next((n for n in nodes if graph.nodes[n]["kind"] == "file"), None)
        for start, added, removed in hunks:
            # a document's prose ("function of ...") defines nothing
            definitions = [] if file.endswith(".md") else [m for t in removed if (m := DEFINITION.match(t))]
            gone[file] |= {m[2] for m in definitions}
            if not nodes:  # a file the graph does not read, or no longer (deleted): its removed definitions only
                continue
            if added is None:  # untracked
                added = (ROOT / file).read_bytes().decode("utf-8", "replace").splitlines()
            kept = [start + i for i, text in enumerate(added) if text.strip()]  # a blank line touches nothing
            if kept:
                touched.update(_innermost(bodies, whole, line) for line in kept)
            elif definitions:  # a whole definition removed, after line `start`: from its class if it was indented
                touched.add(_innermost(classes, whole, start) if definitions[0][1] else whole)
            elif first := next((text for text in removed if text.strip()), ""):  # lines removed, after line `start`
                # from a body when indented (after one of its own lines), else from the top level
                touched.add(_innermost(bodies, whole, max(start, 1)) if first[0].isspace() else whole)
        gone[file] -= {graph.nodes[n]["name"].rsplit(".", 1)[-1] for n in nodes}  # edited, not removed
    touched.discard(None)
    moved = {graph.nodes[n]["name"].rsplit(".", 1)[-1] for n in touched}  # to another file
    gone = {file: sorted(names - moved) for file, names in gone.items() if names - moved}
    if not touched and not gone:
        print(f"nothing touched against {rev} (in what the graph reads)")
        return 0
    if touched:
        print(f"touched ({len(touched)}):")
        for line in _by_file(graph, touched):
            print(f"  {line}")
    if gone:
        print("removed (no longer in the graph):")
        for file, names in sorted(gone.items()):
            print(f"  {file}: {', '.join(names)}")
    uncalled = {n for n in touched if not _called(graph, n)}
    for n in sorted(touched - uncalled, key=lambda n: (graph.nodes[n]["source_file"], _line(graph, n))):
        print(f"\n{_label(graph, n)}:")
        _callers(graph, n, depth)
    if uncalled:
        print("\nnothing calls these (in what the graph sees):")
        for line in _by_file(graph, uncalled):
            print(f"  {line}")
    return 0


# `def reset`, `func _ready`, `class Gabarit`: the name, without the language's keyword.
HEAD_WORDS = re.compile(r"^(?:async\s+def|def|static\s+func|func|class|function|const|var)\s+")


def search_nodes(graph: nx.DiGraph, pattern: str) -> list[tuple[str, str]]:
    """(node, where): by the name first; then, if a displayed text or a
    comment contains it, with what found it."""
    pattern = HEAD_WORDS.sub("", pattern.strip()).lower()
    by_name = sorted(n for n, d in graph.nodes(data=True)
                     if pattern in n.lower() or pattern in d["label"].lower() or pattern in d["name"].lower())
    seen = set(by_name)
    others = []
    for n, d in sorted(graph.nodes(data=True)):
        if n in seen:
            continue
        text = next((t for t in d.get("texts", []) if pattern in t.lower()), None)
        if text is not None:
            others.append((n, f"displays \"{text[:60]}\""))
        elif pattern in d.get("notes", "").lower():
            others.append((n, "comment"))
    return [(n, "") for n in by_name] + others


def search(graph: nx.DiGraph, pattern: str) -> int:
    found = search_nodes(graph, pattern)
    shown = dict(found[:60])
    by_name = [n for n, where in shown.items() if not where]  # first, as search_nodes ranks them
    for line in _by_file(graph, by_name) + _by_file(graph, shown.keys() - set(by_name),
                                                    {n: f" ({where})" for n, where in shown.items()}):
        print(f"  {line}")
    print(f"{len(found)} node(s)" + (" (60 shown)" if len(found) > 60 else ""))
    return 0 if found else 1


# T-0077: the options of grep and rg whose separate value is not the pattern.
GREP_VALUED = {"-A", "-B", "-C", "-m", "-f", "-g", "-t", "-T", "-j", "--glob", "--type", "--type-not", "--max-count",
               "--file", "--include", "--exclude", "--exclude-dir", "--color", "--colors", "--max-depth", "--context",
               "--after-context", "--before-context", "--replace", "--threads"}


def _grep_pattern(command: str) -> str | None:
    """The pattern of the first grep or rg of a shell command: `-e`'s value, else its first operand."""
    # shortcut: the first grep/rg only, a value glued to its option (`-eaider`) is missed, PowerShell is split by
    # POSIX rules; widen if agents' real commands go unhinted.
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    words = list(lexer)  # an unbalanced quote raises: the hook stays silent
    head = next((i for i, w in enumerate(words) if Path(w).name.removesuffix(".exe") in ("grep", "rg")), None)
    if head is None:
        return None
    rest = iter(itertools.takewhile(lambda w: w.strip("();<>|&"), words[head + 1:]))  # up to `|`, `&&`, `;`
    for w in rest:
        if w in ("-e", "--regexp"):
            return next(rest, None)
        if w in GREP_VALUED:
            next(rest, None)
        elif not w.startswith("-"):
            return w
    return None


def hook() -> int:
    """`graphe hook` (T-0077): Claude Code's PreToolUse hook. When Grep, or grep/rg through Bash or PowerShell,
    looks for a name a node bears, one line of added context names `graphe explain` on it. Silent otherwise, and on
    any error; it never blocks the tool, never rebuilds the graph (a stale one is read as it is)."""
    try:
        data = json.loads(sys.stdin.buffer.read())
        tool, tool_input = data["tool_name"], data["tool_input"]
        if tool == "Grep":
            pattern = tool_input["pattern"]
        elif tool in ("Bash", "PowerShell"):
            pattern = _grep_pattern(tool_input["command"]) or ""
        else:
            return 0
        name = re.sub(r"\\[b<>]|\\?\($", "", HEAD_WORDS.sub("", pattern.strip()))  # `def aider\b`, `aider\(`
        if not re.fullmatch(r"[\w.]+", name):  # before any git call: the hook runs on every Bash command
            return 0
        if "cwd" in data:
            os.chdir(data["cwd"])  # the session's directory, not the one the hook was started in
        graph = graphe_root.root() / OUTPUT.name / JSON.name  # ROOT, fixed at import, is the starting directory's
        if not graph.is_file():
            return 0
        names = set()
        for n in json.loads(graph.read_bytes())["nodes"]:  # the names find() designates a node by
            names.update((n["name"], _bare(n["label"])))
            if n["kind"] != "document":  # `BACKLOG.md`'s last segment `md` would designate every document
                names.add(n["name"].rpartition(".")[2])
        if name in names:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext":
                f"graphe: `{name}` is in the code graph; `graphe explain {name}` gives its definition, its callers"
                f" and what it calls, without a grep."}}))
    except Exception:  # noqa: BLE001 - fail-open: a hook's error must never stop the agent's tool
        pass
    return 0


def check() -> int:
    """The coverage of each contribution, read in its sites: the classification of the calls, the most frequent
    names of each verdict, then the alerts; a failure if there is an alert or a dangling link."""
    _, _, dangling, sites = assemble(checking=True)
    alerts = 0
    for who, site_list in sites.items():
        verdicts = Counter(s["verdict"] for s in site_list if "verdict" in s)
        print(f"== {who}: {sum(verdicts.values())} sites classified {dict(verdicts.most_common())}")
        for verdict, n in verdicts.most_common():
            names = Counter(s["text"] for s in site_list if s.get("verdict") == verdict)
            print(f"  {verdict} ({n}): {dict(names.most_common(12))}")
        to_report = [s for s in site_list if "alert" in s]
        alerts += len(to_report)
        print(f"  alerts: {len(to_report)}")
        for s in to_report[:60]:
            print(f"    {s['file']}:{s['line']} {s['text']} ({s['alert']})")
        print()
    print(f"== Graph: {len(dangling)} dangling link(s)")
    for e in dangling[:20]:
        print("  ", e["source"], "->", e["target"], e["relation"], e["source_file"], e["source_location"])
    return 1 if alerts or dangling else 0


# ---------- the git hooks

def _hooks_folder() -> Path:
    r = subprocess.run(["git", "rev-parse", "--git-path", "hooks"], cwd=ROOT, capture_output=True, text=True,
                       check=True)
    folder = Path(r.stdout.strip())
    return folder if folder.is_absolute() else ROOT / folder


def _without_block(text: str) -> str:
    """The hook as it was before `install`, to the byte: the block is an exact addition."""
    for opening, closing in BLOCKS:
        start = text.find("\n" + opening)
        end = text.find(closing, start)
        if start >= 0 and end >= 0:
            # Up to the end of the line that closes the block, LF or CRLF (an editor may have converted the hook): a
            # recognised block is never doubled.
            text = text[:start] + text[end:].partition("\n")[2]
    return text


def _ignore_output() -> None:
    """Adds the output to the host's .gitignore, unless git already ignores it (in whatever form)."""
    if subprocess.run(["git", "check-ignore", "-q", f"{OUTPUT.name}/"], cwd=ROOT).returncode == 0:
        return
    file = ROOT / ".gitignore"
    text = file.read_bytes() if file.exists() else b""  # in bytes: a .gitignore outside UTF-8 stays intact
    file.write_bytes(text + (b"\n" if text and not text.endswith(b"\n") else b"") + f"/{OUTPUT.name}/\n".encode())
    print(f"  .gitignore: /{OUTPUT.name}/ added")


def install(remove: bool = False) -> int:
    """Sets (or removes) the block that rebuilds the graph in each hook; a
    hook already there keeps what it did."""
    folder = _hooks_folder()
    folder.mkdir(parents=True, exist_ok=True)
    # shortcut: `graphe` must be in the PATH of git's shell, else the hook fails silently (the next query rebuilds
    # anyway); an absolute path if a git client does not inherit the PATH.
    block = f"\n{BLOCKS[0][0]} (graphe install)\ngraphe build --quiet >/dev/null 2>&1 &\n{BLOCKS[0][1]}\n"
    for name in HOOKS:
        hook = folder / name
        text = _without_block(hook.read_bytes().decode("utf-8") if hook.exists() else "#!/bin/sh\n")
        if not remove:
            text += block
        # shortcut: a host hook reduced to `#!/bin/sh` is deleted like those install created; to tell apart if a
        # host keeps one.
        if remove and text.strip() in ("", "#!/bin/sh"):
            hook.unlink(missing_ok=True)
            print(f"  {name}: removed")
            continue
        hook.write_bytes(text.encode("utf-8"))
        hook.chmod(0o755)
        print(f"  {name}: {'block removed' if remove else 'set'} ({hook})")
    if not remove:
        _ignore_output()
    return 0


def _option(arguments: list[str], name: str, default: int) -> int:
    return int(arguments[arguments.index(name) + 1]) if name in arguments else default


FLAGS = {"--quiet", "--undirected", "--all", "--source", "--depth", "--remove"}


def main(arguments: list[str] | None = None) -> int:
    """The `graphe` command. An expected error (a RuntimeError: not a git repository, an extension not found, an
    incomplete node) prints one line, `graphe: <message>`; a real bug keeps its traceback (T-0065)."""
    try:
        return _command(sys.argv[1:] if arguments is None else arguments)
    except RuntimeError as e:
        print(f"graphe: {e}", file=sys.stderr)
        return 1


def _command(arguments: list[str]) -> int:
    # Read by another program (an agent, a pipe), cp1252 printed « D?fi ».
    if not sys.stdout.isatty():
        sys.stdout.reconfigure(encoding="utf-8")
    command, rest = (arguments[0], arguments[1:]) if arguments else ("", [])
    if command in ("-h", "--help"):
        print(__doc__)
        return 0
    # An unknown flag ran the command: `install --help` installed the hooks.
    unknown = [a for a in rest if a == "-h" or (a.startswith("--") and a not in FLAGS)]
    if unknown:
        print(__doc__)
        return 0 if set(unknown) <= {"-h", "--help"} else 2
    positionals = [a for i, a in enumerate(rest) if not a.startswith("--")
                   and not (i and rest[i - 1] == "--depth")]
    if command == "build":
        try:
            return build(quiet="--quiet" in rest)
        except Exception:
            if "--quiet" not in rest:
                raise
            import traceback  # noqa: PLC0415 - the error path only
            OUTPUT.mkdir(exist_ok=True)
            (OUTPUT / "error.txt").write_bytes(traceback.format_exc().encode("utf-8"))
            return 1
    if command == "check":
        return check()
    if command == "hook" and not rest:
        return hook()
    if command == "install":
        return install(remove="--remove" in rest)
    if command == "path" and len(positionals) == 2:
        return path(load(), *positionals, undirected="--undirected" in rest)
    if command == "explain" and len(positionals) == 1:
        return explain(load(), positionals[0], all_="--all" in rest, code="--source" in rest)
    if command == "callers" and len(positionals) == 1:
        return callers(load(), positionals[0], _option(rest, "--depth", 2))
    if command == "affected" and len(positionals) <= 1:
        return affected(load(), positionals[0] if positionals else "HEAD", _option(rest, "--depth", 1))
    if command == "search" and len(positionals) == 1:
        return search(load(), positionals[0])
    if command == "view" and len(positionals) <= 1:
        return view(load(), positionals[0] if positionals else None)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
