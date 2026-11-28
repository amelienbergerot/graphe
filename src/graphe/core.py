"""The core: what the graph draws from the text of the sources, once the
readers have run (BACKLOG.md).

For each function, method, command or action:
- `end`: its last line - the first non-blank line that comes back to its
  indentation closes its body (Python, GDScript and PHP are read alike);
  `explain X --source` prints its lines;
- `texts`: the texts it displays, by the `displayed_text` pattern of
  graphe.toml (T-0009) - a text seen on screen leads to its code; without a
  pattern, none;
- `notes`: the comment just above it - a concept said in a comment
  (« clarte ») leads to the function that has it.

And:
- a node per module variable or constant (Python: an assignment in column
  0; GDScript: `const`/`var` in column 0, except `preload`), linked to the
  functions that read it (`reads`) or write it (`writes`) - in its file by
  the name, elsewhere by `X.NAME` when that name exists only once;
- a class and its fields have their end and their comment;
- Python: `alias.CONSTANT`, where `alias` is a module imported under that
  name, reads that module's constant (EXTRACTED);
- a node per document (T-0010): each Markdown file of the host, restricted
  by `[documents] patterns` (graphe.toml). A document whose name starts with
  an identifier (`[documents] identifier`, `T-` and four digits by default)
  is a ticket: the code that contains its identifier (in its body or its
  comment) and the other documents lead to it by `cites`. A document leads
  to the functions it names between backticks (`names`, by the name);
- T-0095: with `[tickets] github` (graphe.toml, issues.py), an issue whose
  title starts with an identifier is that ticket, before a file of the same
  identifier (then a document); its body and its comments cite and name as
  a document's text does, located at the issue's or the comment's URL;
- a `value` node per string (an identifier, `"coupee"`) written both in
  Python and in GDScript, linked to each body that writes it (`value`): what
  one side emits and what the other compares;
- a keyed link (T-0047, `[keys]` of graphe.toml): `sends` from the body
  that names a key (`api("zones")`) to the code that answers it
  (`$chemin === '/api/zones'`), where no name joins them.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import networkx as nx

from graphe import godot, issues, python
from graphe import root as graphe_root  # `root` is the host's path in this module's signatures

# A declaration (`abstract`, T-0081) has no body, but a line, a comment and tickets it cites, as a body.
BODIES = {"function", "method", "command", "action", "class", "abstract"}
# An extent and a comment, without being a body that owns its lines.
EXTENDED = BODIES | {"field"}
PY_ALIAS = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import\s+(\w+)(?:\s+as\s+(\w+))?|import\s+([\w.]+)\s+as\s+(\w+))\s*(?:#.*)?$")
PY_QUALIFIED = re.compile(r"\b([a-z_]\w*)\.(\w+)\b")
# T-0010: a document's default identifier (`[documents] identifier`), that of tickets.
IDENTIFIER = r"\bT-\d{4}\b"
NAMED = re.compile(r"`([A-Za-z_][\w.]*?)(?:\([^`]*\))?`")  # `f`, `f()`, and `f(a, b)` (T-0024)
PY_VARIABLE = re.compile(r"^([A-Za-z_]\w*)\s*(?::[^=]+)?=(?!=)")
GD_VARIABLE = re.compile(r"^(?:static\s+)?(const|var)\s+(\w+)\b(.*)$")
PRELOAD = re.compile(r'^const\s+(\w+)\s*=\s*preload\("res://([^"]+\.gd)"\)', re.M)
QUALIFIED = re.compile(r"\b([A-Z]\w*)\.(\w+)\b")
# Each word right after `x.`: what `elsewhere` (enrich) can find, and more.
AFTER_DOT = re.compile(r"(?<=\w\.)\w+")
# Names too common to be followed from one file to another by the name.
NAME_MIN = 4
VALUE = re.compile(r'"([a-z][a-z0-9_]{3,})"')
VALUE_FILES_MAX = 8
VALUE_BODIES_MAX = 10


def _indent(line: str) -> int:
    if "\t" in line:
        line = line.expandtabs(4)
    return len(line) - len(line.lstrip())


# How a comment line starts, stripped (`_comment` is not None): one call where enrich tests every line (T-0091).
COMMENTS = ("#", "//", "/*", "*")


def _comment(line: str) -> str | None:
    s = line.strip()
    for start in ("#", "//", "/**", "/*", "*"):
        if s.startswith(start):
            return s[len(start):].strip().removesuffix("*/").strip()
    return None


STRING = re.compile(r'"""|\'\'\'|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')


