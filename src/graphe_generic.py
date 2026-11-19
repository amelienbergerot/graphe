"""The generic reader (T-0030, ADR 0003): the languages without a dedicated reader, read the same way by tree-sitter.
A language is data only (`Language`): its grammars by suffix, a query of ours per grammar, the method names
never linked by name, and, for C/C++'s macros and C#'s `#if`, whether a file with errors is read and what is
blanked first. The reading, the owner of a call, the `Class.method` naming and the linking are written once.

The queries follow one capture convention (docs/readers.md): `@function`, `@method`, `@class`, each with its
`@name`; `@call` for `f()`, `@send` for `x.m()`; `@reference` for `new C()`, `extends C`; `@receiver` for a method's
type when it is declared outside it (Go). A use belongs to the innermost definition that contains it; a function in
a `@class` is its method; a method's class is its `@receiver`, or else the innermost `@class` that contains it.

- a node per file, function, method (`Class.method`) and class; the definitions of one kind and name in a file are one
  (Rust's `struct T` and its `impl T`, Java's overloads); the ids carry the extension (`a_t_go`);
- every link a use makes is by the name alone (INFERRED), and only when the name has a single definition in the
  language: a call or a send to a function or a method, a reference to a class. A send never links a common name.
  Each call or send is a site: `ours?`, `ambiguous`, `common` or `external` (no definition of that name);
- a file that does not parse is skipped and named on stderr, unless the language is `tolerant` (C's macros, C#'s
  `#if`, Swift's and Go's newer syntax, Rust's `dyn 'a + Trait`).
"""

from __future__ import annotations

import functools
import re
import sys
from collections import defaultdict
from typing import NamedTuple

import tree_sitter
import tree_sitter_c
import tree_sitter_c_sharp
import tree_sitter_cpp
import tree_sitter_go
import tree_sitter_java
import tree_sitter_kotlin
import tree_sitter_ruby
import tree_sitter_rust
import tree_sitter_swift


class Language(NamedTuple):
    name: str
    grammars: dict[str, tuple[tree_sitter.Language, str]]  # suffix -> (grammar, query)
    common: frozenset[str]  # method names never linked from a send
    tolerant: bool = False  # a file that does not parse is read, not skipped (C's macros, C#, Swift, Go, Rust)
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
    "WithContext", "Must", "Equal", "Skip", "Stack", "Exec", "And", "Or", "Where", "Find", "Insert", "Update"}),
    # Grammar 0.25.0 knows neither Go 1.26's `new(expr)` nor generic methods: 47 of gitea's 3199 files, read all the
    # same (T-0039). shortcut: a generic method is lost in its error node, its calls its file's; to upgrade the
    # grammar when one knows them. shortcut: a Go file that does not parse is not named on stderr; to name it if a
    # host's garbage shows.
    tolerant=True)

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
    "unwrap_or", "unwrap_or_default", "unwrap_or_else", "map_err", "context", "with_context", "run", "call", "poll"}),
    # Grammar 0.24.2 rejects a lifetime first in a trait object (`dyn 's + FnOnce(..)`): 1 of libsignal's 612 files,
    # read all the same (T-0040). shortcut: a Rust file that does not parse is not named on stderr; to name it if a
    # host's garbage shows.
    tolerant=True)

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


# C# (T-0035): the upstream `tags.scm` captures only `x.M()`, the bare `F()` is ours. A type is named by its last name,
# bare, generic, qualified or behind the `pb::` alias of generated code. As Java's, a method without a body (abstract,
# an interface's) is not captured and a constructor is the method `C.C`. shortcut: a property's accessors, a local
# function, an operator and a destructor are no definitions, their calls belong to the class (or the method); to
# capture them if a host's `explain` needs them.
_CS_NAME = "[(identifier) @name (generic_name (identifier) @name)]"
_CS_TYPE = (f"[(identifier) @name (generic_name (identifier) @name) (qualified_name name: {_CS_NAME}) "
            f"(alias_qualified_name name: {_CS_NAME})]")
