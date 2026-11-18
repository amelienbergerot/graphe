Status: ready-for-agent
Type: task
Part of: T-0030
Created: 2026-11-19

# T-0031: The generic reader, Go on gitea

## What to build

A Go host gets a graph with no configuration: `explain`, `callers`, `path` and `search` answer on its functions, its methods (`T.M`, though `func (r *T) M()` is declared outside its type) and its types, with the tickets that cite them. This is the first slice of T-0030: the whole generic reader (ADR 0003), proven end to end on one language and one sample host, gitea; the capture convention proven on snippets for Rust and Java too, before the other languages come in. The documents that make the work visible are born here: the readers document, the sample hosts document, the README's "Tested on" table.

## Acceptance criteria

- [ ] A generic reader module: a `Language` is data only (grammars by suffix, queries, common method names); the reading, the owner of a call, the `Class.method` naming and the linking are written once (T-0030, Implementation Decisions).
- [ ] One capture convention (`@function`, `@method`, `@class`, `@name`, `@call`, `@send`, `@reference`, `@receiver`), queries of ours written from the grammar's `tags.scm`.
- [ ] Linking: a call linked by the name alone (`INFERRED`) only when its name has a single definition in the language; an ambiguous one not attributed (and counted by `explain`, T-0025); a `@send` link marked `?`; a common name never linked from a `@send`; `@reference` becomes `references`; every call a coverage site with its verdict.
- [ ] Ids carry the file's extension; a file that does not parse is skipped and named on stderr, the build goes on.
- [ ] The readers' registry has a `go` entry; the Go grammar is pinned in the main dependencies.
- [ ] Tests at the internal seam `read(language, file, source)`: a Go snippet (`func (r *T) M()` is `T.M`), a Rust snippet (a function of `impl T` is `T.f`) and a Java snippet (a class, its methods, `new C()`), with their calls and owners. The Rust and Java queries and grammars land here; their `rust` and `java` entries do not (T-0032, T-0033).
- [ ] Tests at the external seam `contribute(project)`, with a fake project over files in a temporary folder: unique name linked, ambiguous name not attributed, `?` on a receiver call, a common name not linked, no link from one language to another, a file that does not parse.
- [ ] gitea, at a pinned commit, builds with no dangling link; its `check` coverage, its build time and three `explain` or `callers` queries compared with grep are noted in this ticket's comments; the common names are tuned from `check`'s most frequent names by name.
- [ ] The readers document: the generic reader's section (the convention, the linking rules, how to add a language), Go's section (suffixes, grammar and version, nodes, links and confidence, quirks, `shortcut:` limits, sample host), and a short section per dedicated reader (Python, JS/TS/Svelte, GDScript, PHP) pointing to its module's docstring.
- [ ] The sample hosts document: Django (T-0016, T-0026) and gitea, each with its URL, pinned commit, shallow clone command, languages, `graphe.toml` exclusions and the tickets that measured it.
- [ ] The README: a "Tested on" table (host, languages, files, build time, one query compared with grep) with Django's and gitea's rows, measures only; the README and the skill point to the readers document for the list of readers.
- [ ] The existing hosts (Grid Zero's reference test, dpe, 4cast, the tool itself) checked: the existing readers' nodes and links unchanged; any Go file they carry noted, kept or excluded.
- [ ] What the generic reader misses on gitea is in BACKLOG.md, naming the host.
- [ ] The tests pass.

## Blocked by

None (can start immediately).
