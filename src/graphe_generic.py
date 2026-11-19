"""The generic reader (T-0030, ADR 0003): the languages without a dedicated reader, read the same way by tree-sitter.
A language is data only (`Language`): its grammars by suffix, a query of ours per grammar, and the method names
never linked by name. The reading, the owner of a call, the `Class.method` naming and the linking are written once.

The queries follow one capture convention (docs/readers.md): `@function`, `@method`, `@class`, each with its
`@name`; `@call` for `f()`, `@send` for `x.m()`; `@reference` for `new C()`, `extends C`; `@receiver` for a method's
type when it is declared outside it (Go). A use belongs to the innermost definition that contains it; a function in
a `@class` is its method; a method's class is its `@receiver`, or else the innermost `@class` that contains it.

- a node per file, function, method (`Class.method`) and class; the definitions of one kind and name in a file are one
  (Rust's `struct T` and its `impl T`, Java's overloads); the ids carry the extension (`a_t_go`);
- every link a use makes is by the name alone (INFERRED), and only when the name has a single definition in the
  language: a call or a send to a function or a method, a reference to a class. A send never links a common name.
  Each call or send is a site: `ours?`, `ambiguous`, `common` or `external` (no definition of that name);
- a file that does not parse is skipped and named on stderr, unless the language is `tolerant` (C's macros).
"""

from __future__ import annotations

import functools
import re
import sys
from collections import defaultdict
from typing import NamedTuple

import tree_sitter
import tree_sitter_c
import tree_sitter_cpp
import tree_sitter_go
import tree_sitter_java
import tree_sitter_rust


class Language(NamedTuple):
    name: str
    grammars: dict[str, tuple[tree_sitter.Language, str]]  # suffix -> (grammar, query)
    common: frozenset[str]  # method names never linked from a send
    tolerant: bool = False  # a file that does not parse is read all the same (C's macros), not skipped
    erased: re.Pattern[bytes] | None = None  # what it matches is blanked before parsing (one line, columns kept)


class Definition(NamedTuple):
    kind: str  # function, method, class
    name: str  # `f`, `T.m`, `T`
    line: int


class Use(NamedTuple):
    kind: str  # call, send, reference
    name: str  # the bare name used
    line: int
    owner: Definition | None  # None: the file
    text: str  # what is used, up to its name (`x.y.m`)


DEFINITIONS = ("function", "method", "class")
USES = ("call", "send", "reference")

GO_QUERY = """
(function_declaration name: (identifier) @name) @function
(method_declaration
  receiver: (parameter_list (parameter_declaration type: [
    (type_identifier) @receiver
    (generic_type type: (type_identifier) @receiver)
    (pointer_type (type_identifier) @receiver)
    (pointer_type (generic_type type: (type_identifier) @receiver))]))
  name: (field_identifier) @name) @method
(type_spec name: (type_identifier) @name) @class
(call_expression function: (identifier) @name) @call
(call_expression function: (selector_expression field: (field_identifier) @name)) @send
(type_conversion_expression type: (generic_type type: (type_identifier) @name)) @call
(composite_literal type: [
  (type_identifier) @name
  (generic_type type: (type_identifier) @name)
  (qualified_type name: (type_identifier) @name)]) @reference
(field_declaration !name type: [
  (type_identifier) @name
  (qualified_type name: (type_identifier) @name)
  (pointer_type (type_identifier) @name)
  (pointer_type (qualified_type name: (type_identifier) @name))]) @reference
"""

