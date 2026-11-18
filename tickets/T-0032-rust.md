Status: ready-for-agent
Type: task
Part of: T-0030
Created: 2026-11-19
Blocked by: T-0031

# T-0032: Rust on libsignal

## What to build

A Rust host gets a graph with no configuration: `explain`, `callers`, `path` and `search` answer on its functions, methods (`Class.method`) and types, with the tickets that cite them, through the generic reader of T-0031 (ADR 0003). Its queries were proven on a snippet in T-0031 (a function of `impl T` is `T.f`); this ticket gives Rust its entry and its measure. Proven on the sample host `signalapp/libsignal`.

## Acceptance criteria

- [ ] The readers' registry has a `rust` entry; its `Language` is data only; its grammar is pinned in the main dependencies.
- [ ] Its queries are ours, written from the grammar's `tags.scm` in the capture convention of T-0031, and tested at the internal seam `read(language, file, source)` on a snippet: definitions, `Class.method`, calls with their owner.
- [ ] `signalapp/libsignal`, at a pinned commit (added to the sample hosts document if no ticket pinned it yet), builds with no dangling link; its Rust `check` coverage, its build time and three `explain` or `callers` queries compared with grep are noted in this ticket's comments.
- [ ] The common method names are tuned from `check`'s most frequent Rust names by name.
- [ ] The readers document has Rust's section (suffixes, grammar and version, nodes, links and confidence, quirks, `shortcut:` limits, sample host); the README's "Tested on" table has `signalapp/libsignal`'s row, or its Rust column if the row exists, measures only.
- [ ] The existing hosts checked for Rust files: noted, kept or excluded; the existing readers' nodes and links unchanged.
- [ ] What the generic reader misses on `signalapp/libsignal` is in BACKLOG.md, naming the host.
- [ ] The tests pass.

## Blocked by

T-0031.

## Comments

- **From T-0031's review** (2026-11-19), Rust's query and `RUST.common` are in `graphe_generic.py`, proven on one snippet; probed, not yet fixed: a `struct T` and its `impl T` in two files are two class nodes (the merge is per file), so `T {}` is linked to neither; `impl Tr for &'a T` is not matched (no `reference_type`), its functions are free functions; `impl Tr for Vec<T>` draws a class `Vec`; `crate::m::f()` and `Self::f()` are `@send`, so a common name is never linked even by its path; the common names are guessed, to tune on the sample host.
