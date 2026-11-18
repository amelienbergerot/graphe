"""The host's JavaScript in the code graph (T-0014): `.js` and `.mjs`, read by tree-sitter (ADR 0002); `.ts` and the
`<script>` of a `.svelte` component (T-0015) by the TypeScript grammar, the markup blanked out to keep the lines.

- a node per file, per top-level function (`function f`, `const f = () =>`), per class and per method
  (`Class.method`); the calls in a nested function belong to the function that contains it;
- the imports of our files (relative specifiers, re-exports followed): `imports` between files, and a call to an
  imported name leads to its definition;
- a call is sure (EXTRACTED) by a top-level definition, an import, a namespace (`import * as`, `export * as`),
  `this.m()` in a class or its parents, or `Class.m()`; by the name alone (INFERRED) for `x.m()` when one of our
  methods only has that name, or for a name defined once in the host. A parameter or a variable of the function
  hides an import of the same name: its calls are `local`.

The ids carry the extension (`src_zones_mjs`, `src_tableau_svelte`): `zones.py` is the Python reader's `src_zones`.
"""

from __future__ import annotations

import posixpath
import re
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple

import tree_sitter
import tree_sitter_javascript
import tree_sitter_typescript

JS = tree_sitter.Parser(tree_sitter.Language(tree_sitter_javascript.language()))
TS = tree_sitter.Parser(tree_sitter.Language(tree_sitter_typescript.language_typescript()))
PARSERS = {".js": JS, ".mjs": JS, ".ts": TS, ".svelte": TS}
# The suffixes a relative specifier may leave out (`./lib/eau` is `./lib/eau.ts`); a component is imported with its
# `.svelte`. shortcut: neither `.tsx` nor NodeNext's `./x.js` for `x.ts`; to add when a host has some.
SUFFIXES = (".js", ".mjs", ".ts")
# shortcut: by a pattern, so a `</script>` in a string of the script ends it, and the markup's `{...}` are not read
# (BACKLOG.md, 4cast); to parse the markup when its calls are needed.
SCRIPT = re.compile(rb"<script\b[^>]*>(.*?)</script>", re.S)
FUNCTIONS = {"function_declaration", "generator_function_declaration"}
FUNCTION_VALUES = {"arrow_function", "function_expression", "generator_function", "function"}
CLASSES = {"class_declaration", "abstract_class_declaration", "class"}
SCOPES = FUNCTIONS | FUNCTION_VALUES | {"method_definition"}
PATTERNS = {"formal_parameters", "object_pattern", "array_pattern", "rest_pattern"}
# shortcut: a hand-kept list of the language's and the platform's names, called without being ours (a verdict, not
# an alert); to extend when `check` shows one under `unknown`.
GLOBALS = {"Array", "Boolean", "Date", "Error", "Map", "Number", "Object", "Promise", "RegExp", "Set", "String",
           "Symbol", "TypeError", "URL", "WeakMap", "parseFloat", "parseInt", "isNaN", "isFinite", "fetch", "require",
           "setTimeout", "setInterval", "clearTimeout", "clearInterval", "structuredClone", "queueMicrotask",
           "encodeURIComponent", "decodeURIComponent", "Intl", "Blob", "TextEncoder", "TextDecoder", "Uint8Array",
           "requestAnimationFrame", "alert", "confirm", "console", "Math", "JSON", "Reflect", "document", "window",
           "process", "localStorage", "navigator", "crypto", "performance", "Buffer", "Float32Array",
           "addEventListener", "scrollTo", "matchMedia",
           "$state", "$derived", "$effect", "$props", "$bindable", "$inspect", "$host"}  # Svelte's runes
# shortcut: a chain of re-exports longer than this is not followed (and a cycle stops there); to raise if a host
# re-exports deeper.
DEPTH = 8


class Def(NamedTuple):  # a top-level function or class of the module
    id: str


class Import(NamedTuple):  # `name` of `module`: "default", "*" (the namespace) or a name; module None: a package's
    module: str | None
    name: str


class Local(NamedTuple):  # an export of a name of the module
    name: str


class From(NamedTuple):  # a re-export: `name` of `module` ("*": `export * as`)
    module: str | None
    name: str


class Namespace(NamedTuple):  # what `import * as x` designates: a module of ours
    module: str


def _id(rel: str) -> str:
    return re.sub(r"\W", "_", rel).lower()


def _text(node) -> str:
    return node.text.decode("utf-8", "replace")