# The common names: the standard library's (and xorm's `And`, `Exec`) that one function of gitea would collect from
# every `filepath.Join`, `strings.NewReader`, `cond.And` (T-0031, `check`'s most frequent sends linked by name), and
# the methods of Go's common interfaces. shortcut: a hand-kept list; to extend when `check` shows a standard name
# among the most frequent sends linked by name (`ours?`) on a host.
GO = Language("go", {".go": (tree_sitter.Language(tree_sitter_go.language()), GO_QUERY)}, frozenset({
    "String", "Error", "Close", "Len", "Less", "Swap", "Read", "Write", "Get", "Set", "Add", "Delete", "Load",
    "Store", "Lock", "Unlock", "Wait", "Done", "Run", "Do", "Next", "Reset", "Flush", "Sort", "Join", "Split",
    "NewReader", "HasPrefix", "HasSuffix", "TrimPrefix", "TrimSuffix", "Cut", "Contains", "Replace", "ToUpper",
    "ToLower", "Count", "Bytes", "Strings", "Fatal", "Printf", "Errorf", "MustCompile", "Compile", "QuoteMeta",
    "Getenv", "ReadFile", "WriteFile", "MkdirAll", "Open", "OpenFile", "Create", "Remove", "Stat", "Symlink", "Base",
    "Clean", "Parse", "ParseBool", "Format", "Marshal", "Unmarshal", "MarshalIndent", "WithTimeout", "WithCancel",
    "WithContext", "Must", "Equal", "Skip", "Stack", "Exec", "And", "Or", "Where", "Find", "Insert", "Update"}))

# The functions of a trait without a body (`fn sides(&self);`) are not captured: they would make each name ambiguous.
RUST_QUERY = """
(function_item name: (identifier) @name) @function
[(struct_item name: (type_identifier) @name)
 (enum_item name: (type_identifier) @name)
 (union_item name: (type_identifier) @name)
 (trait_item name: (type_identifier) @name)] @class
(impl_item type: [
  (type_identifier) @name
  (generic_type type: (type_identifier) @name)
  (scoped_type_identifier name: (type_identifier) @name)
  (reference_type type: [
    (type_identifier) @name
    (generic_type type: (type_identifier) @name)
    (scoped_type_identifier name: (type_identifier) @name)])]) @class
(call_expression function: (identifier) @name) @call
(call_expression function: (field_expression field: (field_identifier) @name)) @send
(call_expression function: (scoped_identifier name: (identifier) @name)) @send
(struct_expression name: [
  (type_identifier) @name
  (scoped_type_identifier name: (type_identifier) @name)]) @reference
"""

# The common names: the standard library's and the usual crates' (tokio, futures, http) that one function of
# libsignal would collect from every `Vec::with_capacity`, `std::future::ready`, `f.debug_struct(..).field` (T-0032,
# `check`'s most frequent sends linked by name, from `field` to `builder` below); the others, from `take` on, are
# guessed: the std traits' and iterators' methods. shortcut: a hand-kept list; to extend when `check` shows a
# standard name among the most frequent sends linked by name (`ours?`) on a host.
RUST = Language("rust", {".rs": (tree_sitter.Language(tree_sitter_rust.language()), RUST_QUERY)}, frozenset({
    "new", "default", "clone", "len", "is_empty", "push", "pop", "get", "get_mut", "insert", "remove", "contains",
    "iter", "iter_mut", "into_iter", "map", "and_then", "ok_or", "unwrap", "expect", "to_string", "to_owned", "from",
    "into", "as_ref", "as_str", "fmt", "eq", "cmp", "hash", "next", "collect", "write", "read", "extend", "clear",
    "field", "as_slice", "ok", "err", "decode", "transpose", "with_capacity", "ready", "recv", "channel", "is_none",
    "then", "concat", "null", "timeout", "current", "as_secs", "as_millis", "status", "any", "sort", "as_mut",
    "as_pin_mut", "builder", "take", "encode", "send", "is_some", "spawn", "block_on", "lock", "join", "to_vec",
    "try_from", "try_into", "parse", "split", "chain", "filter", "fold", "find", "zip", "copied", "cloned", "flatten",
    "unwrap_or", "unwrap_or_default", "unwrap_or_else", "map_err", "context", "with_context", "run", "call", "poll"}))

