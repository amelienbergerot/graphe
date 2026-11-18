"""The code graph, client side: the host's GDScript scripts (res://: godot/).

Each .gd script of the host becomes nodes and links, which graphe.py merges
with those of the other readers.

What the reader reads, by patterns and not by a grammar:
- a file, its functions (`func`), its signals;
- `const X = preload("res://...")`: X designates that file;
- a variable typed by X or made by `X.new()`: its calls go to X;
- `X.f(...)`, `f(...)`, `self.f(...)`; a function passed as a value (a
  signal handler); `call_deferred("f")`;

`graphe check` recounts the calls with another reader (Python's tokenize,
`contribute`) and classifies each: our code, the engine (from the API Godot
exports), an anonymous function, ambiguous or unknown. An unlinked call that
bears the name of one of our functions is a miss of the reader.
"""

from __future__ import annotations

import bisect
import io
import json
import re
import subprocess
import sys
import tempfile
import tokenize
from collections import Counter, defaultdict
from pathlib import Path

import graphe_root
from graphe_root import OUTPUT, ROOT

# shortcut: res:// starts at godot/, as in the first host; a .gd elsewhere breaks - look for project.godot if
# needed.
GODOT = ROOT / "godot"

KEYWORDS = {"if", "elif", "while", "for", "match", "return", "and", "or", "not", "in", "is", "as", "func",
            "await", "var", "const", "signal", "static", "class", "extends", "breakpoint", "pass", "else"}
# The language's functions, outside the API the engine exports.
LANGUAGE_BUILTINS = {"preload", "load", "assert", "char", "len", "range", "print_debug", "print_stack", "get_stack",
                     "inst_to_dict", "dict_to_inst", "is_instance_of", "type_exists", "convert", "Color8", "ord",
                     "super", "_init"}
CALLS_BY_NAME = re.compile(r"""\b(?:call_deferred|callv?|has_method|Callable\(\s*self\s*,)\s*\(?\s*"(\w+)\"""")


def scripts() -> list[Path]:
    return graphe_root.files(".gd")


def _id(path: Path) -> str:
    return re.sub(r"\W", "_", str(path.relative_to(ROOT).with_suffix("")).replace("\\", "/")).lower()


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def res(target: str) -> str:
    """The host's file behind `res://target` (`menu/outils.gd` -> `godot/menu/outils.gd`)."""
    return _rel(GODOT / target)


def mask(text: str) -> tuple[str, list[tuple[int, str]]]:
    """The text, strings and comments blanked (quotes and line breaks
    kept), and each string: (start, value)."""
    out = list(text)
    strings = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "#":
            j = text.find("\n", i)
            j = n if j < 0 else j
            out[i:j] = " " * (j - i)
            i = j
        elif c in "\"'":
            end = c * 3 if text.startswith(c * 3, i) else c
            start = j = i + len(end)
            # A plain GDScript string can run over a line break (lectures.gd).
            while j < n and not text.startswith(end, j):
                j += 2 if text[j] == "\\" else 1
            strings.append((i, text[start:j]))
            for k in range(start, min(j, n)):
                if out[k] != "\n":
                    out[k] = " "
            i = j + len(end)
        else:
            i += 1
    return "".join(out), strings