def _scan(line: str, quote: str) -> tuple[int, str]:
    """T-0083: the line's `(` minus its `)`, outside its strings, and the triple quote still open at its end ("" for
    none), `quote` being the one open at its start."""
    if not quote and '"' not in line and "'" not in line:  # T-0091: no string, most lines
        return line.count("(") - line.count(")"), ""
    depth, i = 0, 0
    while i < len(line):
        if quote:
            j = line.find(quote, i)
            if j < 0:
                return depth, quote
            i, quote = j + 3, ""
            continue
        m = STRING.search(line, i)
        piece = line[i:m.start() if m else len(line)]
        depth += piece.count("(") - piece.count(")")
        if not m:
            break
        quote = m[0] if m[0] in ('"""', "'''") else ""
        i = m.end()
    return depth, quote


def extent(lines: list[str], start: int) -> int:
    """The last line (1 = the first of the file) of the block that starts at
    `start`: before the first non-blank line, outside a comment and a string,
    that comes back to the indentation of `start` or less. A closing `}` or
    `)` at that indentation belongs to the block, and a `{` alone on its line
    right after the signature."""
    if start < 1 or start > len(lines):
        return start
    base = _indent(lines[start - 1])
    end = start
    open_, quote = _scan(lines[start - 1], "")
    body = False  # a line of the body seen
    for i in range(start, len(lines)):
        line = lines[i]
        s = line.strip()
        if quote:  # T-0083: in a string over several lines, whatever its indentation
            _, quote = _scan(line, quote)
            end = i + 1
            continue
        indent = _indent(line) if s else 0
        # a signature over several lines; a line back at its indentation ends it, unless it closes a bracket
        if open_ > 0 and not (s and indent <= base and s[0] not in "})]"):
            depth, quote = _scan(line, "")
            open_ += depth
            end = i + 1
            continue
        open_ = 0
        if not s or indent > base and s.startswith(COMMENTS):
            continue
        if indent <= base:
            if s == "{" and indent == base and not body:  # the brace on its own line (PHP's PSR-12)
                end = i + 1
                continue
            if s[0] in "})]" and indent == base:
                end = i + 1
            break
        _, quote = _scan(line, "")  # a docstring that opens here
        end, body = i + 1, True
    return end


def notes(lines: list[str], start: int) -> str:
    """The comment just above line `start` (decorators skipped), on one
    line."""
    i = start - 2
    while i >= 0 and lines[i].strip().startswith("@"):
        i -= 1
    pieces = []
    while i >= 0:
        text = _comment(lines[i])
        if text is None:
            break
        pieces.append(text)
        i -= 1
    return " ".join(reversed([p for p in pieces if p]))


def _variables(rel: str, lines: list[str]) -> list[tuple[str, int, str]]:
    """(name, line, kind) of the module variables and constants."""
    found = []
    if rel.endswith(".py"):
        for i, line in enumerate(lines, start=1):
            m = PY_VARIABLE.match(line)
            if m and m.group(1) not in ("__all__",):
                name = m.group(1)
                found.append((name, i, "constant" if name.lstrip("_").isupper() else "variable"))
    elif rel.endswith(".gd"):
        for i, line in enumerate(lines, start=1):
            m = GD_VARIABLE.match(line)
            if m and "preload(" not in m.group(3) and "load(" not in m.group(3):
                found.append((m.group(2), i, "constant" if m.group(1) == "const" else "variable"))
    seen = set()
    return [t for t in found if not (t[0] in seen or seen.add(t[0]))]


def _add_link(graph: nx.DiGraph, s: str, t: str, relation: str, location: str, confidence: str) -> None:
    if graph.has_edge(s, t):
        d = graph[s][t]
        d["relations"].add(relation)
        if location not in d["locations"]:
            d["locations"].append(location)
    else:
        graph.add_edge(s, t, relations={relation}, confidence=confidence, locations=[location], contexts=[])