CSHARP_QUERY = f"""
[(class_declaration name: (identifier) @name)
 (interface_declaration name: (identifier) @name)
 (struct_declaration name: (identifier) @name)
 (enum_declaration name: (identifier) @name)
 (record_declaration name: (identifier) @name)] @class
(method_declaration name: (identifier) @name body: (_)) @method
(constructor_declaration name: (identifier) @name) @method
(invocation_expression function: {_CS_NAME}) @call
(invocation_expression function: (member_access_expression name: {_CS_NAME})) @send
(invocation_expression function: (conditional_access_expression (member_binding_expression name: {_CS_NAME}))) @send
(object_creation_expression type: {_CS_TYPE}) @reference
(base_list {_CS_TYPE}) @reference
(primary_constructor_base_type type: {_CS_TYPE}) @reference
"""

CSHARP = Language("csharp", {".cs": (tree_sitter.Language(tree_sitter_c_sharp.language()), CSHARP_QUERY)},
                  # The common names: the BCL's that one method of protobuf would collect from every
                  # `builder.Append` (a StringBuilder), `enumerator.MoveNext`, `typeof(T).GetProperty` (T-0035,
                  # `check`'s most frequent sends linked by name, the first three); the others are guessed: the
                  # methods of `object`, the strings, the collections, LINQ, the streams and reflection.
                  # shortcut: a hand-kept list; to extend when `check` shows a standard name among the most frequent
                  # sends linked by name (`ours?`) on a host.
                  frozenset({
                      "Append", "MoveNext", "GetProperty", "AppendLine", "AppendFormat", "ToString", "Equals",
                      "GetHashCode", "GetType", "CompareTo", "Add", "AddRange", "Remove", "RemoveAt", "Contains",
                      "ContainsKey", "TryGetValue", "Clear", "CopyTo", "ToArray", "ToList", "ToDictionary", "Select",
                      "Where", "Any", "All", "First", "FirstOrDefault", "Single", "Count", "Sum", "OrderBy",
                      "SequenceEqual", "GetEnumerator", "Dispose", "Split", "Join", "Substring", "IndexOf",
                      "StartsWith", "EndsWith", "Trim", "Replace", "ToUpper", "ToLower", "ToUpperInvariant",
                      "ToLowerInvariant", "Write", "WriteLine", "ReadLine", "ReadToEnd", "Flush", "Close", "Invoke",
                      "GetValue", "SetValue", "GetMethod", "GetField", "GetCustomAttributes", "IsAssignableFrom"}),
                  # protobuf's generated code cuts its base list with `#if` (`: pb::IMessage<T>` `#if ..` `, ..`
                  # `#endif`): the grammar does not parse it, 44 of 224 files skipped. The directives erased, 2 left
                  # (`f() = x;`, and an expression whose two branches then follow each other), read all the same: no
                  # method lost its class. shortcut: both branches are read (their calls counted twice, their
                  # definitions one); to keep one branch if a host's definitions differ between them. shortcut: a C#
                  # file that does not parse is no longer named on stderr; to name it if a host's garbage shows.
                  tolerant=True, erased=re.compile(rb"(?m)^[ \t]*#[ \t]*(?:if|elif|else|endif)\b.*$"))


# Ruby (T-0036): the upstream `tags.scm` takes a bare identifier for a call, which may be a local variable: ours
# captures the explicit calls only, `b()`, `c arg`, `x.c`. A module is a class, as it holds its `def self.m`; a
# `class << self` is none, its methods its class's. `C.new` is a reference to `C`. shortcut: a bare `b` is no call (it
# may be a variable); to tell a variable from a call (the grammar's `locals.scm`) if a host's `explain` misses them.
# shortcut: an `attr_reader`, an `alias` or a `define_method` is no definition, and a setter call `x.y = v` is a send
# `y`, not `y=`; to capture them if a host's hand-written accessors need callers.
_RB_CONSTANT = "[(constant) @name (scope_resolution name: (constant) @name)]"
RUBY_QUERY = f"""
[(class name: {_RB_CONSTANT}) (module name: {_RB_CONSTANT})] @class
(call receiver: {_RB_CONSTANT} method: (identifier) @_eval block: (_) (#eq? @_eval "class_eval")) @class
[(method name: (_) @name) (singleton_method name: (_) @name)] @method
(call !receiver method: [(identifier) (constant)] @name) @call
(call receiver: (_) method: [(identifier) (constant)] @name) @send
(superclass {_RB_CONSTANT}) @reference
(call receiver: {_RB_CONSTANT} method: (identifier) @_new (#eq? @_new "new")) @reference
"""