# An abstract method (no body) is not captured, as Rust's trait signatures; a constructor is the method `C.C`.
JAVA_QUERY = """
[(class_declaration name: (identifier) @name)
 (interface_declaration name: (identifier) @name)
 (enum_declaration name: (identifier) @name)
 (record_declaration name: (identifier) @name)] @class
(method_declaration name: (identifier) @name body: (block)) @method
(constructor_declaration name: (identifier) @name) @method
(method_invocation !object name: (identifier) @name) @call
(method_invocation object: (_) name: (identifier) @name) @send
(object_creation_expression type: [
  (type_identifier) @name
  (scoped_type_identifier (type_identifier) @name .)
  (generic_type [(type_identifier) @name (scoped_type_identifier (type_identifier) @name .)])]) @reference
(superclass [
  (type_identifier) @name
  (scoped_type_identifier (type_identifier) @name .)
  (generic_type [(type_identifier) @name (scoped_type_identifier (type_identifier) @name .)])]) @reference
(super_interfaces (type_list [
  (type_identifier) @name
  (scoped_type_identifier (type_identifier) @name .)
  (generic_type [(type_identifier) @name (scoped_type_identifier (type_identifier) @name .)])])) @reference
(extends_interfaces (type_list [
  (type_identifier) @name
  (scoped_type_identifier (type_identifier) @name .)
  (generic_type [(type_identifier) @name (scoped_type_identifier (type_identifier) @name .)])])) @reference
"""

# The common names: the JDK's (and JRuby's `newString`) that one method of protobuf would collect from every
# `s.getBytes`, `clazz.getMethod`, `buffer.flip`, `map.keySet` (T-0033, `check`'s most frequent sends linked by name,
# from `getBytes` to `getPackage` below); the others are guessed: the methods of the collections, `Object`,
# `String`, `Optional`, the streams, the threads, the boxed numbers and `Arrays`. shortcut: a hand-kept list; to
# extend when `check` shows a standard name among the most frequent sends linked by name (`ours?`) on a host.
JAVA = Language("java", {".java": (tree_sitter.Language(tree_sitter_java.language()), JAVA_QUERY)}, frozenset({
    "get", "set", "add", "put", "remove", "size", "isEmpty", "contains", "equals", "hashCode", "toString", "length",
    "append", "close", "build", "of", "valueOf", "apply", "accept", "run", "call", "next", "hasNext", "stream",
    "map", "filter", "collect", "forEach", "getName", "getValue", "getKey", "clear", "addAll", "format",
    "getBytes", "getMethod", "keySet", "flip", "remaining", "startsWith", "endsWith", "newString", "array",
    "hasArray", "arrayOffset", "slice", "replace", "push", "emptySet", "empty", "loadClass", "getPackage",
    "entrySet", "values", "iterator", "charAt", "substring", "indexOf", "trim", "split", "compareTo", "getClass",
    "isPresent", "orElse", "ifPresent", "println", "print", "write", "read", "flush", "start", "join", "getMessage",
    "intValue", "longValue", "parseInt", "asList", "sort", "copyOf", "max", "min"}))


# C and C++ (T-0034): the upstream `tags.scm` capture no call. A query pattern sees direct children only, so the
# forms a name takes are spelled out: wrapped in pointers or a reference (`char** f()`, `T& C::m()`), qualified up
# to three scopes (`ns::C::m`), the class the innermost scope (`C<T>::m` too). A prototype (`int f(int);`, a method
# declared in its class) and a declaration without a body (`class C;`, `= default`) are not captured: each would make
# a name ambiguous between the `.h` and the file that defines it. shortcut: a scope is taken for a class, so
# `void internal::Helper() {}` is the method `internal.Helper`; to tell a namespace from a class if a host needs it.
_C_DECLARATOR = ("[{f} (pointer_declarator declarator: {f}) (pointer_declarator declarator: (pointer_declarator "
                 "declarator: {f})){ref}]")