def _pattern(raw, where: str, group: str | None) -> re.Pattern | None:
    """A pattern of graphe.toml; `group` names what its only group holds (None: no group required)."""
    if raw is None:
        return None
    try:
        pattern = re.compile(raw)
    except (re.error, TypeError) as e:
        raise RuntimeError(f"{where} ({graphe_root.CONFIGURATION}): {e}") from None
    if group and pattern.groups != 1:
        raise RuntimeError(f"{where} ({graphe_root.CONFIGURATION}): it needs exactly one group, the "
                           f"{group}; it has {pattern.groups}")
    return pattern


def displayed_text_pattern(root: Path) -> re.Pattern | None:
    """`displayed_text` (graphe.toml): the pattern of a call that displays a text, the text in its only group."""
    return _pattern(graphe_root.configuration(root).get("displayed_text"), "displayed_text", "displayed text")


def _key_patterns(root: Path) -> tuple[re.Pattern, re.Pattern, re.Pattern | None] | None:
    """`[keys]` (graphe.toml, T-0047): where the code names a key, where it answers it, what is a parameter."""
    keys = graphe_root.configuration(root).get("keys")
    if keys is None:
        return None
    for required in ("names", "answers"):
        if required not in keys:
            raise RuntimeError(f"keys ({graphe_root.CONFIGURATION}): it needs `{required}`")
    return (_pattern(keys["names"], "keys.names", "key"), _pattern(keys["answers"], "keys.answers", "key"),
            _pattern(keys.get("parameters"), "keys.parameters", None))


