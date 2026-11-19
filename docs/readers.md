# The readers

A reader turns a host's files of one language into nodes, links and coverage sites, through `contribute(project)` (docs/contribution.md). Each is registered in `READERS` (`src/graphe.py`) under the name of its `graphe.toml` section, the key of its configuration and of its coverage in `graphe check`.

| Section | Reader | Languages | Suffixes |
|---|---|---|---|
| `python` | dedicated, `graphe_python.py` | Python | `.py` |
| `godot` | dedicated, `graphe_godot.py` | GDScript | `.gd` |
| `php` | dedicated, `graphe_php.py` | PHP | `.php` |
| `js` | dedicated, `graphe_js.py` | JavaScript, TypeScript, Svelte | `.js`, `.mjs`, `.ts`, `.svelte` |
| `go` | generic, `graphe_generic.py` | Go | `.go` |
| `rust` | generic, `graphe_generic.py` | Rust | `.rs` |

A **dedicated reader** knows its language's imports and types, and links a call for sure where it can. The **generic reader** (ADR 0003, GLOSSARY.md) reads every other language the same way, by its name alone.

## The generic reader

`src/graphe_generic.py`. A language is data only, a `Language`: its tree-sitter grammars by file suffix, a query of ours per grammar, and its **common names**, the method names never linked from a call on a receiver. The reading, the owner of a call, the `Class.method` naming and the linking are written once.

### The capture convention

Every language's query captures the same names; a query is written from the `tags.scm` its grammar ships, and kept here, so that a grammar's upgrade does not change the graph silently.

