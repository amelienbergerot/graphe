"""The host's JavaScript in the code graph (T-0014): `.js`, `.mjs` and `.jsx`, read by tree-sitter (ADR 0002); `.tsx`
by the TSX grammar (T-0076), a JSX `<Component/>` no call; `.ts` and a `.svelte` component (T-0015) by the TypeScript
grammar: its `<script>`, and the expressions of its markup as statements of the module, their calls the component's
(T-0022); a `.vue` component likewise, its script in the grammar its `lang` names (T-0082); the rest blanked out
to keep the lines.

- a node per file, per top-level function (`function f`, `const f = () =>`), per class and per method
  (`Class.method`), per method of an object literal a function returns or a module's `const` holds (T-0020), per
  test (`test('title', () => ...)`, T-0021); the calls in a nested function belong to the function that contains it;
- the imports of our files (relative specifiers, re-exports followed): `imports` between files, and a call to an
  imported name leads to its definition; a name of a package, re-exported or not, is `external` (T-0018);
- a call is sure (EXTRACTED) by a top-level definition, an import, a namespace (`import * as`, `export * as`),
  `this.m()` in a class or its parents, `Class.m()`, or `x.m()` when x was assigned `new C()` or `[await] f()`
  (T-0020); by the name alone (INFERRED) for `x.m()` when one of our class methods only has that name, or for a
  name defined once in the host. A parameter or a variable of the function or of the module hides an import of
  the same name: its calls are `local`. A bare name of ours as a statement (`onclick={fermer}`) or a JSX expression
  (`onClick={save}`) is a `references`.

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
# T-0076: the JavaScript grammar parses JSX; TypeScript's does not (`<T>x` is a cast there), its TSX sibling does.
TSX = tree_sitter.Parser(tree_sitter.Language(tree_sitter_typescript.language_tsx()))
PARSERS = {".js": JS, ".mjs": JS, ".jsx": JS, ".ts": TS, ".tsx": TSX, ".svelte": TS, ".vue": JS}  # `.vue`: by its `lang`
# T-0082: a Vue component's script in the grammar its `lang` names, JavaScript without one.
LANG = re.compile(rb"""<script\b[^>]*\slang=["']?(tsx?)\b""")
VUE_GRAMMARS = {b"ts": TS, b"tsx": TSX}
# The suffixes a relative specifier may leave out (`./lib/eau` is `./lib/eau.ts`); a component is imported with its
# `.svelte`. shortcut: not NodeNext's `./x.js` for `x.ts`; to add when a host has some.
SUFFIXES = (".js", ".mjs", ".jsx", ".ts", ".tsx")
# shortcut: by a pattern, so a `</script>` in a string of the script ends it; to parse the markup if a host trips on it.
SCRIPT = re.compile(rb"<script\b[^>]*>(.*?)</script>", re.S)
# T-0022: what the markup's expressions are not read in: the script, the style, the comments.
NOT_MARKUP = re.compile(rb"<(script|style)\b[^>]*>.*?</\1>|<!--.*?-->", re.S)
# The keyword of a block or a tag, cut before its expression is kept (`{#if x}`: `x`; `{@const c = f()}`:
# `const c = f()`); `{#each xs as x}` and `{#await p then v}` keep `xs` and `p`. Any other `{#`, `{:`, `{/`, `{@`
# (`{:else}`, `{/if}`, `{#snippet ...}`) keeps nothing.
KEYWORD = re.compile(rb"(#if|#each|#await|#key|:else\s+if|@html|@render|@attach|@debug)\b\s*|@(?=const\b)")
CUT = re.compile(rb"\s(?:as|then|catch)\s")
# T-0082: a Vue template's expressions: `{{ }}`, and the value of a directive (`@click`, `:prop`, `v-on`, `v-bind`,
# `v-if`...); `v-for` keeps what follows its `in` or `of`. Neither `v-slot` nor `#slot`: a pattern, no call.
MUSTACHE = re.compile(rb"\{\{(.*?)\}\}", re.S)
DIRECTIVE = re.compile(rb"""\s([@:]|v-(?:on|bind|if|else-if|show|model|html|text|memo|for)\b)[^\s=>]*\s*=\s*"""
                       rb"""(?:"([^"]*)"|'([^']*)')""")
FOR = re.compile(rb"\s(?:in|of)\s")
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
           "$state", "$derived", "$effect", "$props", "$bindable", "$inspect", "$host",  # Svelte's runes
           "defineProps", "defineEmits", "defineModel", "defineExpose", "defineOptions", "defineSlots", "withDefaults",
           "$emit"}  # Vue's compiler macros, and its template's `$emit`
# T-0021: the functions of node:test, vitest and jest whose callback is a test, named by its title. shortcut: neither
# `test.only` nor `describe.each`; to add when a host has some.
TESTS = {"test", "it", "describe"}
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