_C_DEFINITIONS = """
(function_definition declarator: {declarator} body: (_)) @function
[(struct_specifier name: {type} body: (_))
 (union_specifier name: {type} body: (_))
 (enum_specifier name: {type} body: (_))
 (type_definition type: [(struct_specifier !name body: (_)) (union_specifier !name body: (_))]
  declarator: (type_identifier) @name)] @class
(call_expression function: {call}) @call
(call_expression function: (field_expression field: {field})) @send
"""
_C_FUNCTION = "(function_declarator declarator: (identifier) @name)"
C_QUERY = _C_DEFINITIONS.format(declarator=_C_DECLARATOR.format(f=_C_FUNCTION, ref=""), type="(type_identifier) @name",
                                call="(identifier) @name", field="(field_identifier) @name")
# The forms are listed flat: py-tree-sitter 0.26.1 drops a match whose alternation holds a captured alternation
# (`[[(identifier) (field_identifier)] @name (qualified_identifier)]` misses `int a() {}` in a class).
_CPP_QUALIFIED = ("{n} (qualified_identifier name: [{n}]) "
                  "(qualified_identifier name: (qualified_identifier name: [{n}]))")
_CPP_SCOPED = ("(qualified_identifier scope: [(namespace_identifier) @receiver (template_type name: (type_identifier) "
               "@receiver)] name: [(identifier) @name (destructor_name) @name (operator_name) @name])")
_CPP_FUNCTION = ("(function_declarator declarator: [(identifier) @name (field_identifier) @name "
                 f"(destructor_name) @name (operator_name) @name {_CPP_QUALIFIED.format(n=_CPP_SCOPED)}])")
_CPP_TYPE = "(type_identifier) @name (template_type name: (type_identifier) @name)"
_CPP_CALL = "(identifier) @name (template_function name: (identifier) @name)"
CPP_QUERY = _C_DEFINITIONS.format(
    declarator=_C_DECLARATOR.format(f=_CPP_FUNCTION, ref=f" (reference_declarator {_CPP_FUNCTION})"),
    type=f"[{_CPP_TYPE}]", call=f"[{_CPP_CALL}]",
    field="[(field_identifier) @name (template_method name: (field_identifier) @name)]") + f"""
(class_specifier name: [{_CPP_TYPE}] body: (_)) @class
(call_expression function: (qualified_identifier name: [{_CPP_QUALIFIED.format(n=_CPP_CALL)}])) @send
(new_expression type: [{_CPP_QUALIFIED.format(n=_CPP_TYPE)}]) @reference
(base_class_clause [{_CPP_QUALIFIED.format(n=_CPP_TYPE)}]) @reference
"""