def enrich(graph: nx.DiGraph, root: Path, listed: set[str] | None = None) -> None:
    """`root` is a git repository: the documents are its Markdown files that git tracks (graphe_root.files), from
    `listed` when the build has listed them."""
    displays = displayed_text_pattern(root)
    by_file: dict[str, list[str]] = defaultdict(list)
    for n, d in graph.nodes(data=True):
        by_file[d["source_file"]].append(n)
    file_lines: dict[str, list[str]] = {}
    for rel in by_file:
        path = root / rel
        if path.is_file():
            file_lines[rel] = path.read_bytes().decode("utf-8", "replace").splitlines()

    # The bodies: end, texts, notes.
    bodies: dict[str, tuple[str, int, int]] = {}
    for rel, ids in by_file.items():
        lines = file_lines.get(rel)
        if lines is None:
            continue
        for n in ids:
            d = graph.nodes[n]
            if d["kind"] not in EXTENDED:
                continue
            start = int(d["source_location"].lstrip("L") or 0)
            end = extent(lines, start)
            d["end"] = end
            text = "\n".join(lines[start - 1:end])
            found = [t.replace('\\"', '"') for t in displays.findall(text)] if displays else []
            if found:
                d["texts"] = found
            note = notes(lines, start)
            if note:
                d["notes"] = note
            if d["kind"] in BODIES:
                bodies[n] = (rel, start, end)

    # Each line has its owner: the smallest body that contains it - the
    # branch of a command rather than the function that dispatches (its
    # calls too: an extension's takeovers, T-0008). The head line is not a
    # use.
    owners: dict[str, dict[int, str]] = defaultdict(dict)
    for n, (rel, start, end) in sorted(bodies.items(), key=lambda b: b[1][2] - b[1][1], reverse=True):
        for i in range(start + 1, end + 1):
            owners[rel][i] = n

    # Module variables and constants.
    file_id = {graph.nodes[n]["source_file"]: n for n in graph.nodes if graph.nodes[n]["kind"] == "file"}
    variables: dict[str, dict[str, str]] = defaultdict(dict)  # file -> name -> id
    module_names: dict[str, list[str]] = defaultdict(list)
    for rel, lines in file_lines.items():
        fid = file_id.get(rel)
        if fid is None:
            continue
        for name, line, kind in _variables(rel, lines):
            vid = f"{fid}_{name.lower()}"
            if vid in graph:
                vid += "_" + kind
            graph.add_node(vid, id=vid, label=name, kind=kind, source_file=rel, source_location=f"L{line}",
                           name=name, end=extent(lines, line))
            note = notes(lines, line)
            if note:
                graph.nodes[vid]["notes"] = note
            _add_link(graph, fid, vid, "contains", f"{rel}:{line}", "EXTRACTED")
            variables[rel][name] = vid
            module_names[name].append(vid)
    unique = {name: ids[0] for name, ids in module_names.items() if len(ids) == 1 and len(name) >= NAME_MIN}
    elsewhere = re.compile(r"\b\w+\.(" + "|".join(sorted(map(re.escape, unique), key=len, reverse=True)) + r")\b") \
        if unique else None
    write = r"\s*(?:[-+*/]?=(?!=)|\.(?:append|extend|clear|pop|update|insert|remove|add|discard|erase)\()"
    uses: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    # T-0096: by import name, None when two files bear it; named from the files the reader reads, those that do not
    # parse included, so that both name a module alike
    py_modules: dict[str, str | None] = {}
    py_files = [p.relative_to(root).as_posix() for p in graphe_root.files(".py", root, listed)]
    for rel, name in python.import_names(py_files).items():
        py_modules[name] = None if name in py_modules else rel
    for rel, lines in file_lines.items():
        local = variables.get(rel, {})
        # GDScript: `Script.CONSTANT`, where Script preloads a script (res://: godot/, godot.GODOT).
        alias = {name: godot.res(target) for name, target in PRELOAD.findall("\n".join(lines))} \
            if rel.endswith(".gd") else {}
        # Python: `alias.CONSTANT`, alias a module imported under that name.
        py_alias = _python_aliases(lines, py_modules) if rel.endswith(".py") else {}
        here = re.compile(r"(?<![\w.])(" + "|".join(sorted(map(re.escape, local), key=len, reverse=True)) + r")\b") \
            if local else None
        for i, n in owners.get(rel, {}).items():
            line = lines[i - 1]
            if line.strip().startswith(COMMENTS):
                continue
            location = f"{rel}:{i}"
            if here is not None:
                for m in here.finditer(line):
                    writes = re.match(write, line[m.end():])
                    _add_link(graph, n, local[m.group(1)], "writes" if writes else "reads", location, "EXTRACTED")
            if alias and "." in line:
                for head, name in set(QUALIFIED.findall(line)):
                    vid = variables.get(alias.get(head, ""), {}).get(name)
                    if vid:
                        _add_link(graph, n, vid, "reads", location, "EXTRACTED")
            elif (py_alias or elsewhere is not None) and "." in line:
                sure = set()
                for head, name in set(PY_QUALIFIED.findall(line)) if py_alias else ():
                    vid = variables.get(py_alias.get(head, ""), {}).get(name)
                    if vid:
                        _add_link(graph, n, vid, "reads", location, "EXTRACTED")
                        sure.add(name)
                # T-0091: `elsewhere` tried only where a word after `x.` is one of its names, its alternation slow.
                found = set(elsewhere.findall(line)) if not unique.keys().isdisjoint(AFTER_DOT.findall(line)) else set()
                for name in found - sure:
                    vid = unique[name]
                    # `examen.graine` in Python does not read a GDScript variable.
                    other = graph.nodes[vid]["source_file"]
                    if other != rel and Path(other).suffix == Path(rel).suffix:
                        _add_link(graph, n, vid, "reads", location, "INFERRED")
            # T-0354: values written in one language and read in the other.
            if '"' in line and rel.endswith((".py", ".gd")):
                for v in set(VALUE.findall(line)):
                    uses[v].append((n, location, Path(rel).suffix))

    _link_values(graph, uses)
    keys = _key_patterns(root)
    if keys:
        _link_keys(graph, keys, file_lines, bodies, file_id)
    _link_documents(graph, root, bodies, file_lines, listed)