class Package(NamedTuple):  # T-0018: what a name imported from a package designates, re-exported or not
    name: str


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


def _returned_object(function):
    """T-0020: the object literal a function returns (`return {...}`, `() => ({...})`), outside its nested
    functions; else None."""
    body = function.child_by_field_name("body")
    stack = [body] if body is not None and body.type == "statement_block" else []
    while body is not None and body.type == "parenthesized_expression" and body.named_children:
        body = body.named_children[0]
    if body is not None and body.type == "object":
        return body
    objects, returned = {}, []  # `const p = {...}; ... return p` (dpe's ui_mode.test.mjs)
    while stack:
        node = stack.pop()
        if node.type == "return_statement" and node.named_children:
            value = node.named_children[0]
            while value.type == "parenthesized_expression" and value.named_children:
                value = value.named_children[0]
            returned.append(value)
        elif node.type == "variable_declarator" and (value := node.child_by_field_name("value")) is not None \
                and value.type == "object" and node.child_by_field_name("name").type == "identifier":
            objects[_text(node.child_by_field_name("name"))] = value
        if node.type not in SCOPES:
            stack.extend(node.named_children)
    for value in sorted(returned, key=lambda v: v.start_byte):  # the first return of the source
        if value.type == "object":
            return value
        if value.type == "identifier" and _text(value) in objects:
            return objects[_text(value)]
    return None


def _required(root) -> set[str]:
    """The names a module's top binds by `require(...)` (`const { aider } = require('./x.js')`): names of ours
    perhaps, by the name, that the module's own variables (T-0019) must not hide. shortcut: CommonJS is not followed
    (Reader); to read `require` if a host needs it."""
    return {name for d in root.named_children if d.type in ("lexical_declaration", "variable_declaration")
            for v in d.named_children if v.type == "variable_declarator"
            and (value := v.child_by_field_name("value")) is not None and value.type == "call_expression"
            and _text(_callee(value)) == "require" for name in _names(v.child_by_field_name("name"))}


def _callee(call):
    """What a call or a `new` calls."""
    return call.child_by_field_name("constructor" if call.type == "new_expression" else "function")


def _component(data: bytes) -> tuple[bytearray, list[tuple[int, int]]]:
    """A Svelte or Vue component blanked out byte for byte (lines kept) but its `<script>` blocks, and the spans its
    markup's expressions are not read in."""
    kept = bytearray(re.sub(rb"[^\n]", b" ", data))
    for m in SCRIPT.finditer(data):
        kept[m.start(1):m.end(1)] = m.group(1)
    return kept, [m.span() for m in NOT_MARKUP.finditer(data)]


def _alone(parser, expression: bytes) -> bool:
    """An expression of a Vue template the grammar parses, its `;` a token (not swallowed by a `// comment`)."""
    root = parser.parse(expression + b";").root_node
    return not root.has_error and root.descendant_for_byte_range(len(expression), len(expression) + 1).type == ";"


def _source(path: Path) -> bytes:
    """A file's code: a `.svelte` component's `<script>` blocks, and the expressions of its markup (T-0022) as
    statements of the module, `{f(x)}` read ` f(x);`; the rest blanked out byte for byte (lines kept)."""
    data = path.read_bytes()
    if path.suffix != ".svelte":
        return data
    kept, skipped = _component(data)
    i = 0
    while (i := data.find(b"{", i)) >= 0:
        if (inside := next((end for start, end in skipped if start <= i < end), None)) is not None:
            i = inside
            continue
        depth, j = 0, i  # shortcut: a brace in a string of the expression miscounts; to tokenize if a host has one
        while j < len(data) and not (data[j] == ord("}") and depth == 1):
            depth += {ord("{"): 1, ord("}"): -1}.get(data[j], 0)
            j += 1
        if j == len(data):
            break  # an expression never closed: nothing of it, nor of what follows
        start = i + 1
        if keyword := KEYWORD.match(data, start):
            start = keyword.end()
        elif data[start:start + 1] in (b"#", b":", b"/", b"@"):
            start = j
        end = cut.start() if keyword and (cut := CUT.search(data, start, j)) else j
        kept[start:end] = data[start:end]
        kept[j] = ord(";")
        i = j + 1
    return bytes(kept)