_C = tree_sitter.Language(tree_sitter_c.language())
_CPP = tree_sitter.Language(tree_sitter_cpp.language())
# C and C++ are one family (T-0034): a C++ call to a C function is linked. A `.h` is read as C++, which reads C.
C = Language("c", {".c": (_C, C_QUERY), ".h": (_CPP, CPP_QUERY), ".cpp": (_CPP, CPP_QUERY),
                   ".cc": (_CPP, CPP_QUERY), ".cxx": (_CPP, CPP_QUERY), ".hpp": (_CPP, CPP_QUERY)},
              # The common names: the standard library's (and absl's `Status::message`) that one function of
              # protobuf would collect from every `std::string(..)`, `v.emplace_back`, `s.append`, `v.reserve`
              # (T-0034, `check`'s most frequent sends linked by name, from `string` to `count` below); the others are
              # guessed: the methods of the containers, the strings, the smart pointers, `optional` and `std::`'s
              # functions. shortcut: a hand-kept list; to extend when `check` shows a standard name among the most
              # frequent sends linked by name (`ours?`) on a host.
              frozenset({
                  "string", "append", "emplace_back", "pop_back", "reserve", "message", "str", "release", "count",
                  "size", "empty", "begin", "end", "cbegin", "cend", "push_back", "data", "get", "reset", "find",
                  "insert", "erase", "clear", "at", "front", "back", "c_str", "substr", "length", "emplace", "resize",
                  "swap", "value", "has_value", "value_or", "ok", "status", "move", "forward", "make_unique",
                  "make_shared", "min", "max", "assign", "compare", "contains", "load", "store", "lock", "unlock",
                  "join", "push", "pop", "top", "rfind", "find_first_of", "starts_with", "ends_with", "what"}),
              # The macros the grammar cannot read, upper case with an underscore and no arguments:
              # `class PROTOBUF_EXPORT Foo` reads as a function `Foo`, `f() const ABSL_ATTRIBUTE_LIFETIME_BOUND {` (834
              # on protobuf) as no function, `UPB_INLINE void f()` and `T* PROTOBUF_NONNULL C::f()` as garbage. Erased
              # on protobuf: 2542 classes and 26202 functions and methods against 2208 and 23811, no name made of a
              # macro left. shortcut: a constant (`INT_MAX`) or a class (`struct MY_POINT {`) so named is erased too,
              # and a macro with arguments (`PROTOBUF_ALIGNAS(8)`) is not; to tell them apart if a host loses code.
              tolerant=True, erased=re.compile(rb"\b[A-Z][A-Z0-9]*_[A-Z0-9_]*[A-Z0-9]\b(?!\s*\()"))


@functools.cache
def _query(grammar: tree_sitter.Language, text: str) -> tree_sitter.Query:
    return tree_sitter.Query(grammar, text)


def _grammar(language: Language, file: str) -> tuple[tree_sitter.Language, str]:
    return next(g for suffix, g in language.grammars.items() if file.endswith(suffix))


def read(language: Language, file: str, source: bytes) -> tuple[list[Definition], list[Use]]:
    """A file's definitions and uses, each use with its owner. Raises SyntaxError if the file does not parse and the
    language is not `tolerant`."""
    grammar, text = _grammar(language, file)
    if language.erased:
        source = language.erased.sub(lambda m: b" " * len(m[0]), source)
    root = tree_sitter.Parser(grammar).parse(source).root_node
    # shortcut: one error node skips the whole file (gitea: Go 1.26's syntax, BACKLOG.md); to read the valid part
    # of the tree, or a newer grammar, when one is published.
    if root.has_error and not language.tolerant:
        raise SyntaxError(file)
    found = []  # (start, end, role, name node, receiver)
    for _, captures in tree_sitter.QueryCursor(_query(grammar, text)).matches(root):
        role = next(r for r in DEFINITIONS + USES if r in captures)
        node, name = captures[role][0], captures["name"][0]
        if name.is_missing:  # a name the grammar inserted to recover: C++'s `enum : int {..}` (T-0034)
            continue
        found.append((node.start_byte, node.end_byte, role, name, captures.get("receiver", [None])[0]))
    definitions, uses = [], []
    # A file's definitions of one kind and name are one: Rust's `struct T` and its `impl T`, Java's overloads.
    # shortcut: the line (and the extent) is the first one's; to give the node every line if `explain --source`
    # needs the others. shortcut: nested classes of one name (`X.Builder`, `Y.Builder`) and their methods are one
    # too; to name a nested class by its outer one if a host needs them apart.
    by_kind_name: dict[tuple[str, str], Definition] = {}
    stack: list[tuple[int, Definition]] = []  # the open definitions: (their end, them)
    # By position, an outer node before the inner one it starts with (`f(g())`), a definition before a use there.
    for start, end, role, name_node, receiver in sorted(found, key=lambda f: (f[0], -f[1], f[2] in USES)):
        while stack and stack[-1][0] <= start:
            stack.pop()
        name, line = name_node.text.decode("utf-8", "replace"), name_node.start_point[0] + 1
        if role in USES:
            used = source[start:name_node.end_byte].decode("utf-8", "replace")
            uses.append(Use(role, name, line, stack[-1][1] if stack else None, re.sub(r"\s+", "", used)[:60]))
            continue
        kind = role
        if role != "class":
            cls = receiver.text.decode("utf-8", "replace") if receiver is not None else \
                next((d.name for _, d in reversed(stack) if d.kind == "class"), None)
            kind, name = ("method", f"{cls}.{name}") if cls else ("function", name)
        if (kind, name) not in by_kind_name:
            by_kind_name[kind, name] = Definition(kind, name, line)
            definitions.append(by_kind_name[kind, name])
        stack.append((end, by_kind_name[kind, name]))
    return definitions, uses


