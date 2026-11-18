"""The host's JavaScript in the code graph (T-0014): `.js` and `.mjs`, read by tree-sitter (ADR 0002).

- a node per file, per top-level function (`function f`, `const f = () =>`), per class and per method
  (`Class.method`); the calls in a nested function belong to the function that contains it;
- the imports of our files (relative specifiers, re-exports followed): `imports` between files, and a call to an
  imported name leads to its definition;
- a call is sure (EXTRACTED) by a local definition, an import, `this.m()` in a class or `Class.m()`; by the name
  alone (INFERRED) for `x.m()` when one of our methods only has that name, or for a name defined once in the host.
"""

from __future__ import annotations

import posixpath
import re
from collections import defaultdict
from pathlib import Path

import tree_sitter
import tree_sitter_javascript

from graphe_root import ROOT

PARSER = tree_sitter.Parser(tree_sitter.Language(tree_sitter_javascript.language()))
FUNCTIONS = {"function_declaration", "generator_function_declaration"}
FUNCTION_VALUES = {"arrow_function", "function_expression", "generator_function", "function"}
# Called without being ours: the language's and the platform's (a verdict, not an alert).
GLOBALS = {"Array", "Boolean", "Date", "Error", "Map", "Number", "Object", "Promise", "RegExp", "Set", "String",
           "Symbol", "TypeError", "URL", "WeakMap", "parseFloat", "parseInt", "isNaN", "isFinite", "fetch", "require",
           "setTimeout", "setInterval", "clearTimeout", "clearInterval", "structuredClone", "queueMicrotask",
           "encodeURIComponent", "decodeURIComponent", "Intl", "Blob", "TextEncoder", "TextDecoder", "Uint8Array",
           "requestAnimationFrame", "alert", "confirm", "console", "Math", "JSON", "Reflect", "document", "window",
           "process", "localStorage", "navigator", "crypto", "performance", "Buffer"}


def _id(rel: str) -> str:
    return re.sub(r"\W", "_", posixpath.splitext(rel)[0]).lower()


def _text(node) -> str:
    return node.text.decode("utf-8", "replace")


def contribute(project) -> dict:
    """The JS reader's contribution (docs/contribution.md): a site per call."""
    reader = Reader(sorted(project.files(".js") + project.files(".mjs")), project.root)
    return {"nodes": reader.nodes, "links": reader.links, "sites": reader.sites}


class Module:
    def __init__(self, rel: str, tree) -> None:
        self.rel, self.id, self.tree = rel, _id(rel), tree
        self.bindings: dict[str, tuple] = {}  # local name -> ("def", id) | ("import", module rel or None, name)
        self.exports: dict[str, tuple] = {}  # exported name -> ("local", name) | ("from", module rel, name)
        self.stars: list[str] = []  # export * from
        self.owners: dict[tuple, tuple[str, str | None]] = {}  # a body (start, end) -> (its node, its class)