def _link_keys(graph: nx.DiGraph, keys: tuple[re.Pattern, re.Pattern, re.Pattern | None],
               file_lines: dict[str, list[str]], bodies: dict[str, tuple[str, int, int]],
               file_id: dict[str, str]) -> None:
    """T-0047: a keyed link (`sends`), from the body that names a key to the code that answers it: what the
    answering line calls, else its body (not its file). Two keys match when equal, `*` for each parameter."""
    names, answers, parameters = keys
    # The head line too: a one-line arrow (`f = () => api("zones")`) names on it.
    holders: dict[str, dict[int, str]] = defaultdict(dict)
    for n, (rel, start, end) in sorted(bodies.items(), key=lambda b: b[1][2] - b[1][1], reverse=True):
        for i in range(start, end + 1):
            holders[rel][i] = n
    called: dict[str, list[str]] = defaultdict(list)
    for _, t, d in graph.edges(data=True):
        if "calls" in d["relations"]:
            for location in d["locations"]:
                called[location].append(t)

    def key(raw: str) -> str:
        return parameters.sub("*", raw) if parameters else raw

    # shortcut: a route's HTTP method is no part of its key (4cast checks it on another line than the path), so
    # GET and POST of a path lead to the same code; to take it in when a host answers them apart.
    # shortcut: a call in the answering condition (`$chemin === '/api/x' && autorise()`) answers in place of the
    # body; to take only the calls after the key when a host's router does that.
    named: list[tuple[str, str, str]] = []
    answerers: dict[str, set[str]] = defaultdict(set)
    for rel, lines in file_lines.items():
        for i, line in enumerate(lines, 1):
            if _comment(line) is not None:
                continue
            body = holders[rel].get(i)
            location = f"{rel}:{i}"
            if namer := body or file_id.get(rel):
                named += [(namer, key(m.group(1)), location) for m in names.finditer(line)]
            # Not a file: its top-level router calls every route, `callers` would go from one route to all.
            if answerer := called.get(location) or ([body] if body else []):
                for m in answers.finditer(line):
                    answerers[key(m.group(1))].update(answerer)
    for n, k, location in named:
        for t in sorted(answerers.get(k, ())):
            if t != n:
                _add_link(graph, n, t, "sends", location, "INFERRED")
                if k not in graph[n][t]["contexts"]:
                    graph[n][t]["contexts"].append(k)


def _link_values(graph: nx.DiGraph, uses: dict[str, list[tuple[str, str, str]]]) -> None:
    """T-0354: a value written in Python and in GDScript becomes a node; its
    name keeps its quotes, so as not to make ambiguous the name of a
    function spelled the same. A value written in more than
    VALUE_FILES_MAX files (`"name"`, `"tick"`) says nothing and shortened
    one undirected path in three: no node."""
    for v, us in sorted(uses.items()):
        if {s for _, _, s in us} != {".py", ".gd"}:
            continue
        if (len({location.rsplit(":", 1)[0] for _, location, _ in us}) > VALUE_FILES_MAX
                or len({n for n, _, _ in us}) > VALUE_BODIES_MAX):
            continue
        vid = f"value_{v}"
        rel, line = min(location for _, location, s in us if s == ".py").rsplit(":", 1)
        graph.add_node(vid, id=vid, label=f'"{v}"', kind="value", source_file=rel, source_location=f"L{line}",
                       name=f'"{v}"', end=int(line))
        for n, location, _ in us:
            _add_link(graph, n, vid, "value", location, "EXTRACTED")


def _python_aliases(lines: list[str], modules: dict[str, str | None]) -> dict[str, str]:
    """The modules imported under a name: name -> file, a module found by its import name (`modules`)."""
    alias = {}
    for line in lines:
        m = PY_ALIAS.match(line)
        if not m:
            continue
        if m.group(1):
            module, name = f"{m.group(1)}.{m.group(2)}", m.group(3) or m.group(2)
        else:
            module, name = m.group(4), m.group(5)
        if modules.get(module):
            alias[name] = modules[module]
    return alias


def _documents(root: Path) -> tuple[re.Pattern, list[str] | None]:
    """`[documents]` (graphe.toml): the pattern of a document's identifier (IDENTIFIER otherwise), and the
    patterns that restrict the documents (None: all Markdown files)."""
    table = graphe_root.configuration(root).get("documents", {})
    if not isinstance(table, dict):
        raise RuntimeError(f"documents ({graphe_root.CONFIGURATION}): [documents] must be a table")
    try:
        pattern = re.compile(table.get("identifier", IDENTIFIER))
    except (re.error, TypeError) as e:
        raise RuntimeError(f"[documents] identifier ({graphe_root.CONFIGURATION}): {e}") from None
    restricted = table.get("patterns")
    if restricted is not None and not (isinstance(restricted, list) and all(isinstance(m, str) for m in restricted)):
        raise RuntimeError(f"[documents] patterns ({graphe_root.CONFIGURATION}): it must be a list of patterns")
    return pattern, restricted


def _document_id(prefix: str, name: str) -> str:
    return prefix + re.sub(r"\W+", "_", name.lower()).strip("_")


def _cited(pattern: re.Pattern, text: str) -> set[str]:
    return {m.group(0) for m in pattern.finditer(text) if m.group(0)}