def _id(text: str) -> str:
    return re.sub(r"\W", "_", text).lower()


def contribute(language: Language, project) -> dict:
    """The contribution of one language (docs/contribution.md): only its own definitions are linked. A host without
    its files contributes nothing, not even an empty coverage."""
    paths = sorted({p for suffix in language.grammars for p in project.files(suffix)})
    if not paths:
        return {}
    nodes, links, sites, ids = [], [], [], set()

    def node(nid: str, label: str, kind: str, rel: str, line: int, name: str) -> str:
        base, n = nid, 2  # made unique (`Get` and `get`, two `init`): an id taken would merge them
        while nid in ids:
            nid, n = f"{base}_{n}", n + 1
        ids.add(nid)
        nodes.append({"id": nid, "label": label, "kind": kind, "source_file": rel, "source_location": f"L{line}",
                      "name": name})
        return nid

    def link(source: str, target: str, relation: str, rel: str, line: int, sure: bool = True) -> None:
        links.append({"source": source, "target": target, "relation": relation,
                      "confidence": "EXTRACTED" if sure else "INFERRED", "source_file": rel,
                      "source_location": f"L{line}", "context": ""})

    files = []  # (rel, the file's id, the id of each definition, the uses)
    callables: dict[str, list[str]] = defaultdict(list)  # bare name -> function and method ids
    classes: dict[str, list[str]] = defaultdict(list)
    for path in paths:
        rel = path.relative_to(project.root).as_posix()
        try:
            definitions, uses = read(language, rel, path.read_bytes())
        except SyntaxError:
            print(f"graphe: {rel} does not parse ({language.name}): skipped", file=sys.stderr)
            continue
        fid = node(_id(rel), rel.rsplit("/", 1)[-1], "file", rel, 1, rel)
        held = {d: node(f"{fid}_{_id(d.name)}", d.name if d.kind == "class" else f"{d.name}()", d.kind, rel, d.line,
                        d.name) for d in definitions}
        in_file = {d.name: held[d] for d in definitions if d.kind == "class"}
        for d in definitions:
            (classes[d.name] if d.kind == "class" else callables[d.name.rsplit(".", 1)[-1]]).append(held[d])
            # a method's class holds it when it is defined in the same file (Go's type is often in another one)
            cls = d.name.rsplit(".", 1)[0] if d.kind == "method" else None
            link(in_file.get(cls, fid), held[d], "contains", rel, d.line)
        files.append((rel, fid, held, uses))
    for rel, fid, held, uses in files:
        for u in uses:
            owner = held[u.owner] if u.owner else fid
            ours = (classes if u.kind == "reference" else callables).get(u.name, [])
            if u.kind != "reference":
                verdict = "external" if not ours else "common" if u.kind == "send" and u.name in language.common \
                    else "ours?" if len(ours) == 1 else "ambiguous"
                sites.append({"verdict": verdict, "file": rel, "line": u.line, "name": u.name, "text": u.text})
                if verdict != "ours?":
                    continue
            if len(ours) == 1 and ours[0] != owner:
                link(owner, ours[0], "calls" if u.kind != "reference" else "references", rel, u.line, sure=False)
    return {"nodes": nodes, "links": links, "sites": sites}
