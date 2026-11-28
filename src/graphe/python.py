"""The code graph, Python side: modules, classes, functions and calls.

Read by Python's ast. A call is linked to its target when its receiver has
a known type: an annotation (parameter, variable, attribute, dataclass
field, return), a construction (`x = Class(...)`, `self.x = Class(...)`),
an iteration over a typed container, an inferred return
(`return Class(...)`). Failing that, a name borne by a single one of our
functions is linked by the name alone (INFERRED); borne by several, it stays
unlinked and counts as `ambiguous`.

`graphe check` reads the classification of each call in the sites of its
contribution (`contribute`).

T-0026: each file's parse and definitions are kept in graphe/cache, keyed by
this file, the Python version, the path, the import name and the content; the
resolution across modules is redone at each build.

T-0096: a module is imported by its import name (`import_names`: `src/graphe/core.py`
is `graphe.core`); its node keeps its path's name. `import a.b.c` binds `a` and links
`a.b` and `a.b.c` (`as d`: not `a`); `a.b`, and `from a import b`, is the submodule
unless the package binds `b` otherwise, its own import of it winning over a fallback
beside it (`_submodule`). A name two modules bear resolves to neither, an import
through a leading folder without `__init__.py` to nothing (`shortcut:` each).
"""

from __future__ import annotations

import ast
import builtins
import hashlib
import os
import pickle
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from graphe import root
from graphe.root import ROOT

BUILTINS = set(dir(builtins))
# The methods of the containers we know how to type: what they return.
TO_ELEMENT = {"get", "pop", "setdefault", "__getitem__"}
TO_CONTAINER = {"values", "copy", "keys"}


def files() -> list[Path]:
    return root.files(".py")


def _id(text: str) -> str:
    return re.sub(r"\W", "_", text).lower()


@dataclass(eq=False)
class Function:
    id: str
    name: str
    qualname: str
    module: Module
    cls: Class | None
    parent: Function | None
    node: ast.FunctionDef | ast.AsyncFunctionDef
    locals: dict[str, list] = field(default_factory=lambda: defaultdict(list))

    @property
    def decorators(self) -> set[str]:
        return {d.id if isinstance(d, ast.Name) else d.attr for d in self.node.decorator_list
                if isinstance(d, (ast.Name, ast.Attribute))}


@dataclass(eq=False)
class Class:
    id: str
    name: str
    qualname: str
    module: Module
    node: ast.ClassDef
    methods: dict[str, Function] = field(default_factory=dict)
    # name -> [(expression, "annotation" | "value", the function where it is written)]
    attributes: dict[str, list] = field(default_factory=lambda: defaultdict(list))
    # The fields annotated in the class body (a dataclass): name -> line.
    fields: dict[str, int] = field(default_factory=dict)


@dataclass(eq=False)
class Module:
    id: str
    name: str  # the path's name (`src.graphe.core`), that of the node
    rel: str
    import_name: str  # T-0096: the name it is imported by (`graphe.core`), import_names
    tree: ast.Module
    functions: dict[str, Function] = field(default_factory=dict)
    classes: dict[str, Class] = field(default_factory=dict)
    imports: dict[str, tuple] = field(default_factory=dict)
    variables: dict[str, list] = field(default_factory=lambda: defaultdict(list))


def _store(entry: Path, value: tuple) -> None:
    """Writes alongside then replaces: a build that reads at the same time never sees half an entry."""
    temporary = entry.with_suffix(f".{os.getpid()}.tmp")
    try:
        data = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        if not entry.parent.is_dir():  # outside git even in a host without `graphe install` (pytest's way)
            entry.parent.mkdir(parents=True)
            (entry.parent / ".gitignore").write_text("*\n", encoding="utf-8")
        temporary.write_bytes(data)
        os.replace(temporary, entry)
    # shortcut: a tree too deep for pickle is read again at each build; raise the recursion limit if one is slow.
    except RecursionError:
        pass
    except OSError:  # the entry open by another build (Windows), a full disk: the cache is only a gain
        temporary.unlink(missing_ok=True)


def _load(entry: Path | None) -> tuple | None:
    """A module's definitions from the cache, or None. The cache is the host's (graphe/), like its extensions,
    which graphe runs too."""
    if entry is None:
        return None
    try:
        return pickle.loads(entry.read_bytes())
    except Exception:  # absent, unreadable, or written by another build at this instant
        return None


def _module_name(rel: str) -> str:
    name = rel.removesuffix(".py").replace("/", ".")
    return name.removesuffix(".__init__")


def import_names(rels: list[str]) -> dict[str, str]:
    """T-0096: each file's import name, the name it is imported by: its path without its leading folders that are no
    package (a package: a folder that holds an `__init__.py` among `rels`). `src/graphe/core.py` is `graphe.core`,
    `tools/outil.py` is `outil`, `pkg/sub/x.py` `pkg.sub.x` (`sub/` a namespace package inside `pkg`)."""
    # shortcut: a leading namespace package (PEP 420, `google/protobuf/` without `google/__init__.py`) is left out,
    # so an import through it (`google.protobuf.x`, Django's `tests.sphinx_tests...`) resolves to nothing; keep such
    # a folder when a sample host's `callers` suffer.
    packages = {rel.rpartition("/")[0] for rel in rels if rel.rpartition("/")[2] == "__init__.py"}
    names = {}
    for rel in rels:
        parts = rel.removesuffix(".py").split("/")
        start = 0
        while start < len(parts) - 1 and "/".join(parts[:start + 1]) not in packages:
            start += 1
        names[rel] = ".".join(parts[start:]).removesuffix(".__init__")
    return names


