Status: ready-for-agent
Type: task
Part of: T-0030
Created: 2026-11-19
Blocked by: T-0031

# T-0037: Swift on libsignal

## What to build

A Swift host gets a graph with no configuration: `explain`, `callers`, `path` and `search` answer on its functions, methods (`Class.method`) and types, with the tickets that cite them, through the generic reader of T-0031 (ADR 0003). The upstream `tags.scm` captures no call: the call queries are wholly ours. Proven on the sample host `signalapp/libsignal`.

## Acceptance criteria

- [ ] The readers' registry has a `swift` entry; its `Language` is data only; its grammar is pinned in the main dependencies.
- [ ] Its queries are ours, written from the grammar's `tags.scm` in the capture convention of T-0031, and tested at the internal seam `read(language, file, source)` on a snippet: definitions, `Class.method`, calls with their owner.
- [ ] A bare call and a receiver call are both captured, tested.
- [ ] `signalapp/libsignal`, at a pinned commit (added to the sample hosts document if no ticket pinned it yet), builds with no dangling link; its Swift `check` coverage, its build time and three `explain` or `callers` queries compared with grep are noted in this ticket's comments.
- [ ] The common method names are tuned from `check`'s most frequent Swift names by name.
- [ ] The readers document has Swift's section (suffixes, grammar and version, nodes, links and confidence, quirks, `shortcut:` limits, sample host); the README's "Tested on" table has `signalapp/libsignal`'s row, or its Swift column if the row exists, measures only.
- [ ] The existing hosts checked for Swift files: noted, kept or excluded; the existing readers' nodes and links unchanged.
- [ ] What the generic reader misses on `signalapp/libsignal` is in BACKLOG.md, naming the host.
- [ ] The tests pass.

## Blocked by

T-0031.