# The common names: `new` (892 sends `C.new`, 9 `def self.new` in protobuf), `each` (38) and `pack` (6 of its 9 sends
# `Array#pack`, linked to `Any.pack`), measured on protobuf (T-0036, `check`); the others are guessed: the methods of
# `Object`, the conversions, `Enumerable`, `Array`, `Hash`, `String` and `IO`. A name whose sends are mostly protobuf's
# is left out: `push`, `pop`, `first`, `delete`, `keys` (its `RepeatedField` and `Map` mirror `Array` and `Hash`),
# `eql?` (its messages'). shortcut: a
# hand-kept list; to extend when `check` shows a standard name among the most frequent sends linked by name (`ours?`)
# on a host.
RUBY = Language("ruby", {".rb": (tree_sitter.Language(tree_sitter_ruby.language()), RUBY_QUERY)}, frozenset({
    "new", "each", "pack", "to_s", "inspect", "hash", "dup", "clone", "freeze", "frozen?", "is_a?", "kind_of?",
    "respond_to?", "send", "public_send", "nil?", "class", "tap", "then", "to_i", "to_f", "to_sym", "to_str",
    "to_proc", "map", "select", "reject", "each_with_index", "each_with_object", "each_pair", "include?", "any?",
    "all?", "find", "count", "sum", "min", "max", "sort", "sort_by", "reduce", "inject", "flat_map", "flatten",
    "compact", "uniq", "zip", "join", "key?", "fetch", "merge", "dig", "empty?", "size", "split", "strip",
    "gsub", "sub", "start_with?", "end_with?", "upcase", "downcase", "read", "write", "puts", "print", "close",
    "call"}))


# Swift (T-0037): the upstream `tags.scm` captures no call. A class, a struct, an enum and an actor are one
# `class_declaration`, a class; a protocol is one too. An `extension C` is no class: its methods are `C`'s by
# `@receiver` (as Go's), so that a type extended in several files stays one class and its references are linked. A
# method is captured as a direct child of its body, the only way to tell a type's from an extension's; `init` is
# `C.init`, a computed property `var p: T { .. }` the method `C.p` (577 on libsignal, whose 670 calls would be their
# class's; reading `x.p` is no call, so it has no caller). A type is named by its last name, generic or not.
# shortcut: a nested function, an operator (`static func ==`) and a subscript are no definitions, and a stored
# property's initial value or observers (`didSet`) call from the class; to capture them if a host's `explain` needs
# them. shortcut: a call to a capitalised name (`C(..)`, `Foo.Bar(..)`) is a reference to that type, a lower-case one
# a call, Swift's naming convention; to tell them apart by their definitions if a host breaks it. shortcut: the grammar
# reads `defer { }` as a call `defer`, and the standard `withUnsafePointer(to:)` and `withUnsafeMutablePointer(to:)`
# are linked to a host's method of that name (libsignal's, 24 bare calls all the standard's): no calls, so a host's
# own bare function so named gets no caller; to drop them by their `to:` label if a host defines one.
_SW_LAST = ("[(user_type (type_identifier) @{c} .) "
            "(user_type (type_identifier) @{c} . (type_arguments) .)]")
_SW_EXTENDED = _SW_LAST.format(c="receiver")
_SW_TYPE = _SW_LAST.format(c="name")
_SW_FUNCTION = ("[(function_declaration name: (simple_identifier) @name body: (_)) "
                "(init_declaration \"init\" @name body: (_)) "
                "(property_declaration name: (pattern bound_identifier: (simple_identifier) @name) "
                "computed_value: (_))]")
