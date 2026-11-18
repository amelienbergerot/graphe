Status: ready-for-agent
Type: task
Part of: T-0030
Created: 2026-11-19
Blocked by: T-0031

# T-0033: Java on protobuf

## What to build

A Java host gets a graph with no configuration: `explain`, `callers`, `path` and `search` answer on its functions, methods (`Class.method`) and types, with the tickets that cite them, through the generic reader of T-0031 (ADR 0003). Its queries were proven on a snippet in T-0031; this ticket gives Java its entry and its measure. Proven on the sample host `protocolbuffers/protobuf`.

## Acceptance criteria

- [ ] The readers' registry has a `java` entry; its `Language` is data only; its grammar is pinned in the main dependencies.
- [ ] Its queries are ours, written from the grammar's `tags.scm` in the capture convention of T-0031, and tested at the internal seam `read(language, file, source)` on a snippet: definitions, `Class.method`, calls with their owner.
- [ ] `new C()` and `extends C` are `references` to the class, tested.
- [ ] `protocolbuffers/protobuf`, at a pinned commit (added to the sample hosts document if no ticket pinned it yet), builds with no dangling link; its Java `check` coverage, its build time and three `explain` or `callers` queries compared with grep are noted in this ticket's comments.
- [ ] The common method names are tuned from `check`'s most frequent Java names by name.
- [ ] The readers document has Java's section (suffixes, grammar and version, nodes, links and confidence, quirks, `shortcut:` limits, sample host); the README's "Tested on" table has `protocolbuffers/protobuf`'s row, or its Java column if the row exists, measures only.
- [ ] The existing hosts checked for Java files: noted, kept or excluded; the existing readers' nodes and links unchanged.
- [ ] What the generic reader misses on `protocolbuffers/protobuf` is in BACKLOG.md, naming the host.
- [ ] The tests pass.

## Blocked by

T-0031.