def _names(pattern) -> set[str]:
    """The names a parameter or a declaration binds (`a`, `{ b, c: d }`, `[e = 1]`, `...f`)."""
    if pattern.type in ("identifier", "shorthand_property_identifier_pattern"):
        return {_text(pattern)}
    if pattern.type in ("required_parameter", "optional_parameter"):  # TypeScript's, typed
        return _names(pattern.child_by_field_name("pattern"))
    if pattern.type in ("assignment_pattern", "object_assignment_pattern"):
        return _names(pattern.child_by_field_name("left"))
    if pattern.type == "pair_pattern":
        return _names(pattern.child_by_field_name("value"))
    if pattern.type in PATTERNS:
        return set().union(*map(_names, pattern.named_children))
    return set()


def _declared(scope) -> set[str]:
    """The parameters of a function and the names its body declares, outside its nested functions (whose names it
    declares). shortcut: a block's `let` counts for the whole function; to scope it if a host shadows in a block."""
    found = set()
    for field in ("parameters", "parameter"):
        if (p := scope.child_by_field_name(field)) is not None:
            found |= _names(p)
    stack = [c for c in scope.named_children if c.type not in ("formal_parameters", "identifier")]
    while stack:
        node = stack.pop()
        if node.type == "variable_declarator":
            found |= _names(node.child_by_field_name("name"))
        elif node.type in FUNCTIONS | CLASSES and (name := node.child_by_field_name("name")) is not None:
            found.add(_text(name))
        elif node.type == "catch_clause" and (p := node.child_by_field_name("parameter")) is not None:
            found |= _names(p)
        if node.type not in SCOPES:
            stack.extend(node.named_children)
    return found


def _source(path: Path) -> bytes:
    """A file's code: a `.svelte` component's `<script>` blocks, the rest blanked out byte for byte (lines kept)."""
    data = path.read_bytes()
    if path.suffix != ".svelte":
        return data
    kept = bytearray(re.sub(rb"[^\n]", b" ", data))
    for m in SCRIPT.finditer(data):
        kept[m.start(1):m.end(1)] = m.group(1)
    return bytes(kept)


def contribute(project) -> dict:
    """The JS reader's contribution (docs/contribution.md): a site per call."""
    reader = Reader(sorted(p for suffix in PARSERS for p in project.files(suffix)), project.root)
    return {"nodes": reader.nodes, "links": reader.links, "sites": reader.sites}


class Module:
    def __init__(self, rel: str, tree) -> None:
        self.rel, self.id, self.tree = rel, _id(rel), tree
        self.bindings: dict[str, Def | Import] = {}
        self.exports: dict[str, Local | From] = {}
        self.stars: list[str] = []  # export * from
        self.owners: dict[tuple, tuple[str, str | None]] = {}  # a body (start, end) -> (its node, its class)