SWIFT_QUERY = f"""
[(class_declaration name: (type_identifier) @name) (protocol_declaration name: (type_identifier) @name)] @class
(source_file (function_declaration name: (simple_identifier) @name body: (_)) @function)
(class_declaration name: (type_identifier) body: [(class_body {_SW_FUNCTION} @function)
                                                   (enum_class_body {_SW_FUNCTION} @function)])
(class_declaration name: {_SW_EXTENDED} body: (class_body {_SW_FUNCTION} @method))
(call_expression (simple_identifier) @name
 (#not-match? @name "^([A-Z]|(defer|withUnsafePointer|withUnsafeMutablePointer)$)")) @call
(call_expression (simple_identifier) @name (#match? @name "^[A-Z]")) @reference
(call_expression (navigation_expression suffix: (navigation_suffix suffix: (simple_identifier) @name))
 (#not-match? @name "^[A-Z]")) @send
(call_expression (navigation_expression suffix: (navigation_suffix suffix: (simple_identifier) @name))
 (#match? @name "^[A-Z]")) @reference
(call_expression (prefix_expression target: (simple_identifier) @name)) @send
(constructor_expression constructed_type: {_SW_TYPE}) @reference
(inheritance_specifier inherits_from: {_SW_TYPE}) @reference
"""

# The common names: `init` (611 sends `self.init`, `.init`, `super.init`), `append` (71, `Data`'s), `combine` (3 of
# its 4 sends `Hasher.combine`, linked to `GroupSendEndorsement.combine`) and `withCString` (`String`'s, which libsignal
# wraps on `Optional`), measured on libsignal (T-0037, `check`); the others are guessed: the standard library's
# collections, sequences, `Codable`, `Hashable` and unsafe pointers. `remove` is left out: its one send is
# libsignal's `svrB.remove()`. shortcut: a hand-kept list; to extend when `check` shows a standard name among the most
# frequent sends linked by name (`ours?`) on a host.
SWIFT = Language("swift", {".swift": (tree_sitter.Language(tree_sitter_swift.language()), SWIFT_QUERY)}, frozenset({
    "init", "append", "combine", "withCString", "map", "filter", "reduce", "forEach", "compactMap", "flatMap",
    "contains", "first", "last", "insert", "removeAll", "sorted", "sort", "joined", "split", "description", "hash",
    "encode", "decode", "withUnsafeBytes", "withUnsafeBufferPointer", "withUnsafeMutableBufferPointer",
    "withUnsafeMutableBytes", "index", "firstIndex", "count", "isEmpty", "prefix", "suffix", "dropFirst", "dropLast",
    "enumerated", "zip", "makeIterator", "next", "get", "set", "value", "copyBytes"}),
    # The grammar does not parse 10 of libsignal's 218 files (parameter packs `repeat (each T)`, `case .self`,
    # `catch E.c(_:)`, `() = try x`); read all the same, they lose no definition. shortcut: a Swift file that does
    # not parse is not named on stderr; to name it if a host's garbage shows.
    tolerant=True)


# Kotlin (T-0038): the grammar ships no `tags.scm`, the query is ours. A class, an interface, an enum and an `object`
# are classes; a companion object is none, its functions its class's. A function is captured as a direct child of a
# file or of a type's body, so an anonymous object's (`object : Runnable { override fun run() }`) and a local one are
# none, their calls their enclosing function's; an abstract one (no body) is none, as Java's. An extension function
# `fun Foo.Bar.f()` is the method `Bar.f` by `@receiver` (as Go's): libsignal's 73, its `toFfiArgType` of each type
# apart. A secondary constructor is the method `C.constructor`. A type is named by its last name, generic or not.
# shortcut: a property's getter or setter (32 on libsignal) and an `init { }` block are no definitions, their calls
# their class's; to capture them as Swift's computed properties if a host's `explain` needs them. shortcut: the grammar
# reads no class body on one line (`class C { fun f() {} }`) and takes `Array<Int>(1)` without a trailing lambda for
# comparisons; to take a newer grammar if a host loses code to them. shortcut: a call to
# a capitalised name (`C(..)`, `Foo.Bar(..)`) is a reference to that type, a lower-case one a call, Kotlin's naming
# convention; to tell them apart by their definitions if a host breaks it.
_KT_LAST = ("[(user_type (identifier) @{c} .) "
            "(user_type (identifier) @{c} . (type_arguments) .)]")