def _link_documents(graph: nx.DiGraph, root: Path, bodies: dict, texts: dict[str, list[str]],
                    listed: set[str] | None) -> None:
    """T-0010: each Markdown file of the host (`[documents] patterns` restricts them) is a document. One whose
    name starts with an identifier is a ticket, unless an issue is (T-0095); it is cited by the code and by the
    documents and issues that contain it.
    A document names the functions it writes between backticks."""
    pattern, restricted = _documents(root)
    tickets: dict[str, str] = {}  # identifier -> id
    documents = []  # (id, its file or an URL, its text)
    # T-0095: an issue whose title starts with an identifier is its ticket, before a file of that identifier; located
    # at its URL, without a line, its body at it, each comment at its own.
    for issue in issues.tickets(root):
        m = pattern.match(issue["title"])
        if not (m and m.group(0)) or m.group(0) in tickets:
            continue
        name = m.group(0)
        tickets[name] = did = _document_id("ticket_", name)
        graph.add_node(did, id=did, label=name, kind="ticket", source_file=issue["url"], source_location="",
                       name=name, notes=issue["title"][m.end():].lstrip(" :-") or name)
        documents += [(did, issue["url"], issue["body"])] + [(did, c["url"], c["body"]) for c in issue["comments"]]
    for path in graphe_root.files(".md", root, listed):
        rel = path.relative_to(root).as_posix()
        if restricted is not None and not graphe_root.designates(rel, restricted):
            continue
        text = path.read_bytes().decode("utf-8", "replace")
        title = next((line.split(":", 1)[1].strip() for line in text.splitlines()[:8]
                      if line.startswith("title:")), path.stem)
        m = pattern.match(path.name)
        # shortcut: two files with the same identifier, the second is only a document; and two names that differ
        # only by punctuation (`a-b.md`, `a_b.md`) make a single node. To revisit if a host has some.
        if m and m.group(0) and m.group(0) not in tickets:
            name, kind = m.group(0), "ticket"
            tickets[name] = did = _document_id("ticket_", name)
        else:
            name, kind, did = rel, "document", _document_id("document_", rel)
        graph.add_node(did, id=did, label=name, kind=kind, source_file=rel, source_location="L1",
                       name=name, notes=title, end=len(text.splitlines()))
        documents.append((did, rel, text))
    # The code that cites a ticket, in its body or its comment.
    # T-0091: a body's text is a piece of its file's cut at line ends, where `\b` holds as at the ends of a text: with
    # the default identifier, a file that has none has no body that cites. shortcut: another identifier (`^`, a
    # lookbehind) can match in a piece and not in the whole, so its bodies are each searched; to test it on the
    # whole file too when a host with one needs the time.
    # `T-` first: the pattern starts with `\b`, which `re` tries at each character.
    somewhere = {rel: "T-" in (text := "\n".join(lines)) and pattern.search(text) is not None
                 for rel, lines in texts.items()} if pattern.pattern == IDENTIFIER else {}
    for n, (rel, start, end) in bodies.items():
        lines = texts.get(rel, []) if somewhere.get(rel, True) else []
        cited = _cited(pattern, "\n".join(lines[start - 1:end])) | _cited(pattern, graph.nodes[n].get("notes", ""))
        for ident in sorted(cited):
            if ident in tickets:
                _add_link(graph, n, tickets[ident], "cites", f"{rel}:{start}", "EXTRACTED")
    # The tickets a document cites, and the functions it names: a name borne by a single body.
    bearers: dict[str, list[str]] = defaultdict(list)
    for n in bodies:
        d = graph.nodes[n]
        if d["kind"] in ("function", "method", "class"):
            bearers[d["name"].rsplit(".", 1)[-1]].append(n)
    for did, rel, text in documents:
        url = "://" in rel  # an issue's text: no line
        for i, line in enumerate(text.splitlines(), start=1):
            for ident in sorted(_cited(pattern, line)):
                if ident in tickets and tickets[ident] != did:  # not from itself to itself
                    _add_link(graph, did, tickets[ident], "cites", rel if url else f"{rel}:{i}", "EXTRACTED")
        for name in set(NAMED.findall(text)):
            last = name.rsplit(".", 1)[-1]
            if len(last) >= NAME_MIN and len(bearers.get(last, [])) == 1:
                _add_link(graph, did, bearers[last][0], "names", rel, "INFERRED")


def lines_without_comments(lines: list[str]) -> list[str]:
    return [line for line in lines if _comment(line) is None]