class Reader:
    """shortcut: ES modules only, neither `require` nor `module.exports`, and relative specifiers only (neither a
    package's `exports` nor aliases); nested functions and the methods of an object literal are not nodes
    (BACKLOG.md). To extend when a host needs it."""

    def __init__(self, paths: list[Path], root: Path) -> None:
        self.nodes: list[dict] = []
        self.links: list[dict] = []
        self.sites: list[dict] = []
        self.modules: dict[str, Module] = {}
        for path in paths:
            rel = path.relative_to(root).as_posix()
            self.modules[rel] = Module(rel, PARSERS[path.suffix].parse(_source(path)))
        self.ids: set[str] = set()
        self.methods: dict[str, list[str]] = defaultdict(list)  # method name -> ids
        self.by_name: dict[str, list[str]] = defaultdict(list)  # top-level function or class name -> ids
        self.class_methods: dict[str, dict[str, str]] = {}  # class id -> method name -> id
        self.bases: dict[str, tuple[Module, str]] = {}  # class id -> (its module, the name it extends)
        for m in self.modules.values():
            self._node(m.id, posixpath.basename(m.rel), "file", m.rel, 1, m.rel)
            for top in m.tree.root_node.named_children:
                if top.type == "import_statement":
                    self._import(m, top)
                elif top.type == "export_statement":
                    self._export_statement(m, top)
                else:
                    self._declaration(m, top)
        for m in self.modules.values():
            self._calls(m)

    # ---------- the definitions, the imports and the exports

    def _import(self, m: Module, node) -> None:
        target = self._module(m, node.child_by_field_name("source"))
        for clause in (c for c in node.named_children if c.type == "import_clause"):
            for part in clause.named_children:
                if part.type == "identifier":
                    m.bindings[_text(part)] = Import(target, "default")
                elif part.type == "namespace_import":
                    m.bindings[_text(part.named_children[0])] = Import(target, "*")
                elif part.type == "named_imports":
                    for name, alias in map(self._specifier, part.named_children):
                        m.bindings[alias] = Import(target, name)
        if target:
            self._link(m.id, self.modules[target].id, "imports", m.rel, node)

    def _export_statement(self, m: Module, node) -> None:
        source = node.child_by_field_name("source")
        target = self._module(m, source) if source else None
        if target:
            self._link(m.id, self.modules[target].id, "imports", m.rel, node)
        declaration = node.child_by_field_name("declaration") or node.child_by_field_name("value")
        clause = next((c for c in node.named_children if c.type in ("export_clause", "namespace_export")), None)
        if clause is not None and clause.type == "namespace_export":  # export * as name from
            m.exports[_text(clause.named_children[-1])] = From(target, "*")
        elif clause is not None:
            for name, alias in map(self._specifier, clause.named_children):
                m.exports[alias] = From(target, name) if source else Local(name)
        elif source:
            if target:
                m.stars.append(target)  # export * from
        elif declaration is not None:
            names = self._declaration(m, declaration)
            if not any(c.type == "default" for c in node.children):
                for name in names:
                    m.exports[name] = Local(name)
                return
            if declaration.type == "identifier":
                names = [_text(declaration)]
            elif not names and declaration.type in FUNCTION_VALUES | CLASSES:  # anonymous
                names = [self._define(m, "default", declaration)]
            if names:
                m.exports["default"] = Local(names[0])

    @staticmethod
    def _specifier(s) -> tuple[str, str]:
        """(the name, the alias) of `name as alias` in an import or an export."""
        name, alias = s.child_by_field_name("name"), s.child_by_field_name("alias")
        return _text(name), _text(alias or name)

    def _declaration(self, m: Module, node) -> list[str]:
        """The names a top-level declaration defines: a function, a class, `const f = () =>`."""
        if node.type in FUNCTIONS | CLASSES:
            name = node.child_by_field_name("name")
            return [] if name is None else [self._define(m, _text(name), node)]
        names = []
        if node.type in ("lexical_declaration", "variable_declaration"):
            for d in node.named_children:
                name, value = d.child_by_field_name("name"), d.child_by_field_name("value")
                if d.type == "variable_declarator" and name is not None and name.type == "identifier" \
                        and value is not None and value.type in FUNCTION_VALUES | CLASSES:
                    names.append(self._define(m, _text(name), value, head=d))
        return names

    def _define(self, m: Module, name: str, node, head=None) -> str:
        """A function or a class at the top of `m` (its methods with it); its name."""
        head = head or node
        is_class = node.type in CLASSES
        nid = self._node(f"{m.id}_{name.lower()}", name if is_class else f"{name}()",
                         "class" if is_class else "function", m.rel, head.start_point[0] + 1, name)
        self._link(m.id, nid, "contains", m.rel, head)
        m.bindings[name] = Def(nid)
        self.by_name[name].append(nid)
        m.owners[(node.start_byte, node.end_byte)] = (nid, nid if is_class else None)
        if not is_class:
            return name
        methods = self.class_methods[nid] = {}
        heritage = next((c for c in node.named_children if c.type == "class_heritage"), None)
        base = heritage.named_children[0] if heritage is not None and heritage.named_children else None
        if base is not None and base.type == "extends_clause":  # TypeScript's
            base = base.child_by_field_name("value")
        if base is not None and base.type == "identifier":
            self.bases[nid] = (m, _text(base))
        for c in node.child_by_field_name("body").named_children:
            if c.type == "method_definition":
                method = _text(c.child_by_field_name("name"))
                mid = self._node(f"{nid}_{method.lower().lstrip('#')}", f"{name}.{method}()", "method", m.rel,
                                 c.start_point[0] + 1, f"{name}.{method}")
                self._link(nid, mid, "contains", m.rel, c)
                self.methods[method].append(mid)
                methods.setdefault(method, mid)  # a getter and its setter: the first
                m.owners[(c.start_byte, c.end_byte)] = (mid, nid)
        return name

    def _module(self, m: Module, source) -> str | None:
        """The file of ours that a relative specifier designates (`./zones.mjs`, `../lib`), else None."""
        spec = _text(source).strip("'\"`")
        if not spec.startswith("."):
            return None
        path = posixpath.normpath(posixpath.join(posixpath.dirname(m.rel), spec))
        for candidate in (path, *(path + s for s in SUFFIXES), *(f"{path}/index{s}" for s in SUFFIXES)):
            if candidate in self.modules:
                return candidate
        return None

    def _export(self, rel: str | None, name: str, depth: int = 0) -> str | Namespace | None:
        """What the module `rel` exports under `name`: a node, a namespace; re-exports followed."""
        m = self.modules.get(rel)
        if m is None or depth > DEPTH:
            return None
        e = m.exports.get(name)
        if isinstance(e, Local):
            return self._binding(m, e.name, depth)
        if isinstance(e, From):
            return Namespace(e.module) if e.name == "*" and e.module else self._export(e.module, e.name, depth + 1)
        for star in m.stars:
            if found := self._export(star, name, depth + 1):
                return found
        return None

    def _binding(self, m: Module, name: str, depth: int = 0) -> str | Namespace | None:
        """What a top-level name of `m` designates: a node of ours, a namespace of ours, else None."""
        b = m.bindings.get(name)
        if isinstance(b, Def):
            return b.id
        if isinstance(b, Import) and b.module:
            return Namespace(b.module) if b.name == "*" else self._export(b.module, b.name, depth + 1)
        return None

    def _method(self, cls: str, name: str, depth: int = 0) -> str | None:
        """The method `name` of the class `cls`, or of the class it extends."""
        if found := self.class_methods.get(cls, {}).get(name):
            return found
        if cls in self.bases and depth < DEPTH:
            base = self._binding(*self.bases[cls])
            if isinstance(base, str):
                return self._method(base, name, depth + 1)
        return None

    # ---------- the calls

    def _calls(self, m: Module) -> None:
        stack = [(m.tree.root_node, m.id, None, frozenset())]
        while stack:
            node, owner, cls, hidden = stack.pop()
            owner, cls = m.owners.get((node.start_byte, node.end_byte), (owner, cls))
            if node.type in SCOPES:
                hidden = hidden | _declared(node)
            if node.type in ("call_expression", "new_expression"):
                callee = node.child_by_field_name("function" if node.type == "call_expression" else "constructor")
                if callee is not None:
                    self._call(m, owner, cls, hidden, callee, node)
            stack.extend((c, owner, cls, hidden) for c in reversed(node.named_children))

    def _call(self, m: Module, owner: str, cls: str | None, hidden: frozenset, callee, node) -> None:
        """A call from `owner`: its link, and its site. `hidden`: the names its functions declare."""
        target, sure, verdict = None, True, "unknown"
        name = _text(callee)
        if callee.type == "identifier":
            b = m.bindings.get(name)
            if name in hidden:
                verdict = "local"
            elif b is not None:
                target = self._binding(m, name)
                target = target if isinstance(target, str) else None
                verdict = "ours" if target else "external" if isinstance(b, Import) and b.module is None else "absent"
            elif name in GLOBALS:
                verdict = "global"
            elif len(ours := self.by_name.get(name, [])) == 1:
                target, sure, verdict = ours[0], False, "ours?"
            elif ours:
                verdict = "ambiguous"
        elif callee.type == "member_expression":
            receiver, name = callee.child_by_field_name("object"), _text(callee.child_by_field_name("property"))
            known = receiver.type == "identifier" and _text(receiver) not in hidden
            b = m.bindings.get(_text(receiver)) if known else None
            if receiver.type == "this" and cls:
                target = self._method(cls, name)
            elif isinstance(b, Import) and b.module is None:
                verdict = "external"
            elif b is not None:
                holder = self._binding(m, _text(receiver))
                if isinstance(holder, Namespace):
                    target = self._export(holder.module, name)
                    target = target if isinstance(target, str) else None
                elif holder:  # a class: `Class.m()`; anything else is an object, its methods by the name
                    target = self._method(holder, name)
            elif known and _text(receiver) in GLOBALS:
                verdict = "global"
            if target:
                verdict = "ours"
            elif verdict == "unknown":
                ours = self.methods.get(name, [])
                if len(ours) == 1:
                    target, sure, verdict = ours[0], False, "ours?"
                else:
                    verdict = "ambiguous" if ours else "member"
        if target and target != owner:
            self._link(owner, target, "calls", m.rel, node, sure)
        self.sites.append({"verdict": verdict, "file": m.rel, "line": node.start_point[0] + 1, "name": name,
                           "text": _text(callee)[:60]})

    # ---------- the graph

    def _node(self, nid: str, label: str, kind: str, rel: str, line: int, name: str) -> str:
        """A node; its id, made unique (`get x` and `set x`, `Foo` and `foo`): an id taken would merge them."""
        base, n = nid, 2
        while nid in self.ids:
            nid, n = f"{base}_{n}", n + 1
        self.ids.add(nid)
        self.nodes.append({"id": nid, "label": label, "kind": kind, "source_file": rel,
                           "source_location": f"L{line}", "name": name})
        return nid

    def _link(self, source: str, target: str, relation: str, rel: str, node, sure: bool = True) -> None:
        self.links.append({"source": source, "target": target, "relation": relation,
                           "confidence": "EXTRACTED" if sure else "INFERRED", "source_file": rel,
                           "source_location": f"L{node.start_point[0] + 1}", "context": ""})