| Capture | What it marks |
|---|---|
| `@function`, `@method`, `@class` | A definition (the whole node), with its `@name`. `@class` is a class, an interface, a struct, an enum, a trait, a Rust `impl`. |
| `@receiver` | Inside a `@method`: its type, when the method is declared outside it (Go's `func (r *T) M()`). |
| `@call` | A bare call `f()`, with `@name` the name called. |
| `@send` | A call on a receiver `x.m()`, a package `pkg.F()` or a path `T::f()`, with `@name` the method's name. |
| `@reference` | A use of a class that is not a call (`new C()`, `extends C`, Go's `T{}`), with `@name` the class. |

- A use belongs to the innermost definition that contains it; outside any, to its file.
- A `@function` inside a `@class` is a method of that class. A method's class is its `@receiver`, or else the innermost `@class` that contains it. A method is named `Class.method`.
- The classes of one name in one file are one node (Rust's `struct T` and its `impl T`, `impl Display for T`).

### Nodes

A node per file (`file`), function (`function`), method (`method`, `Class.method`) and class (`class`). Modules, packages and namespaces are not nodes. The ids carry the file's extension (`models/repo/repo.go` is `models_repo_repo_go`), so that `Foo.java` and `Foo.kt` never share an id; an id already taken gets `_2`, `_3`.

A file `contains` its definitions; a class `contains` its methods when they are in its file. Elsewhere (a Go method of a type of another file), the method's file contains it.

### Links and their confidence

Every link a use makes is by the name alone (`INFERRED`: `[by name]`, `?` in the answers), and made only when the name has **a single definition in the language**:

- `@call` and `@send` become `calls`, to the function or method of that bare name (`Save` for `T.Save`);
- `@reference` becomes `references`, to the class of that name;
- a `@send` of a common name is never linked;
- a call to its own definition (recursion) draws no link;
- no call is linked to another language: each language is its own registry entry, and sees only its own definitions.

A bare call and a send are marked alike: both are by name.

Every call or send is a coverage site, with its verdict:

| Verdict | Meaning | Linked |
|---|---|---|
| `ours?` | A single definition of that name in the language. | yes, `INFERRED` |
| `ambiguous` | Several definitions of that name. | no: `explain` counts it ("+ N calls named `f` the graph could not attribute: grep them", T-0025) |
| `common` | A send of a common name that the host defines. | no: counted by `explain` likewise |
| `external` | No definition of that name in the host (the standard library, a dependency, a builtin). | no |

A file that does not parse (any error node in its tree) is skipped and named on stderr; the build goes on. A host without the language's files gets no contribution at all, not even an empty coverage.

### Adding a language

1. Pin its grammar in the main dependencies (`pyproject.toml`, `uv add tree-sitter-<language>==<version>`).
2. Write its query in `graphe_generic.py` from the grammar's `tags.scm`, in the capture convention above: definitions with a body only (an abstract method or a signature would make each name ambiguous with its implementation).
3. Its `Language`: the name of its `graphe.toml` section, the grammar and query per suffix, a first list of common names.
4. A snippet test at the seam `read(language, file, source)` (`tests/test_generic.py`): its definitions and its uses with their owners.
5. Its entry in `READERS` (`functools.partial(graphe_generic.contribute, graphe_generic.<LANGUAGE>)`).
6. Its sample host (docs/sample-hosts.md): build, no dangling link, `graphe check`; tune the common names from the most frequent sends linked by name; three queries compared with grep; its README row and its section here; what it misses in BACKLOG.md, naming the host.

A quirk the query cannot express is a `shortcut:` in its section here. A language that needs code of its own is the proof that it needs a dedicated reader (ADR 0003).

## Go

- **Section**: `go`. **Suffixes**: `.go`.
- **Grammar**: `tree-sitter-go` 0.25.0 (py-tree-sitter 0.26.1).
- **Nodes**: a `function` per `func f()`; a `method` `T.M` per `func (r T) M()`, `func (r *T) M()` and their generic forms (`*T[K]`), its class the receiver's type; a `class` per type declaration (`type T struct`, `interface`, and any other `type T ...`). An interface's method specs are not nodes: each would make its implementations' name ambiguous.
- **Links**: `f()` and `f[T](x)` are `@call`; `x.M()` and `pkg.F()` are `@send`, so a package's functions follow the common names. `T{}`, `&pkg.T{}` and an embedded field (`struct { Base }`) are `references` to `T`. All `INFERRED`.
- **Common names**: the standard library's names that one function of gitea would collect from every `filepath.Join`, `strings.NewReader`, `strings.HasPrefix`, `log.Fatal`, xorm's `cond.And` and `sess.Exec` (measured from `graphe check` on gitea, T-0031), and the methods of Go's common interfaces (`String`, `Error`, `Close`, `Read`, `Write`, `Len`...). The list is `GO.common`.
- **Quirks**: a type conversion `T(x)` is a call to `T`, so `external` (no function `T`). The methods of a type declared in several packages under one name are one name too (`Repository.Load...`): ambiguous unless unique.
- **Limits**:
  - `shortcut:` a file with one error node is skipped whole: grammar 0.25.0 knows neither Go 1.26's `new(expr)` nor generic methods, 47 of gitea's 3199 files (BACKLOG.md); to upgrade the grammar when one does, or to read the valid part of a tree.
  - `shortcut:` a call through a value (`handlers[name](ctx)`, a field holding a func) and a function passed as a value are not uses; to read if a host needs it.
  - `shortcut:` no imports: `pkg.F()` links to any `F` of the host, `strings.Join` included when the host defines one `Join` and `Join` is not common.
- **Sample host**: gitea (docs/sample-hosts.md).

## Rust

- **Section**: `rust`. **Suffixes**: `.rs`.
- **Grammar**: `tree-sitter-rust` 0.24.2 (py-tree-sitter 0.26.1).
- **Nodes**: a `function` per `fn f()` with a body; a `method` `T.f` per function of an `impl T`, `impl Tr for T`, `impl Tr for &'a T` (and their generic and `path::T` forms) or of a `trait T` (a default method); a `class` per `struct`, `enum`, `union`, `trait` and `impl`. A trait's signatures without a body are not nodes: each would make its implementations' name ambiguous.
- **Links**: `f()` is `@call`; `x.f()`, `T::f()` and `crate::m::f()` are `@send`, so a path follows the common names. `T { .. }` and `path::T { .. }` are `references` to `T`. All `INFERRED`.
- **Common names**: the standard library's and the usual crates' (tokio, futures, http) names that one function of libsignal would collect from every `Vec::with_capacity`, `std::future::ready`, `f.debug_struct(..).field`, `x.ok()` (measured from `graphe check` on libsignal, T-0032), and the methods of Rust's common traits (`new`, `default`, `clone`, `from`, `into`, `fmt`...). The list is `RUST.common`.
- **Quirks**: `Ok(x)`, `Some(x)`, `Err(e)` and a tuple struct `T(x)` are calls, `external` (no function of that name).
- **Limits**:
  - `shortcut:` a macro's arguments are tokens to the grammar: a call inside `assert_eq!`, `vec![]`, `format!` is not a use (libsignal: 8604 macro invocations, BACKLOG.md); to parse a token tree as expressions when it parses.
  - `shortcut:` the classes of one name are one node per file only: a `struct T` and its `impl` in another file are two classes, so `T { .. }` is ambiguous (libsignal: 605 of 3250); `impl<T> Tr for T` draws a class `T`, `impl Tr for Vec<X>` a class `Vec` (BACKLOG.md); to merge a class's nodes across files.
  - `shortcut:` `T::f()` is linked by `f` alone, so `T::new()` is never linked (`new` is common) and `KeyPair::generate` is ambiguous between 6 types (BACKLOG.md); to link a path to its type's method if ADR 0003 allows it.
  - `shortcut:` a file with one error node is skipped whole: grammar 0.24.2 rejects `dyn 'a + Trait`, 1 of libsignal's 612 files (BACKLOG.md); to upgrade the grammar when one does, or to read the valid part of a tree.
- **Sample host**: libsignal (docs/sample-hosts.md).

## Java (not registered yet)

Its grammar (`tree-sitter-java` 0.23.5) and query are in `graphe_generic.py`, proven on a snippet (T-0031): a Java class, its methods and its constructor (`C.C`), `new C()`, `extends`, `implements` as `references`. Its `java` entry, section and sample host come with T-0033. The limits already probed (overloads, anonymous and nested classes) are in that ticket.

## The dedicated readers

Each is specified in its module's docstring.

- **Python**, `graphe_python.py`: the `ast`, a call resolved by its receiver's type (annotations, constructions, returns), by the name alone otherwise; a cache of each file's definitions (T-0026).
- **GDScript**, `graphe_godot.py`: by patterns, a `preload` constant designates its script, a variable typed by it or made by `X.new()` sends its calls there; `check` recounts the calls.
- **PHP**, `graphe_php.py`: by patterns, its functions, the actions of a `switch ($action)`, the calls of the file's top (T-0023).
- **JavaScript, TypeScript, Svelte**, `graphe_js.py`: tree-sitter, ES imports and re-exports followed, `new C()` and `f()` assigned typed, by the name otherwise; a Svelte component's script and markup (T-0014, T-0015, T-0022).