class Reader:
    def __init__(self, paths: list[Path] | None = None, root: Path = ROOT) -> None:
        self.root = root
        self.nodes: list[dict] = []
        self.links: list[dict] = []
        self.sites: list[dict] = []
        self.modules: dict[str, Module] = {}
        for path in paths or []:
            rel = path.relative_to(root).as_posix()
            self.modules[rel] = Module(rel, PARSER.parse(path.read_bytes()))
        self.methods: dict[str, list[str]] = defaultdict(list)  # method name -> ids
        self.by_name: dict[str, list[str]] = defaultdict(list)  # top-level function or class name -> ids
        self.ids: set[str] = set()
        for m in self.modules.values():
            self._node(m.id, posixpath.basename(m.rel), "file", m.rel, 1, m.rel)
            for top in m.tree.root_node.named_children:
                self._top(m, top)
        for m in self.modules.values():
            self._calls(m)

    # ---------- the definitions, the imports and the exports

    def _top(self, m: Module, node) -> None:
        if node.type == "import_statement":
            target = self._module(m, node.child_by_field_name("source"))
            for c in node.named_children:
                if c.type != "import_clause":
                    continue
                for part in c.named_children:
                    if part.type == "identifier":
                        m.bindings[_text(part)] = ("import", target, "default")
                    elif part.type == "namespace_import":
                        m.bindings[_text(part.named_children[0])] = ("import", target, "*")
                    elif part.type == "named_imports":
                        for s in part.named_children:
                            name, alias = s.child_by_field_name("name"), s.child_by_field_name("alias")
                            m.bindings[_text(alias or name)] = ("import", target, _text(name))
            if target:
                self._link(m.id, self.modules[target].id, "imports", m.rel, node)
            return
        if node.type == "export_statement":
            source = node.child_by_field_name("source")
            target = self._module(m, source) if source else None
            if source and target:
                self._link(m.id, self.modules[target].id, "imports", m.rel, node)
            if source and node.child_by_field_name("declaration") is None and not any(
                    c.type == "export_clause" or c.type == "namespace_export" for c in node.named_children):
                if target:
                    m.stars.append(target)  # export * from
                return
            for c in node.named_children:
                if c.type == "export_clause":
                    for s in c.named_children:
                        name, alias = s.child_by_field_name("name"), s.child_by_field_name("alias")
                        m.exports[_text(alias or name)] = ("from", target, _text(name)) if source \
                            else ("local", _text(name))
            default = any(c.type == "default" for c in node.children)
            declaration = node.child_by_field_name("declaration") or node.child_by_field_name("value")
            if declaration is None:
                return
            names = self._top(m, declaration) or []
            if default:
                if declaration.type == "identifier":
                    names = [_text(declaration)]
                elif not names and declaration.type in FUNCTION_VALUES | {"class"}:  # anonymous
                    names = [self._define(m, "default", declaration)]
                if names:
                    m.exports["default"] = ("local", names[0])
            else:
                for name in names:
                    m.exports[name] = ("local", name)
            return
        names = []
        if node.type in FUNCTIONS | {"class_declaration", "class"}:
            if (name := node.child_by_field_name("name")) is not None:
                names.append(self._define(m, _text(name), node))
        elif node.type in ("lexical_declaration", "variable_declaration"):
            for d in node.named_children:
                name, value = d.child_by_field_name("name"), d.child_by_field_name("value")
                if d.type == "variable_declarator" and name is not None and name.type == "identifier" \
                        and value is not None and value.type in FUNCTION_VALUES | {"class"}:
                    names.append(self._define(m, _text(name), value, head=d))
        return names

    def _define(self, m: Module, name: str, node, head=None) -> str:
        """A function or a class at the top of `m` (its methods with it); its name."""
        head = head or node
        is_class = node.type in ("class_declaration", "class")
        nid = f"{m.id}_{name.lower()}"
        self._node(nid, name if is_class else f"{name}()", "class" if is_class else "function", m.rel,
                   head.start_point[0] + 1, name)
        self._link(m.id, nid, "contains", m.rel, head)
        m.bindings[name] = ("def", nid)
        self.by_name[name].append(nid)
        m.owners[(node.start_byte, node.end_byte)] = (nid, nid if is_class else None)
        if is_class:
            for c in node.child_by_field_name("body").named_children:
                if c.type == "method_definition":
                    method = _text(c.child_by_field_name("name"))
                    mid = f"{nid}_{method.lower().lstrip('#')}"
                    self._node(mid, f"{name}.{method}()", "method", m.rel, c.start_point[0] + 1, f"{name}.{method}")
                    self._link(nid, mid, "contains", m.rel, c)
                    self.methods[method].append(mid)
                    m.owners[(c.start_byte, c.end_byte)] = (mid, nid)
        return name

    def _module(self, m: Module, source) -> str | None:
        """The file of ours that a relative specifier designates (`./zones.mjs`, `../lib`), else None."""
        spec = _text(source).strip("'\"`")
        if not spec.startswith("."):
            return None
        path = posixpath.normpath(posixpath.join(posixpath.dirname(m.rel), spec))
        for candidate in (path, path + ".js", path + ".mjs", path + "/index.js", path + "/index.mjs"):
            if candidate in self.modules:
                return candidate
        return None

    def _export(self, rel: str | None, name: str, depth: int = 0) -> str | None:
        """The node that the module `rel` exports under `name`, re-exports followed."""
        m = self.modules.get(rel)
        if m is None or depth > 8:
            return None
        e = m.exports.get(name)
        if e and e[0] == "local":
            return self._binding(m, e[1], depth)
        if e:
            return self._export(e[1], e[2], depth + 1)
        for star in m.stars:
            if found := self._export(star, name, depth + 1):
                return found
        return None

    def _binding(self, m: Module, name: str, depth: int = 0) -> str | None:
        b = m.bindings.get(name)
        if b and b[0] == "def":
            return b[1]
        if b and b[2] != "*":
            return self._export(b[1], b[2], depth + 1)
        return None

    # ---------- the calls

    def _calls(self, m: Module) -> None:
        stack = [(m.tree.root_node, m.id, None)]
        while stack:
            node, owner, cls = stack.pop()
            owner, cls = m.owners.get((node.start_byte, node.end_byte), (owner, cls))
            if node.type in ("call_expression", "new_expression"):
                callee = node.child_by_field_name("function" if node.type == "call_expression" else "constructor")
                if callee is not None:
                    self._call(m, owner, cls, callee, node)
            stack.extend((c, owner, cls) for c in reversed(node.named_children))

    def _call(self, m: Module, owner: str, cls: str | None, callee, node) -> None:
        target, sure, verdict = None, True, "unknown"
        name = _text(callee)
        if callee.type == "identifier":
            b = m.bindings.get(name)
            if b is not None:
                target = self._binding(m, name)
                verdict = "ours" if target else ("external" if b[0] == "import" and b[1] is None else "absent")
            elif name in GLOBALS:
                verdict = "global"
            elif len(ours := self.by_name.get(name, [])) == 1:
                target, sure, verdict = ours[0], False, "ours?"
            elif ours:
                verdict = "ambiguous"
        elif callee.type == "member_expression":
            obj, prop = callee.child_by_field_name("object"), callee.child_by_field_name("property")
            name = _text(prop)
            head = _text(obj)
            b = m.bindings.get(head) if obj.type == "identifier" else None
            if obj.type == "this" and cls:
                target = self._method(cls, name)
            elif b is not None and b[0] == "import" and b[1] is None:
                verdict = "external"
            elif b is not None:
                holder = self._binding(m, head) if b[0] == "def" or b[2] != "*" else None
                target = self._method(holder, name) if holder else self._export(b[1], name)
            elif head.split(".")[0] in GLOBALS:
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

    def _method(self, cls: str, name: str) -> str | None:
        mid = f"{cls}_{name.lower().lstrip('#')}"
        return mid if mid in self.ids else None

    # ---------- the graph

    def _node(self, nid: str, label: str, kind: str, rel: str, line: int, name: str) -> None:
        self.ids.add(nid)
        self.nodes.append({"id": nid, "label": label, "kind": kind, "source_file": rel,
                           "source_location": f"L{line}", "name": name})

    def _link(self, source: str, target: str, relation: str, rel: str, node, sure: bool = True) -> None:
        self.links.append({"source": source, "target": target, "relation": relation,
                           "confidence": "EXTRACTED" if sure else "INFERRED", "source_file": rel,
                           "source_location": f"L{node.start_point[0] + 1}", "context": ""})