class Script:
    """A script read: its functions, its preload aliases, its typed
    variables, its signals - and, line by line, the function that encloses
    it."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.id = _id(path)
        self.text = path.read_bytes().decode("utf-8")
        self.masked, self.strings = mask(self.text)
        self.lines = self.masked.split("\n")
        self.starts = [0]
        for m in re.finditer("\n", self.masked):
            self.starts.append(m.end())
        self.functions: dict[str, int] = {}
        self.enclosing: list[str | None] = [None] * len(self.lines)
        self.alias: dict[str, str] = {}
        self.types: dict[str, str] = {}
        self.anonymous: set[str] = set()
        self.signals: dict[str, int] = {}
        self._read()

    def line_of(self, position: int) -> int:
        return bisect.bisect_right(self.starts, position)

    def string_at(self, position: int) -> str | None:
        i = bisect.bisect_left(self.strings, (position, ""))
        return self.strings[i][1] if i < len(self.strings) and self.strings[i][0] == position else None

    def _read(self) -> None:
        current, indent = None, -1
        for number, line in enumerate(self.lines):
            content = line.strip()
            shift = len(line) - len(line.lstrip())
            if current and content and shift <= indent:
                current = None
            m = re.match(r"\s*(?:static\s+)?func\s+([A-Za-z_]\w*)\s*\(", line)
            if m:
                current, indent = m.group(1), shift
                self.functions[current] = number + 1
                for name, type_ in re.findall(r"(\w+)\s*:\s*([A-Za-z_]\w*)", line[m.end():]):
                    self.types[name] = type_
            self.enclosing[number] = current
            m = re.match(r"\s*signal\s+(\w+)", line)
            if m:
                self.signals[m.group(1)] = number + 1
        line_start = 0
        for line in self.lines:
            m = re.match(r"\s*(?:@\w+(?:\([^)]*\))?\s+)*(?:static\s+)?(?:const|var)\s+(\w+)\s*(?::\s*([A-Za-z_]\w*))?"
                         r"[^=\n]*?(?::?=\s*(.*))?$", line)
            if m:
                name, type_, value = m.group(1), m.group(2), m.group(3) or ""
                p = re.match(r"(?:pre)?load\(\s*\"", value)
                if p:
                    path = self.string_at(line_start + m.start(3) + p.end() - 1)
                    if path and path.endswith(".gd"):
                        self.alias[name] = path
                else:
                    n = re.match(r"([A-Za-z_]\w*)\.new\(", value)
                    if n:
                        self.types[name] = n.group(1)
                    elif type_:
                        self.types[name] = type_
                    if re.match(r"func\s*\(", value):
                        self.anonymous.add(name)
            line_start += len(line) + 1
        # A variable declared Node, made further down by one of our scripts:
        # that script receives its calls.
        for name, type_ in re.findall(r"(?<![\w.])(\w+)[ \t]*=[ \t]*([A-Za-z_]\w*)\.new\(", self.masked):
            if type_ in self.alias or name not in self.types:
                self.types[name] = type_


class Reader:
    def __init__(self, api: dict | None = None, paths: list[Path] | None = None) -> None:
        self.scripts = {f"res://{s.relative_to(GODOT).as_posix()}": Script(s)
                        for s in (scripts() if paths is None else paths)}
        self.by_name: dict[str, list[Script]] = defaultdict(list)
        for s in self.scripts.values():
            for name in s.functions:
                self.by_name[name].append(s)
        # Without GDScript, no Godot to run.
        self.engine_methods, self.engine_names = _engine_api(api) if self.scripts else (set(), set())
        self.nodes: list[dict] = []
        self.links: list[dict] = []
        self.sites: list[dict] = []
        for s in self.scripts.values():
            self._nodes(s)
        for s in self.scripts.values():
            self._calls(s)

    def _node(self, s: Script, id_: str, label: str, line: int, kind: str, name: str) -> None:
        self.nodes.append({"id": id_, "label": label, "kind": kind, "source_file": _rel(s.path),
                           "source_location": f"L{line}", "name": name})

    def _link(self, s: Script, source: str, target: str, relation: str, line: int, sure: bool = True,
              context: str = "") -> None:
        self.links.append({"source": source, "target": target, "relation": relation,
                           "confidence": "EXTRACTED" if sure else "INFERRED", "context": context,
                           "source_file": _rel(s.path), "source_location": f"L{line}"})

    def _nodes(self, s: Script) -> None:
        self._node(s, s.id, s.path.name, 1, "file", _rel(s.path))
        for name, line in s.functions.items():
            self._node(s, f"{s.id}_{name.lower()}", f"{name}()", line, "function", name)
            self._link(s, s.id, f"{s.id}_{name.lower()}", "contains", line)
        for name, line in s.signals.items():
            self._node(s, f"{s.id}_signal_{name.lower()}", f"{name} (signal)", line, "signal", name)
            self._link(s, s.id, f"{s.id}_signal_{name.lower()}", "contains", line)
        for alias, path in s.alias.items():
            if path in self.scripts:
                self._link(s, s.id, self.scripts[path].id, "imports", 1, context=alias)

    def _context(self, s: Script, line: int) -> str:
        name = s.enclosing[line - 1]
        return f"{s.id}_{name.lower()}" if name else s.id

    def _script_of(self, s: Script, receiver: str) -> Script | None:
        """The script a receiver designates: an alias, or a variable typed
        by an alias."""
        bearer = s
        for i, segment in enumerate(receiver.split(".")):
            if i == 0 and segment in bearer.alias:
                target = bearer.alias[segment]
            elif bearer.types.get(segment) in bearer.alias:
                target = bearer.alias[bearer.types[segment]]
            else:
                return None
            bearer = self.scripts.get(target)
            if bearer is None:
                return None
        return bearer

    def _calls(self, s: Script) -> None:
        for m in re.finditer(r"\b([A-Za-z_]\w*)[ \t]*\(", s.masked):
            name = m.group(1)
            before = s.masked[max(0, m.start() - 200):m.start()].rstrip()  # a window: the whole prefix made reading quadratic
            if name in KEYWORDS or re.search(r"\b(?:func|signal)$", before):
                continue
            receiver = ""
            if before.endswith("."):
                r = re.search(r"([A-Za-z_][\w.]*)\s*\.$", before)
                receiver = r.group(1) if r and not before[:r.start()].rstrip().endswith(".") else "<expr>"
                receiver = receiver.removeprefix("self.")
                if receiver == "self":
                    receiver = ""
            line = s.line_of(m.start())
            self.sites.append({"script": s, "line": line, "name": name, "receiver": receiver,
                               **self._resolve(s, name, receiver, line, m.end())})
        for m in re.finditer(r"(?<![.\w])([A-Za-z_]\w*)(?:\.([A-Za-z_]\w*))?\b(?!\s*\()", s.masked):
            head, member = m.group(1), m.group(2)
            line = s.line_of(m.start())
            before = s.masked[max(0, m.start() - 20):m.start()].rstrip()
            if re.search(r"\bfunc$", before):
                continue
            if member is None and head in s.functions:
                self._link(s, self._context(s, line), f"{s.id}_{head.lower()}", "references", line)
            elif member and head in s.alias and s.alias[head] in self.scripts:
                target = self.scripts[s.alias[head]]
                if member in target.functions:
                    self._link(s, self._context(s, line), f"{target.id}_{member.lower()}", "references", line)
        for m in CALLS_BY_NAME.finditer(s.text):
            if s.masked[m.start()] == s.text[m.start()] and m.group(1) in s.functions:
                line = s.line_of(m.start())
                self._link(s, self._context(s, line), f"{s.id}_{m.group(1).lower()}", "indirect_call", line)

    def _resolve(self, s: Script, name: str, receiver: str, line: int, after: int) -> dict:
        source = self._context(s, line)
        if not receiver:
            if name in s.functions:
                self._link(s, source, f"{s.id}_{name.lower()}", "calls", line)
                return {"verdict": "ours"}
            if name in LANGUAGE_BUILTINS or name in self.engine_names or name in self.engine_methods:
                return {"verdict": "engine"}
            return {"verdict": "unknown"}
        target = self._script_of(s, receiver)
        if target is not None:
            if name in target.functions:
                self._link(s, source, f"{target.id}_{name.lower()}", "calls", line)
                return {"verdict": "ours"}
            if name == "new":
                self._link(s, source, target.id, "uses", line, context="new")
                return {"verdict": "ours"}
            return {"verdict": "engine" if name in self.engine_methods else "unknown"}
        last = receiver.split(".")[-1]
        if name in ("connect", "emit", "disconnect", "is_connected"):
            bearer = s if last == receiver else self._script_of(s, receiver.rsplit(".", 1)[0])
            if bearer is not None and last in bearer.signals:
                relation = "emits" if name == "emit" else "connects"
                self._link(s, source, f"{bearer.id}_signal_{last.lower()}", relation, line)
                return {"verdict": "ours"}
            return {"verdict": "engine"}
        if name == "call" and last in s.anonymous:
            return {"verdict": "anonymous"}
        head = receiver.split(".")[0]
        if (head in self.engine_names or (receiver == head and s.types.get(head) in self.engine_names)) \
                and (name in self.engine_methods or name not in self.by_name):
            return {"verdict": "engine"}
        ours = self.by_name.get(name, [])
        if ours and name not in self.engine_methods:
            for other in ours:
                self._link(s, source, f"{other.id}_{name.lower()}", "calls", line, sure=False)
            return {"verdict": "ours?" if len(ours) == 1 else "ambiguous"}
        if name in self.engine_methods:
            return {"verdict": "ambiguous" if ours else "engine"}
        return {"verdict": "unknown"}


def _engine_api(api: dict | None) -> tuple[set[str], set[str]]:
    """The methods and the names (classes, global functions) of the API
    Godot exports (--dump-extension-api)."""
    cached = OUTPUT / "extension_api.json"
    if api is None and not cached.exists():
        # Looked for after the cache: a frozen tree can receive the API without Godot.
        godot = graphe_root.executable("godot", "godot")
        if godot is None:
            return set(), set()  # nothing in cache: the key, once set, serves at the next build
        with tempfile.TemporaryDirectory() as folder:
            try:
                subprocess.run([str(godot), "--headless", "--dump-extension-api"], cwd=folder,
                               capture_output=True, timeout=180, check=False)
                raw = (Path(folder) / "extension_api.json").read_bytes()
                api = json.loads(raw)  # a broken JSON stays out of the cache: it would break every build
            except (OSError, ValueError, subprocess.SubprocessError) as e:
                print(f"graphe: {godot} ([godot] executable) did not give the engine API ({e}):"
                      " its calls stay unresolved", file=sys.stderr)
                return set(), set()
        OUTPUT.mkdir(exist_ok=True)
        cached.write_bytes(raw)
    if api is None:
        api = json.loads(cached.read_bytes())
    methods, names = set(), set()
    for class_ in api["classes"] + api["builtin_classes"]:
        names.add(class_["name"])
        methods |= {m["name"] for m in class_.get("methods", [])}
        methods |= {s["name"] for s in class_.get("signals", [])}
    names |= {f["name"] for f in api["utility_functions"]}
    names |= {s["name"] for s in api["singletons"]}
    return methods, names


# ---------- check

def _calls_by_tokenize(path: Path) -> Counter:
    """A script's calls, read by another reader: Python's tokenize (GDScript
    looks enough like it: strings, comments, indentation). A name followed
    by a parenthesis, outside a definition. A plain string that runs over a
    line break, which Python refuses, gets a continuation backslash where it
    stops: the line numbers stay."""
    lines = path.read_bytes().decode("utf-8").split("\n")
    while True:
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO("\n".join(lines)).readline))
            break
        except tokenize.TokenError as e:
            if "unterminated string" not in e.args[0]:
                raise
            lines[e.args[1][0] - 1] += "\\"
    sites = Counter()
    for i, token in enumerate(tokens[:-1]):
        following = tokens[i + 1]
        preceding = tokens[i - 1] if i else None
        if token.type == tokenize.NAME and following.string == "(" and token.string not in KEYWORDS \
                and not (preceding and preceding.string in ("func", "signal")):
            sites[(token.start[0], token.string)] += 1
    return sites


def contribute(project) -> dict:
    """The GDScript reader's contribution (docs/contribution.md): a site per call, and its alerts.

    Under `graphe check`, the calls are recounted by another reader (Python's tokenize): a missed call is an
    alert.
    """
    reader = Reader(paths=project.files(".gd"))
    ids = {n["id"] for n in reader.nodes}
    sites = []
    for s in reader.sites:
        site = {"verdict": s["verdict"], "file": _rel(s["script"].path), "line": s["line"], "name": s["name"],
                "text": f"{s['receiver'] or '-'}.{s['name']}"}
        if s["verdict"] == "unknown" and s["name"] in reader.by_name:
            site["alert"] = "not linked to the name of one of our functions"
        sites.append(site)
    if project.checking:
        read_calls = Counter((_rel(site["script"].path), site["line"], site["name"]) for site in reader.sites)
        recounted = Counter()
        for s in reader.scripts.values():
            for (line, name), n in _calls_by_tokenize(s.path).items():
                recounted[(_rel(s.path), line, name)] += n
        # A call too many never made check fail: only the misses are alerts.
        for (file, line, name), n in sorted((recounted - read_calls).items()):
            sites += [{"file": file, "line": line, "name": name, "text": name, "alert": "missed by the reader"}] * n
    return {"nodes": reader.nodes, "sites": sites, "links": [e for e in reader.links if e["target"] in ids]}