_KT_TYPE = _KT_LAST.format(c="name")
_KT_RECEIVER = _KT_LAST.format(c="receiver")
# The name right after the modifiers, the type parameters or nothing: a receiver between them is an extension.
_KT_FUNCTION = ("[(function_declaration . name: (identifier) @name (function_body)) "
                "(function_declaration (modifiers) . name: (identifier) @name (function_body)) "
                "(function_declaration (type_parameters) . name: (identifier) @name (function_body)) "
                "(secondary_constructor \"constructor\" @name)]")
KOTLIN_QUERY = f"""
[(class_declaration name: (identifier) @name) (object_declaration name: (identifier) @name)] @class
(source_file {_KT_FUNCTION} @function)
(class_declaration [(class_body {_KT_FUNCTION} @function) (enum_class_body {_KT_FUNCTION} @function)])
[(object_declaration (class_body {_KT_FUNCTION} @function)) (companion_object (class_body {_KT_FUNCTION} @function))]
(function_declaration {_KT_RECEIVER} . name: (identifier) @name (function_body)) @function
(function_declaration (nullable_type {_KT_RECEIVER}) . name: (identifier) @name (function_body)) @function
(call_expression (identifier) @name (#not-match? @name "^[A-Z]")) @call
(call_expression (identifier) @name (#match? @name "^[A-Z]")) @reference
(call_expression (navigation_expression (identifier) @name .) (#not-match? @name "^[A-Z]")) @send
(call_expression (navigation_expression (identifier) @name .) (#match? @name "^[A-Z]")) @reference
(delegation_specifier {_KT_TYPE}) @reference
(delegation_specifier (constructor_invocation {_KT_TYPE})) @reference
(delegation_specifier (explicit_delegation {_KT_TYPE})) @reference
"""

# The common names: `get` (78 sends, `CompletableFuture.get`, linked to `TestingIntBox.get`), `toString` (32), `map`
# (31, mostly a collection's, linked to `RequestResult.map`) and `hashCode`, measured on libsignal (T-0038, `check`);
# the others are guessed: `Any`'s, the scope functions, the collections', the arrays' and the futures'. Left out, their
# sends mostly libsignal's: `await` (its `CompletableFuture.await`), `start`, `of`, and `remove` and `invoke`, whose one
# send each is libsignal's (`svrB.remove()`, `SetProfileHelpers.invoke`). shortcut: a hand-kept list; to
# extend when `check` shows a standard name among the most frequent sends linked by name (`ours?`) on a host.
KOTLIN = Language("kotlin", {".kt": (tree_sitter.Language(tree_sitter_kotlin.language()), KOTLIN_QUERY)}, frozenset({
    "get", "toString", "map", "hashCode", "equals", "compareTo", "let", "apply", "also", "run", "use", "takeIf",
    "filter", "forEach", "flatMap", "mapNotNull", "first", "firstOrNull", "last", "single", "toList", "toSet", "toMap",
    "toTypedArray", "toByteArray", "joinToString", "contains", "isEmpty", "isNotEmpty", "set", "add", "addAll", "put",
    "clear", "copyOf", "copyOfRange", "contentEquals", "contentHashCode", "close", "split",
    "thenApply", "thenCompose", "complete", "completeExceptionally", "getOrNull", "getOrThrow", "getOrElse",
    "onSuccess", "onFailure", "fold", "iterator", "next", "hasNext"}))


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
C = Language("c", {".c": (_C, C_QUERY), **dict.fromkeys((".h", ".cpp", ".cc", ".cxx", ".hpp"), (_CPP, CPP_QUERY))},
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
    # shortcut: unless the language is `tolerant`, one error node skips the whole file (protobuf: 5 Kotlin files,
    # BACKLOG.md); to make it `tolerant` once measured on its host, or a newer grammar, when one is published.
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
