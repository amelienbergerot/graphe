Status: closed
Type: task
Part of: T-0030
Created: 2026-11-19

# T-0031: The generic reader, Go on gitea

## What to build

A Go host gets a graph with no configuration: `explain`, `callers`, `path` and `search` answer on its functions, its methods (`T.M`, though `func (r *T) M()` is declared outside its type) and its types, with the tickets that cite them. This is the first slice of T-0030: the whole generic reader (ADR 0003), proven end to end on one language and one sample host, gitea; the capture convention proven on snippets for Rust and Java too, before the other languages come in. The documents that make the work visible are born here: the readers document, the sample hosts document, the README's "Tested on" table.

## Acceptance criteria

- [x] A generic reader module: a `Language` is data only (grammars by suffix, queries, common method names); the reading, the owner of a call, the `Class.method` naming and the linking are written once (T-0030, Implementation Decisions).
- [x] One capture convention (`@function`, `@method`, `@class`, `@name`, `@call`, `@send`, `@reference`, `@receiver`), queries of ours written from the grammar's `tags.scm`.
- [x] Linking: a call linked by the name alone (`INFERRED`) only when its name has a single definition in the language; an ambiguous one not attributed (and counted by `explain`, T-0025); a `@send` link marked `?`; a common name never linked from a `@send`; `@reference` becomes `references`; every call a coverage site with its verdict.
- [x] Ids carry the file's extension; a file that does not parse is skipped and named on stderr, the build goes on.
- [x] The readers' registry has a `go` entry; the Go grammar is pinned in the main dependencies.
- [x] Tests at the internal seam `read(language, file, source)`: a Go snippet (`func (r *T) M()` is `T.M`), a Rust snippet (a function of `impl T` is `T.f`) and a Java snippet (a class, its methods, `new C()`), with their calls and owners. The Rust and Java queries and grammars land here; their `rust` and `java` entries do not (T-0032, T-0033).
- [x] Tests at the external seam `contribute(project)`, with a fake project over files in a temporary folder: unique name linked, ambiguous name not attributed, `?` on a receiver call, a common name not linked, no link from one language to another, a file that does not parse.
- [x] gitea, at a pinned commit, builds with no dangling link; its `check` coverage, its build time and three `explain` or `callers` queries compared with grep are noted in this ticket's comments; the common names are tuned from `check`'s most frequent names by name.
- [x] The readers document: the generic reader's section (the convention, the linking rules, how to add a language), Go's section (suffixes, grammar and version, nodes, links and confidence, quirks, `shortcut:` limits, sample host), and a short section per dedicated reader (Python, JS/TS/Svelte, GDScript, PHP) pointing to its module's docstring.
- [x] The sample hosts document: Django (T-0016, T-0026) and gitea, each with its URL, pinned commit, shallow clone command, languages, `graphe.toml` exclusions and the tickets that measured it.
- [x] The README: a "Tested on" table (host, languages, files, build time, one query compared with grep) with Django's and gitea's rows, measures only; the README and the skill point to the readers document for the list of readers.
- [x] The existing hosts (Grid Zero's reference test, dpe, 4cast, the tool itself) checked: the existing readers' nodes and links unchanged; any Go file they carry noted, kept or excluded.
- [x] What the generic reader misses on gitea is in BACKLOG.md, naming the host.
- [x] The tests pass.

## Blocked by

None (can start immediately).

## Comments

- **The module** (2026-11-19): `src/graphe_generic.py`. `Language` (name, grammar and query per suffix, common names) for Go, Rust and Java; `read(language, file, source)` gives the definitions and the uses with their owners; `contribute(language, project)` the nodes, links and sites. Only `go` is in `READERS`. A new verdict, `common` (a send of a common name the host defines), is not attributed: `explain` counts it (T-0025, `UNATTRIBUTED`). A host without Go files gets no contribution at all, so its `graphe.json` has no `go` coverage.
- **The existing hosts** (none carries a `.go`, `.rs` or `.java` file): Grid Zero, dpe, 4cast and the tool itself built by HEAD's tool and by this one: `graphe.json` identical, the build's duration aside; Grid Zero's reference test (`graphe_reference.py comparer`): identical.
- **gitea** (`c376d5d`, 6431 files, 3199 `.go`, 276 `.ts`): 23878 nodes, 63819 links, 0 dangling. Build 31.3 / 31.9 / 31.4 s (warm; the first, cold, 55 s), the JS reader included. 47 Go files do not parse (Go 1.26's `new(expr)` and generic methods, grammar 0.25.0): skipped and named (BACKLOG.md).
- **Coverage** (`graphe check`, go, 155575 sites): before the common names `ours?` 57895, `external` 51542, `ambiguous` 46105; the common names taken from the most frequent sends linked by name whose receiver is a standard package (`filepath.Join` 345, `strings.NewReader` 290, `strings.HasPrefix` 276, `log.Fatal` 134, xorm's `cond.And` 307, `sess.Exec`...): `ours?` 52902, `external` 51542, `ambiguous` 27174, `common` 23957. One pattern added on the measure: `g[int](x)` is a type conversion in the grammar's tree, now a call.
- **Three queries against grep** (bytes of the answer):
  - `explain GetRepositoryByID`: what it calls (`GetEngine`, `references` `ErrRepoNotExist`) and 72 callers by name, 1770 bytes; grep `GetRepositoryByID(`: 80 lines in 63 files, 7813 bytes (the definition, comments, and calls in skipped files included).
  - `callers DecodeJSON`: 223 callers, 15772 bytes; grep: 689 lines in 134 files, 72802 bytes. The 533 calls the graph sees plus 155 grep finds in skipped files: the gap is the parse, not the linking.
  - `explain AssertExistsAndLoadBean`: 831 callers by name, the first 25 shown, 1854 bytes; grep: 2893 lines in 377 files, 367261 bytes.
- **Django** (README row, docs/sample-hosts.md): `9e2e5a3` gives T-0016's graph exactly (49936 nodes, 153089 links); warm build 54.9 / 54.4 / 54.8 s (the cache of T-0026 filled first). `explain django/shortcuts.py::get_object_or_404`: 839 bytes, as in T-0016; grep `get_object_or_404(`: 21 lines, 2130 bytes.
- **The documents**: `docs/readers.md` (the generic reader, Go, Rust and Java's queries not registered yet, the dedicated readers), `docs/sample-hosts.md` (Django, gitea), the README's "Tested on" table and its pointer to the readers; the skill points to the readers document; `docs/contribution.md` and `--help` name the `go` reader.
- **Not checked**: Linux and macOS wheels of the three grammars.
- **The review** (2026-11-19, standards and spec): the common names carry their `shortcut:`, "common name" is in GLOSSARY.md; what it found in Rust's and Java's queries (an `impl` in another file than its `struct`, `impl Tr for &T`, Java's overloads, anonymous and nested classes) is in T-0032 and T-0033, which register those languages. Closed.