def _parse(path: Path):
    """A file's tree; a `.vue` component's (T-0082): its `<script>` blocks, and its template's expressions as
    statements of the module, each one alone, one the grammar cannot parse left out; the rest blanked out.
    shortcut: the Options API's `methods: {}` are no nodes, a call to one stays `unknown`; to read when a host has some."""
    if path.suffix != ".vue":
        return PARSERS[path.suffix].parse(_source(path))
    data = path.read_bytes()
    parser = VUE_GRAMMARS[lang.group(1)] if (lang := LANG.search(data)) else JS
    kept, skipped = _component(data)
    expressions = [m.span(1) for m in MUSTACHE.finditer(data)]
    for m in DIRECTIVE.finditer(data):
        start, end = m.span(2 if m.group(2) is not None else 3)
        if m.group(1) == b"v-for" and (cut := FOR.search(data, start, end)):
            start = cut.end()
        expressions.append((start, end))
    for start, end in expressions:
        if not any(s <= start < e for s, e in skipped) and _alone(parser, data[start:end]):
            kept[start:end] = data[start:end]
            kept[end] = ord(";")  # the `}` of `}}`, or the closing quote
    return parser.parse(bytes(kept))


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
            self.modules[rel] = Module(rel, _parse(path))
        self.ids: set[str] = set()
        self.methods: dict[str, list[str]] = defaultdict(list)  # method name -> ids
        self.by_name: dict[str, list[str]] = defaultdict(list)  # top-level function or class name -> ids
        self.class_methods: dict[str, dict[str, str]] = {}  # class id -> method name -> id
        self.bases: dict[str, tuple[Module, str]] = {}  # class id -> (its module, the name it extends)
        self.returning: set[str] = set()  # the functions whose methods are those of the object they return
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
                    for name, alias in map(self._specifier, (c for c in part.named_children if c.type != "comment")):
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
            for name, alias in map(self._specifier, (c for c in clause.named_children if c.type != "comment")):
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
                elif d.type == "variable_declarator" and name is not None and name.type == "identifier" \
                        and value is not None and value.type == "object":  # T-0020: `const outils = { m() {} }`
                    nid = self._node(f"{m.id}_{_text(name).lower()}", _text(name), "object", m.rel,
                                     d.start_point[0] + 1, _text(name))
                    self._link(m.id, nid, "contains", m.rel, d)
                    m.bindings[_text(name)] = Def(nid)
                    self._members(m, nid, _text(name), value)
                    names.append(_text(name))
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
            if (returned := _returned_object(node)) is not None:  # T-0020: dpe's page objects
                self._members(m, nid, name, returned)
                self.returning.add(nid)
            return name
        heritage = next((c for c in node.named_children if c.type == "class_heritage"), None)
        base = heritage.named_children[0] if heritage is not None and heritage.named_children else None
        if base is not None and base.type == "extends_clause":  # TypeScript's
            base = base.child_by_field_name("value")
        if base is not None and base.type == "identifier":
            self.bases[nid] = (m, _text(base))
        self._members(m, nid, name, node.child_by_field_name("body"))
        return name

    def _members(self, m: Module, nid: str, name: str, body) -> None:
        """The methods of a class body or of an object literal (T-0020: `m() {}`, `m: () => ...`), nodes held by
        `nid`: `this.m()` inside them is `nid`'s. An object's methods are reached by its type only, never by the name
        alone: dpe's fake objects have `click`, `getItem`, which the DOM's would take."""
        methods = self.class_methods.setdefault(nid, {})
        for c in body.named_children:
            if c.type == "method_definition":
                method = _text(c.child_by_field_name("name"))
            elif c.type == "pair" and (value := c.child_by_field_name("value")) is not None \
                    and value.type in FUNCTION_VALUES:
                method = _text(c.child_by_field_name("key")).strip("'\"")
            else:
                continue
            mid = self._node(f"{nid}_{method.lower().lstrip('#')}", f"{name}.{method}()", "method", m.rel,
                             c.start_point[0] + 1, f"{name}.{method}")
            self._link(nid, mid, "contains", m.rel, c)
            if body.type == "class_body":
                self.methods[method].append(mid)
            methods.setdefault(method, mid)  # a getter and its setter: the first
            arrow = c.type == "pair" and c.child_by_field_name("value").type == "arrow_function"
            m.owners[(c.start_byte, c.end_byte)] = (mid, None if arrow else nid)  # an arrow's `this` is not nid

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

    def _export(self, rel: str | None, name: str, depth: int = 0) -> str | Namespace | Package | None:
        """What the module `rel` exports under `name`: a node, a namespace, a package's name; re-exports followed."""
        m = self.modules.get(rel)
        if m is None or depth > DEPTH:
            return None
        e = m.exports.get(name)
        if isinstance(e, Local):
            return self._binding(m, e.name, depth)
        if isinstance(e, From) and e.module is None:
            return Package(e.name)
        if isinstance(e, From):
            return Namespace(e.module) if e.name == "*" else self._export(e.module, e.name, depth + 1)
        for star in m.stars:
            if found := self._export(star, name, depth + 1):
                return found
        return None

    def _binding(self, m: Module, name: str, depth: int = 0) -> str | Namespace | Package | None:
        """What a top-level name of `m` designates: a node of ours, a namespace of ours, a package's name, else
        None."""
        b = m.bindings.get(name)
        if isinstance(b, Def):
            return b.id
        if isinstance(b, Import) and b.module is None:
            return Package(b.name)
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
        # T-0019: the module's own variables (a Svelte prop, `let { onouvrir } = $props()`) hide like a function's;
        # its definitions and imports stay bindings.
        root = m.tree.root_node
        hidden = _declared(root) - m.bindings.keys() - _required(root)
        stack = [(root, m.id, None, frozenset(hidden), self._typed(m, root))]
        while stack:
            node, owner, cls, hidden, types = stack.pop()
            owner, cls = m.owners.get((node.start_byte, node.end_byte), (owner, cls))
            if node.type in SCOPES:
                declared = _declared(node)
                hidden = hidden | declared
                types = {k: v for k, v in types.items() if k not in declared} | self._typed(m, node)
            if node.type in ("call_expression", "new_expression"):
                callee = _callee(node)
                if callee is not None:
                    self._call(m, owner, cls, hidden, types, callee, node)
                if node.type == "call_expression" and callee is not None and callee.type == "identifier" \
                        and _text(callee) in TESTS and _text(callee) not in hidden:
                    self._test(m, owner, node)
            elif node.type in ("expression_statement", "jsx_expression") and len(node.named_children) == 1 \
                    and node.named_children[0].type == "identifier" and _text(node.named_children[0]) not in hidden:
                # T-0022: a bare name, a handler of the markup (`onclick={fermer}`, JSX's `onClick={save}`, T-0076):
                # a reference, not a call
                if isinstance(target := self._binding(m, _text(node.named_children[0])), str) and target != owner:
                    self._link(owner, target, "references", m.rel, node)
            stack.extend((c, owner, cls, hidden, types) for c in reversed(node.named_children))

    def _test(self, m: Module, owner: str, node) -> None:
        """T-0021: `test('title', () => {...})`: a node named by its title, held by `owner` (its file, its
        `describe`); the calls of the callback are its own."""
        if isinstance(self._binding(m, _text(node.child_by_field_name("function"))), str):
            return  # a `test` of ours
        arguments = node.child_by_field_name("arguments")
        title = next((a for a in arguments.named_children if a.type in ("string", "template_string")), None)
        callback = next((a for a in arguments.named_children if a.type in FUNCTION_VALUES), None)
        if title is None or callback is None:
            return
        line = node.start_point[0] + 1
        tid = self._node(f"{m.id}_test_{line}", _text(title)[1:-1], "test", m.rel, line, _text(title)[1:-1])
        self._link(owner, tid, "contains", m.rel, node)
        m.owners[(callback.start_byte, callback.end_byte)] = (tid, None)

    def _typed(self, m: Module, scope) -> dict[str, str]:
        """T-0020: the variables of a scope assigned `new C()` or `[await] f()`, C a class of ours or f a function
        of ours that returns an object literal: name -> what holds their methods."""
        found = {}
        stack = list(scope.named_children)
        while stack:
            node = stack.pop()
            if node.type == "variable_declarator" and (value := node.child_by_field_name("value")) is not None:
                if value.type == "await_expression" and value.named_children:
                    value = value.named_children[0]
                callee = _callee(value) if value.type in ("new_expression", "call_expression") else None
                name = node.child_by_field_name("name")
                if callee is not None and callee.type == "identifier" and name.type == "identifier":
                    holder = self._binding(m, _text(callee))
                    if isinstance(holder, str) and holder in self.class_methods:
                        found[_text(name)] = holder
            if node.type not in SCOPES:
                stack.extend(node.named_children)
        return found

    def _call(self, m: Module, owner: str, cls: str | None, hidden: frozenset, types: dict[str, str], callee,
              node) -> None:
        """A call from `owner`: its link, and its site. `hidden`: the names its functions declare; `types`: the
        variables whose methods are known (T-0020)."""
        target, sure, verdict = None, True, "unknown"
        name = _text(callee)
        if callee.type == "identifier":
            b = m.bindings.get(name)
            if name in hidden:
                verdict = "local"
            elif b is not None:
                target = self._binding(m, name)
                verdict = "ours" if isinstance(target, str) else "external" if isinstance(target, Package) else "absent"
                target = target if isinstance(target, str) else None
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
            if receiver.type == "identifier" and _text(receiver) in types:
                target = self._method(types[_text(receiver)], name)
            elif receiver.type == "this" and cls:
                target = self._method(cls, name)
            elif isinstance(b, Import) and b.module is None:
                verdict = "external"
            elif b is not None:
                holder = self._binding(m, _text(receiver))
                if isinstance(holder, Namespace):
                    target = self._export(holder.module, name)
                    target = target if isinstance(target, str) else None
                elif isinstance(holder, Package):
                    verdict = "external"
                elif holder and holder not in self.returning:  # `Class.m()`, `objet.m()`; not `f.m()` (T-0020)
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