class Reader:
    """All our modules read, and each call classified."""

    def __init__(self, paths: list[Path] | None = None, root: Path = ROOT, cache: Path | None = None) -> None:
        self.root = root
        self.modules: dict[str, Module] = {}  # by path
        # T-0026: a module's definitions, read from its file alone: path -> (module, its classes and
        # functions in reading order, or None if to read, the cache file)
        read: dict[str, tuple] = {}
        tool = hashlib.sha256(Path(__file__).read_bytes() + sys.version.encode()).digest()
        paths = paths if paths is not None else files()
        names = import_names([path.relative_to(root).as_posix() for path in paths])
        for path in paths:
            rel = path.relative_to(root).as_posix()
            content = path.read_bytes()
            # the import name in the key: the relative imports are resolved by it, and an `__init__.py` changes it
            key = tool + rel.encode() + b"\0" + names[rel].encode() + b"\0" + content
            entry = cache / f"{hashlib.sha256(key).hexdigest()[:32]}.pickle" if cache else None
            if cached := _load(entry):
                m, classes, functions = cached
            else:
                try:
                    tree = ast.parse(content, filename=rel)
                except (SyntaxError, ValueError) as e:  # ValueError: a null byte
                    print(f"graphe: {rel} does not parse, skipped ({e})", file=sys.stderr)
                    continue
                m, classes, functions = Module(_id(rel.removesuffix(".py")), _module_name(rel), rel, names[rel],
                                               tree), None, None
            self.modules[rel] = m
            read[rel] = (m, classes, functions, entry)
        # shortcut: an import name borne by two modules resolves to neither (none in Django, Grid Zero or graphe);
        # resolve by the importer's nearest when a host imports such a name.
        self._by_import: dict[str, Module | None] = {}
        for rel, name in names.items():  # a file that does not parse bears its name too, as in the core
            self._by_import[name] = None if name in self._by_import else self.modules.get(rel)
        self.functions: list[Function] = []
        self.classes: list[Class] = []
        for m in self.modules.values():
            _, classes, functions, entry = read[m.rel]
            if classes is None:
                first_class, first_function = len(self.classes), len(self.functions)
                self._read_module(m)
                classes, functions = self.classes[first_class:], self.functions[first_function:]
                if entry is not None:
                    _store(entry, (m, classes, functions))
            else:
                self.classes += classes
                self.functions += functions
        if cache is not None and cache.is_dir():  # the entries of files gone or changed
            used = {e.name for *_, e in read.values()}
            for p in cache.glob("*.pickle"):
                if p.name not in used:
                    try:
                        p.unlink(missing_ok=True)
                    except OSError:  # open by another build (Windows)
                        pass
        # the candidates of `x.f()` by name: T-0099, a nested function is no attribute of anything
        # shortcut: one assigned to an attribute (`self.save_m2m = save_m2m`, Django) is, and is lost by its name too;
        # follow such assignments if a host's `x.f()` misses them.
        self.by_name: dict[str, list[Function]] = defaultdict(list)
        for f in self.functions:
            if f.parent is None:
                self.by_name[f.name].append(f)
        self.class_names = {c.name for c in self.classes}
        # T-0026: what holds a nested class, a table rather than a scan of every class per class (Django: 1.7 s)
        self._holders: dict[tuple, str] = {}
        for holder in [*self.classes, *self.functions]:
            self._holders.setdefault((id(holder.module), holder.qualname), holder.id)
        self.nodes: list[dict] = []
        self.links: list[dict] = []
        self.sites: list[dict] = []
        self._memo: dict = {}
        self._in_progress: set = set()
        self._emit()

    # ---------- reading the definitions

    def _read_module(self, m: Module) -> None:
        for node in m.tree.body:
            self._read_import(m, node)
        for node in self._statements(m.tree.body):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                self._note_assignment(m.variables, node, None)
        self._read_body(m, m.tree.body, m.id, "", None, None)

    @staticmethod
    def _import_entries(m: Module, node: ast.stmt) -> dict[str, tuple]:
        if isinstance(node, ast.Import):
            entries = {a.asname or a.name.split(".")[0]: ("module", a.name if a.asname else a.name.split(".")[0])
                       for a in node.names}
            # T-0096: `import a.b.c` (`as d` or not) imports `a.b` and `a.b.c` too: kept under their dotted names,
            # which no name reads, for their links.
            # shortcut: `import a.b as c` links `a.b`, not `a`: a key `a` would bind the name `a`, which `as` does not;
            # to give the links their own list if a host's `imports` suffer.
            for a in node.names:
                parts = a.name.split(".")
                entries.update({".".join(parts[:i]): ("module", ".".join(parts[:i])) for i in range(2, len(parts) + 1)})
            return entries
        if isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                package = m.import_name.split(".") if m.rel.endswith("__init__.py") else m.import_name.split(".")[:-1]
                package = package[:len(package) - node.level + 1]
                base = ".".join(package + ([base] if base else []))
            return {a.asname or a.name: ("symbol", base, a.name) for a in node.names}
        return {}

    def _read_import(self, m: Module, node: ast.stmt) -> None:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            m.imports.update(self._import_entries(m, node))
        elif isinstance(node, (ast.If, ast.Try)):
            for sub in [*node.body, *getattr(node, "orelse", []), *getattr(node, "finalbody", []),
                        *[s for h in getattr(node, "handlers", []) for s in h.body]]:
                self._read_import(m, sub)

    def _read_body(self, m: Module, body: list, parent_id: str, prefix: str, cls: Class | None,
                   function: Function | None) -> None:
        for node in self._definitions(body):
            if isinstance(node, ast.ClassDef):
                qual = prefix + node.name
                c = Class(f"{m.id}_{_id(qual)}", node.name, qual, m, node)
                self.classes.append(c)
                if function is None and cls is None:
                    m.classes[node.name] = c
                elif function is not None:
                    function.locals[node.name].append((c, "class", function, (node.lineno, None)))
                elif cls is not None:
                    cls.attributes[node.name].append((node, "class", None))
                for sub in node.body:
                    if isinstance(sub, (ast.Assign, ast.AnnAssign)):
                        self._note_assignment(c.attributes, sub, None)
                    if isinstance(sub, ast.AnnAssign) and isinstance(sub.target, ast.Name):
                        c.fields[sub.target.id] = sub.lineno
                self._read_body(m, node.body, c.id, qual + ".", c, None)
            else:
                qual = prefix + node.name
                f = Function(f"{m.id}_{_id(qual)}", node.name, qual, m, cls, function, node)
                self.functions.append(f)
                if function is not None:
                    function.locals[node.name].append((f, "def", function, (node.lineno, None)))
                if function is None:
                    if cls is not None:
                        cls.methods[node.name] = f
                    else:
                        m.functions[node.name] = f
                self._read_locals(f)
                self._read_body(m, node.body, f.id, qual + ".", None, f)

    @staticmethod
    def _statements(body: list):
        """The statements of a body, including under an if or a try, without
        entering the defs and classes."""
        stack = list(body)
        while stack:
            node = stack.pop(0)
            yield node
            if isinstance(node, (ast.If, ast.Try, ast.With, ast.For, ast.While)):
                stack[0:0] = [*node.body, *getattr(node, "orelse", []), *getattr(node, "finalbody", []),
                              *[s for h in getattr(node, "handlers", []) for s in h.body]]

    @staticmethod
    def _definitions(body: list):
        """The defs and classes of a body, including under an if or a try."""
        stack = list(body)
        while stack:
            node = stack.pop(0)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                yield node
            elif isinstance(node, (ast.If, ast.Try, ast.With, ast.For, ast.While)):
                stack[0:0] = [*node.body, *getattr(node, "orelse", []), *getattr(node, "finalbody", []),
                              *[s for h in getattr(node, "handlers", []) for s in h.body]]

    @staticmethod
    def _note_assignment(table: dict, node: ast.stmt, function: Function | None, location: tuple = ()) -> None:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            table[node.target.id].append((node.annotation, "annotation", function, *location))
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    table[target.id].append((node.value, "value", function, *location))

    def _read_locals(self, f: Function) -> None:
        # Each source of a local variable bears its location: (line, None)
        # for an assignment, (start, end) for a comprehension variable.
        a = f.node.args
        params = [*a.posonlyargs, *a.args, *a.kwonlyargs]
        start = (f.node.lineno, None)
        for i, p in enumerate(params):
            if p.annotation is not None:
                f.locals[p.arg].append((p.annotation, "annotation", f, start))
            elif i == 0 and f.cls is not None and f.parent is None and "staticmethod" not in f.decorators:
                f.locals[p.arg].append(
                    (f.cls, "class" if "classmethod" in f.decorators else "instance", f, start))
        own = list(self._own_nodes(f.node))  # T-0026: walked once, not twice (Django: 4.4 million nodes)
        globals_ = {name for n in own if isinstance(n, ast.Global) for name in n.names}
        for node in own:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for local, imp in self._import_entries(f.module, node).items():
                    f.locals[local].append((imp, "import", f, (node.lineno, None)))
                    if local in globals_:  # a module loaded later, by `global` in a function
                        f.module.imports[local] = imp
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                location = (node.lineno, None)
                self._note_assignment(f.locals, node, f, (location,))
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Tuple):
                        for i, el in enumerate(target.elts):
                            if isinstance(el, ast.Name):
                                f.locals[el.id].append(((node.value, i), "unpacked", f, location))
                    self._note_attribute(f, target, node)
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                self._note_iteration(f, node.target, node.iter, (node.lineno, None))
            elif isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
                for g in node.generators:
                    self._note_iteration(f, g.target, g.iter, (node.lineno, node.end_lineno))
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if isinstance(item.optional_vars, ast.Name):
                        f.locals[item.optional_vars.id].append(
                            (item.context_expr, "value", f, (node.lineno, None)))
            elif isinstance(node, ast.NamedExpr):
                f.locals[node.target.id].append((node.value, "value", f, (node.lineno, None)))

    def _note_attribute(self, f: Function, target: ast.expr, node: ast.stmt) -> None:
        """`self.x = ...` or `self.x: T = ...` in a method: an attribute of
        the class."""
        if not (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name)):
            return
        method = f
        while method.parent is not None:
            method = method.parent
        if method.cls is None:
            return
        first = (method.node.args.posonlyargs + method.node.args.args)[:1]
        if not first or first[0].arg != target.value.id:
            return
        if isinstance(node, ast.AnnAssign):
            method.cls.attributes[target.attr].append((node.annotation, "annotation", f))
        else:
            method.cls.attributes[target.attr].append((node.value, "value", f))

    @staticmethod
    def _note_iteration(f: Function, target: ast.expr, iterable: ast.expr, location: tuple) -> None:
        if isinstance(target, ast.Name):
            f.locals[target.id].append((iterable, "element", f, location))
        elif isinstance(target, ast.Tuple):
            for i, el in enumerate(target.elts):
                if isinstance(el, ast.Name):
                    f.locals[el.id].append(((iterable, i), "unpacked_element", f, location))

    @staticmethod
    def _own_nodes(node: ast.AST):
        """The nodes of a function, without those of its nested functions and
        classes (lambdas belong to it)."""
        stack = list(ast.iter_child_nodes(node))
        while stack:
            n = stack.pop()
            yield n
            if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                stack.extend(ast.iter_child_nodes(n))

    # ---------- the types

    def _module(self, name: str) -> Module | None:
        return self._by_import.get(name)

    def _submodule(self, package: Module, name: str) -> Module | None:
        """T-0096: `package.name` as the submodule (`pkg.a`, `from pkg import a`), unless the package binds `name`
        itself: a def, a class, a variable, an import of something else than that submodule (`from .x import g as
        name`). The package's own import of it (`from . import name`, `import pkg.name`) wins over its other bindings,
        a fallback beside it (`except ImportError: name = None`) for one."""
        sub = self._module(f"{package.import_name}.{name}")
        if sub is None:
            return None
        own = (("symbol", package.import_name, name), ("module", sub.import_name))
        # shortcut: the order is not read, so `from . import a` then `a = a.f` still takes `a` for the submodule; to
        # follow the package's statements in order if a host rebinds a submodule's name so.
        if package.imports.get(name) in own or package.imports.get(sub.import_name) in own:
            return sub
        bound = name in package.imports or name in package.functions or name in package.classes \
            or name in package.variables
        return None if bound else sub

    def _from_module(self, m: Module, name: str):
        if name in m.functions:
            return ("function", m.functions[name])
        if name in m.classes:
            return ("class", m.classes[name])
        if name in m.imports:
            return self._import(m, m.imports[name], name)
        if name in m.variables:  # guarded like a local: `l = l[1:]` at the top of a module
            return self._guard(("variable", m.id, name), lambda: self._from_sources(m.variables[name], None, m))
        if name in BUILTINS:
            return ("external", name)
        return None

    def _import(self, m: Module, imp: tuple, name: str):
        if imp[0] == "module":
            target = self._module(imp[1])
            return ("module", target) if target else ("external", imp[1])
        target = self._module(imp[1])
        if target is None:
            sub = self._module(f"{imp[1]}.{imp[2]}")
            return ("module", sub) if sub else ("external", f"{imp[1]}.{imp[2]}")
        if sub := self._submodule(target, imp[2]):
            return ("module", sub)
        return self._guard(("import", imp), lambda: self._from_module(target, imp[2]))

    def _guard(self, key, compute):
        if key in self._memo:
            return self._memo[key]
        if key in self._in_progress:
            return None
        self._in_progress.add(key)
        try:
            result = compute()
        finally:
            self._in_progress.discard(key)
        self._memo[key] = result
        return result

    @staticmethod
    def _at_line(sources: list, line: int | None) -> list:
        """The sources of a variable seen from the line where it serves: that
        of the comprehension that encloses it, then the assignments that
        precede, the closest first, then the following ones (a loop)."""
        if line is None:
            return [s for s in sources if len(s) <= 3 or s[3][1] is None]
        inside = [s for s in sources if len(s) > 3 and s[3][1] is not None and s[3][0] <= line <= s[3][1]]
        before = sorted((s for s in sources if len(s) > 3 and s[3][1] is None and s[3][0] <= line),
                        key=lambda s: -s[3][0])
        after = [s for s in sources if len(s) > 3 and s[3][1] is None and s[3][0] > line]
        return inside[::-1] + before + after + [s for s in sources if len(s) <= 3]

    def _from_sources(self, sources: list, f: Function | None, m: Module):
        for source, kind, where, *_ in sources:
            scope = where if where is not None else f
            t = self._source(source, kind, scope, m)
            if t is not None:
                return t
        return None

    def _source(self, source, kind: str, f: Function | None, m: Module):
        if kind == "annotation":
            return self._annotation(source, f, m)
        if kind in ("instance", "class"):
            return (kind, source)
        if kind == "def":
            return ("function", source)
        if kind == "import":
            return self._import(m, source, "")
        if kind == "value":
            return self.type_of(source, f, m)
        if kind == "element":
            return self._element(self.type_of(source, f, m))
        if kind == "unpacked_element":
            iterable, i = source
            t = self.type_of(iterable, f, m)
            if t and t[0] == "external":
                return t
            if t and t[0] == "pairs":
                return t[1][i] if i < len(t[1]) else None
            if t and t[0] == "container" and t[2]:
                return t[2][i] if i < len(t[2]) else None
            return None
        if kind == "unpacked":
            value, i = source
            t = self.type_of(value, f, m)
            if t and t[0] == "external":
                return t
            if t and t[0] == "container" and t[2]:
                return t[2][i] if i < len(t[2]) else None
            return None
        return None

    @staticmethod
    def _element(t):
        if t and t[0] == "container":
            return t[1]
        if t and t[0] == "pairs":
            return ("container", None, list(t[1]))
        if t and t[0] == "external":
            return ("external", "element")  # what comes out of an object outside the repository is not ours
        return None

    def _annotation(self, a, f: Function | None, m: Module):
        """The type an annotation designates, as an instance."""
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            try:
                a = ast.parse(a.value, mode="eval").body
            except SyntaxError:
                return None
        if isinstance(a, ast.BinOp) and isinstance(a.op, ast.BitOr):
            return self._annotation(a.left, f, m) or self._annotation(a.right, f, m)
        if isinstance(a, ast.Subscript):
            head = self._final_name(a.value)
            args = a.slice.elts if isinstance(a.slice, ast.Tuple) else [a.slice]
            if head in ("Optional", "ClassVar", "Final", "Annotated"):
                return self._annotation(args[0], f, m)
            if head == "Union":
                return next((t for t in (self._annotation(x, f, m) for x in args) if t), None)
            if head in ("list", "List", "set", "Set", "frozenset", "Sequence", "Iterable", "Iterator", "deque",
                        "Generator", "Collection", "MutableSequence"):
                return ("container", self._annotation(args[0], f, m), None)
            if head in ("dict", "Dict", "Mapping", "MutableMapping", "defaultdict", "OrderedDict") and len(args) == 2:
                return ("dict", self._annotation(args[0], f, m), self._annotation(args[1], f, m))
            if head in ("tuple", "Tuple"):
                return ("container", None, [self._annotation(x, f, m) for x in args])
            if head in ("type", "Type"):
                t = self._annotation(args[0], f, m)
                return ("class", t[1]) if t and t[0] == "instance" else None
            return self._annotation(a.value, f, m)
        if isinstance(a, (ast.Name, ast.Attribute)):
            t = self.type_of(a, f, m)
            if t and t[0] == "class":
                return ("instance", t[1])
            return ("external", self._final_name(a)) if t is None or t[0] == "external" else None
        return None

    @staticmethod
    def _final_name(e: ast.expr) -> str:
        if isinstance(e, ast.Name):
            return e.id
        if isinstance(e, ast.Attribute):
            return e.attr
        return ""

    def _local_name(self, name: str, f: Function | None, m: Module, line: int | None = None):
        scope = f
        while scope is not None:
            if name in scope.locals:
                here = line if scope is f else None
                sources = self._at_line(scope.locals[name], here)
                if sources:
                    return self._guard(("local", scope.id, name, here),
                                       lambda p=scope, s=sources: self._from_sources(s, p, m))
            scope = scope.parent
        return self._from_module(m, name)

    def type_of(self, e: ast.expr, f: Function | None, m: Module):
        """What an expression is: ("module" | "class" | "instance" |
        "function", object), a container, ("external", name), or None."""
        if isinstance(e, ast.Name):
            return self._local_name(e.id, f, m, e.lineno)
        if isinstance(e, ast.Attribute):
            if isinstance(e.value, ast.Call) and isinstance(e.value.func, ast.Name) and e.value.func.id == "super":
                cls = self._enclosing_class(f)
                return self._from_class(cls, e.attr, skip=True) if cls else None
            return self.attribute(self.type_of(e.value, f, m), e.attr)
        if isinstance(e, ast.Call):
            return self._result(e, f, m)
        if isinstance(e, ast.Subscript):
            t = self.type_of(e.value, f, m)
            if t and t[0] == "external":
                return ("external", "element")
            if t and t[0] == "dict":
                return t[2]
            if t and t[0] == "container":
                if t[2] and isinstance(e.slice, ast.Constant) and isinstance(e.slice.value, int):
                    return t[2][e.slice.value] if e.slice.value < len(t[2]) else None
                return t[1]
            return None
        if isinstance(e, (ast.List, ast.Set)):
            types = [self.type_of(x, f, m) for x in e.elts if not isinstance(x, ast.Starred)]
            return ("container", next((t for t in types if t), None), None)
        if isinstance(e, ast.Tuple):
            return ("container", None, [self.type_of(x, f, m) for x in e.elts])
        if isinstance(e, ast.Dict):
            values = [self.type_of(v, f, m) for v in e.values if v is not None]
            return ("dict", None, next((t for t in values if t), None))
        if isinstance(e, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            return ("container", self.type_of(e.elt, f, m), None)
        if isinstance(e, ast.DictComp):
            return ("dict", None, self.type_of(e.value, f, m))
        if isinstance(e, ast.IfExp):
            return self.type_of(e.body, f, m) or self.type_of(e.orelse, f, m)
        if isinstance(e, ast.BoolOp):
            return next((t for t in (self.type_of(v, f, m) for v in e.values) if t and t[0] != "external"), None)
        if isinstance(e, ast.NamedExpr):
            return self.type_of(e.value, f, m)
        if isinstance(e, ast.Await):
            return self.type_of(e.value, f, m)
        if isinstance(e, (ast.Constant, ast.JoinedStr, ast.BinOp, ast.Compare, ast.UnaryOp)):
            return ("external", type(e).__name__)
        return None

    @staticmethod
    def _enclosing_class(f: Function | None) -> Class | None:
        while f is not None and f.parent is not None:
            f = f.parent
        return f.cls if f else None

    def _mro(self, c: Class, seen: set | None = None) -> list:
        """The class and its bases (ours); a base outside the repository is
        given as ("external", name)."""
        seen = seen if seen is not None else set()
        if c.id in seen:
            return []
        seen.add(c.id)
        order = [c]
        for base in c.node.bases:
            t = self.type_of(base, None, c.module)
            if t and t[0] == "class":
                order += self._mro(t[1], seen)
            else:
                order.append(("external", self._final_name(base)))
        return order

    def _from_class(self, c: Class, name: str, instance: bool = True, skip: bool = False):
        external = False
        for bearer in self._mro(c)[1 if skip else 0:]:
            if isinstance(bearer, tuple):
                external = True
                continue
            if name in bearer.methods:
                method = bearer.methods[name]
                if "property" in method.decorators or "cached_property" in method.decorators:
                    return self._return(method) if instance else ("function", method)
                return ("function", method)
            if name in bearer.attributes:
                sources = bearer.attributes[name]
                if sources and sources[0][1] == "class":
                    nested = next((k for k in self.classes if k.node is sources[0][0]), None)
                    return ("class", nested) if nested else None
                t = self._guard(("attribute", bearer.id, name),
                                lambda p=bearer: self._from_sources(p.attributes[name], None, p.module))
                return t if t is not None else ("attribute", bearer, name)
        if external or name.startswith("__"):
            return ("external", name)
        return ("absent", c, name)

    def attribute(self, t, name: str):
        if t is None:
            return None
        kind = t[0]
        if kind == "module":
            if sub := self._submodule(t[1], name):  # T-0096: `pkg.a.f()` after `import pkg.a`
                return ("module", sub)
            return self._from_module(t[1], name) or ("absent", t[1], name)
        if kind in ("instance", "class"):
            return self._from_class(t[1], name, instance=kind == "instance")
        if kind == "dict":
            if name in TO_ELEMENT:
                return ("returns", t[2])
            if name == "values":
                return ("returns", ("container", t[2], None))
            if name == "items":
                return ("returns", ("pairs", (t[1], t[2])))
            return ("external", name)
        if kind == "container":
            if name in TO_ELEMENT:
                return ("returns", t[1])
            if name in TO_CONTAINER:
                return ("returns", t)
            return ("external", name)
        if kind in ("external", "pairs"):
            return ("external", name)
        return None

    def _return(self, f: Function):
        def compute():
            if f.node.returns is not None:
                return self._annotation(f.node.returns, f, f.module)
            for n in self._own_nodes(f.node):
                if isinstance(n, ast.Return) and n.value is not None:
                    t = self.type_of(n.value, f, f.module)
                    if t is not None:
                        return t
            return None
        return self._guard(("return", f.id), compute)

    def _result(self, call: ast.Call, f: Function | None, m: Module):
        if isinstance(call.func, ast.Name) and call.func.id == "super":
            return None
        target = self.type_of(call.func, f, m)
        if target is None:
            return None
        if target[0] == "class":
            return ("instance", target[1])
        if target[0] == "function":
            if target[1].name == "__new__" or target[1].name == "__init__":
                return None
            return self._return(target[1])
        if target[0] == "returns":
            return target[1]
        if target[0] == "external":
            if target[1] in ("replace", "deepcopy", "copy") and call.args:
                return self.type_of(call.args[0], f, m)
            if target[1] in ("sorted", "list", "reversed", "tuple", "set", "frozenset") and call.args:
                t = self.type_of(call.args[0], f, m)
                return ("container", self._element(t), None) if t and t[0] in ("container", "dict") else t
            if target[1] in ("enumerate",) and call.args:
                return ("container", ("container", None, [("external", "int"), self._element(
                    self.type_of(call.args[0], f, m))]), None)
            if target[1] in ("zip",) and call.args:
                return ("container", ("container", None, [self._element(self.type_of(a, f, m))
                                                          for a in call.args]), None)
            if target[1] in ("min", "max", "next") and call.args:
                return self._element(self.type_of(call.args[0], f, m))
            if target[1] in ("cast",) and call.args:
                return self._annotation(call.args[0], f, m)
            return ("external", target[1])
        return None

    # ---------- the graph

    def _node(self, id_: str, label: str, kind: str, rel: str, line: int, name: str) -> None:
        self.nodes.append({"id": id_, "label": label, "kind": kind, "source_file": rel,
                           "source_location": f"L{line}", "name": name})

    def _link(self, source: str, target: str, relation: str, rel: str, line: int, sure: bool = True,
              context: str = "") -> None:
        self.links.append({"source": source, "target": target, "relation": relation,
                           "confidence": "EXTRACTED" if sure else "INFERRED", "context": context,
                           "source_file": rel, "source_location": f"L{line}"})

    def _emit(self) -> None:
        for m in self.modules.values():
            self._node(m.id, Path(m.rel).name, "file", m.rel, 1, m.name)
            for local, imp in m.imports.items():
                target = self._module(imp[1])
                if imp[0] == "symbol":  # `from pkg import a`: the submodule `pkg.a`, or the package
                    sub = self._submodule(target, imp[2]) if target else self._module(f"{imp[1]}.{imp[2]}")
                    target = sub or target
                if target is not None and target is not m:
                    self._link(m.id, target.id, "imports", m.rel, 1, context=local)
                if imp[0] == "symbol" and target is not None:
                    t = self._import(m, imp, local)
                    if t and t[0] in ("function", "class"):
                        self._link(m.id, t[1].id, "imports", m.rel, 1, context=local)
        for c in self.classes:
            self._node(c.id, c.name, "class", c.module.rel, c.node.lineno, c.qualname)
            self._link(c.module.id if "." not in c.qualname else self._parent_id(c), c.id, "contains",
                       c.module.rel, c.node.lineno)
            for base in c.node.bases:
                t = self.type_of(base, None, c.module)
                if t and t[0] == "class":
                    self._link(c.id, t[1].id, "inherits", c.module.rel, c.node.lineno)
            for name, line in c.fields.items():
                self._node(self.field_id(c, name), f"{c.name}.{name}", "field", c.module.rel, line,
                           f"{c.qualname}.{name}")
                self._link(c.id, self.field_id(c, name), "contains", c.module.rel, line)
        for f in self.functions:
            label = f"{'.' if f.cls else ''}{f.name}()"
            self._node(f.id, label, "method" if f.cls else "function", f.module.rel, f.node.lineno, f.qualname)
            if f.cls is not None:
                self._link(f.cls.id, f.id, "method", f.module.rel, f.node.lineno)
            else:
                self._link(f.parent.id if f.parent else f.module.id, f.id, "contains", f.module.rel, f.node.lineno)
        for m in self.modules.values():
            body = [n for n in m.tree.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                                                 ast.ClassDef))]
            self._walk(body, m.id, None, m)
        for c in self.classes:
            body = [n for n in c.node.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                                                 ast.ClassDef))]
            self._walk(body + c.node.bases + c.node.decorator_list, c.id, None, c.module)
        for f in self.functions:
            a = f.node.args
            headers = [*f.node.decorator_list, *a.defaults, *[d for d in a.kw_defaults if d is not None]]
            self._walk(headers, f.parent.id if f.parent else (f.cls.id if f.cls else f.module.id),
                       f.parent, f.module)
            self._walk(f.node.body, f.id, f, f.module)
            for p in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg]:
                if p is not None:
                    self._types(p.annotation, f.id, f, f.module)
            self._types(f.node.returns, f.id, f, f.module)

    def _parent_id(self, c: Class) -> str:
        """The class, else the function, that holds a nested class (the first of the same qualname)."""
        return self._holders.get((id(c.module), c.qualname.rsplit(".", 1)[0]), c.module.id)

    def _walk(self, nodes: list, owner: str, f: Function | None, m: Module) -> None:
        stack = [(n, owner) for n in reversed(nodes)]
        called = set()
        while stack:
            n, who = stack.pop()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(n, ast.AnnAssign):
                self._types(n.annotation, who, f, m)
                stack.extend((x, who) for x in (n.value, n.target) if x is not None)
                continue
            if isinstance(n, ast.Call):
                called.add(id(n.func))
                self._call(n, who, f, m)
            elif isinstance(n, (ast.Name, ast.Attribute)) and isinstance(n.ctx, ast.Load) \
                    and id(n) not in called:
                if isinstance(n, ast.Attribute):
                    self._property(n, who, f, m)
                    self._field(n, who, f, m, "reads")
                self._reference(n, who, f, m)
            elif isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Store):
                self._field(n, who, f, m, "writes")
            elif isinstance(n, (ast.Import, ast.ImportFrom)) and f is not None:
                for local, imp in self._import_entries(m, n).items():
                    target = self._import(m, imp, local)
                    if target and target[0] in ("function", "class", "module") and target[1] is not m:
                        self._link(who, target[1].id, "imports", m.rel, n.lineno, context=local)
            stack.extend((x, who) for x in reversed(list(ast.iter_child_nodes(n))))

    def _reference(self, n: ast.expr, who: str, f: Function | None, m: Module, context: str = "") -> None:
        """One of our functions passed as a value (a callback, a sort key, a
        pool task), or one of our classes named without being called
        (isinstance, an annotation: context « type »)."""
        t = self.type_of(n, f, m)
        if t and t[0] == "function" and t[1].id != who and "property" not in t[1].decorators:
            self._link(who, t[1].id, "references", m.rel, n.lineno, context=context)
        elif t and t[0] == "class" and t[1].id != who:
            self._link(who, t[1].id, "references", m.rel, n.lineno, context=context)

    def _property(self, n: ast.Attribute, who: str, f: Function | None, m: Module) -> None:
        """Reading a property is calling its function."""
        receiver = self.type_of(n.value, f, m)
        if not receiver or receiver[0] != "instance":
            return
        for bearer in self._mro(receiver[1]):
            if isinstance(bearer, tuple):
                continue
            method = bearer.methods.get(n.attr)
            if method is not None:
                if {"property", "cached_property"} & method.decorators and method.id != who:
                    self._link(who, method.id, "calls", m.rel, n.lineno, context="property")
                return

    def field_id(self, c: Class, name: str) -> str:
        id_ = f"{c.id}_{_id(name)}"
        return id_ + "_field" if name in c.methods or name in self.class_names else id_

    def _field(self, n: ast.Attribute, who: str, f: Function | None, m: Module, relation: str) -> None:
        """`etat.demande`: reading or writing a field of one of our classes,
        when the receiver's type is known - the first bearer in the order of
        the bases."""
        receiver = self.type_of(n.value, f, m)
        if not receiver or receiver[0] != "instance":
            return
        for bearer in self._mro(receiver[1]):
            if isinstance(bearer, tuple):
                return
            if n.attr in bearer.fields:
                self._link(who, self.field_id(bearer, n.attr), relation, m.rel, n.lineno)
                return
            if n.attr in bearer.methods:
                return

    def _types(self, annotation: ast.expr | None, who: str, f: Function | None, m: Module) -> None:
        """The classes an annotation names, strings included."""
        if annotation is None:
            return
        for n in ast.walk(annotation):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                try:
                    self._types(ast.parse(n.value, mode="eval").body, who, f, m)
                except SyntaxError:
                    pass
            elif isinstance(n, ast.Name) or (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)):
                if isinstance(n, ast.Name) and any(isinstance(a, ast.Attribute) and a.value is n
                                                   for a in ast.walk(annotation)):
                    continue
                self._reference(n, who, f, m, context="type")

    def _call(self, call: ast.Call, who: str, f: Function | None, m: Module) -> None:
        func = call.func
        name = self._final_name(func)
        site = {"rel": m.rel, "line": call.lineno, "name": name, "expr": ast.unparse(func)[:80]}
        t = self.type_of(func, f, m)
        if t and t[0] == "function":
            self._link(who, t[1].id, "calls", m.rel, call.lineno)
            verdict = "ours"
        elif t and t[0] == "class":
            self._link(who, t[1].id, "uses", m.rel, call.lineno, context="instantiates")
            verdict = "ours"
        elif t and t[0] in ("external", "returns"):
            verdict = "external"
        elif t and t[0] == "attribute":
            verdict = "attribute"  # an attribute called: a callback stored in the object
        elif t and t[0] == "absent":
            verdict = "absent"
        else:
            receiver = None
            if isinstance(func, ast.Attribute):
                receiver = self.type_of(func.value, f, m)
            if receiver and receiver[0] in ("external", "container", "dict", "pairs"):
                verdict = "external"
            elif not name:
                verdict = "dynamic"
            elif isinstance(func, ast.Name):
                verdict = "local" if self._is_local(name, f) else "unknown"
            else:
                ours = self.by_name.get(name, [])
                if len(ours) == 1:
                    self._link(who, ours[0].id, "calls", m.rel, call.lineno, sure=False)
                    verdict = "ours?"
                elif ours:
                    verdict = "ambiguous"
                    site["candidates"] = len(ours)
                else:
                    verdict = "external?"
        site["verdict"] = verdict
        self.sites.append(site)

    @staticmethod
    def _is_local(name: str, f: Function | None) -> bool:
        while f is not None:
            a = f.node.args
            if name in f.locals or name in {p.arg for p in [*a.posonlyargs, *a.args, *a.kwonlyargs]} \
                    or (a.vararg and a.vararg.arg == name) or (a.kwarg and a.kwarg.arg == name):
                return True
            f = f.parent
        return False


def contribute(project) -> dict:
    """The Python reader's contribution (docs/contribution.md): a site per call, and its alerts."""
    reader = Reader(project.files(".py"), project.root, project.root / root.OUTPUT.name / "cache")
    our_names = set(reader.by_name) | reader.class_names
    sites = []
    for s in reader.sites:
        site = {"verdict": s["verdict"], "file": s["rel"], "line": s["line"], "name": s["name"], "text": s["expr"]}
        if s["verdict"] in ("unknown", "external?", "absent") and s["name"] in our_names:
            site["alert"] = "not linked to the name of one of our functions"
        sites.append(site)
    if project.checking:
        total = sum(1 for m in reader.modules.values() for n in ast.walk(m.tree) if isinstance(n, ast.Call))
        if total != len(reader.sites):
            sites.append({"file": "", "line": 0, "name": "", "alert": "ast calls left unclassified",
                          "text": f"{total} calls in the ast, {len(reader.sites)} classified"})
    return {"nodes": reader.nodes, "links": reader.links, "sites": sites}
