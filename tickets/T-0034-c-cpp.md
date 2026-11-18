Status: ready-for-agent
Type: task
Part of: T-0030
Created: 2026-11-19
Blocked by: T-0031

# T-0034: C/C++ on protobuf, with its build time

## What to build

A C/C++ host gets a graph with no configuration: `explain`, `callers`, `path` and `search` answer on its functions, methods (`Class.method`) and types, with the tickets that cite them, through the generic reader of T-0031 (ADR 0003). C and C++ are one family, the single entry `c`: `.c` reads with the C grammar, `.h`, `.cpp`, `.cc`, `.cxx` and `.hpp` with the C++ one, and a C++ call to a C function is linked. The upstream `tags.scm` of both capture no call: the call queries are wholly ours. protobuf is the largest sample host: its build time decides whether the generic reader needs a cache. Proven on the sample host `protocolbuffers/protobuf`.

## Acceptance criteria

- [ ] The readers' registry has a `c` entry; its `Language` is data only; its grammar is pinned in the main dependencies.
- [ ] Its queries are ours, written from the grammar's `tags.scm` in the capture convention of T-0031, and tested at the internal seam `read(language, file, source)` on a snippet: definitions, `Class.method`, calls with their owner.
- [ ] Both grammars pinned; a test at `contribute(project)`: a C++ call to a function defined in a `.c` file is linked, and a `.h` declaration is read.
- [ ] protobuf's whole build time measured; if the generic reader weighs heavily, a BACKLOG.md entry for a per-file cache reusing T-0026's mechanism. The Python and PHP readers' result on protobuf noted as a cross-check.
- [ ] `protocolbuffers/protobuf`, at a pinned commit (added to the sample hosts document if no ticket pinned it yet), builds with no dangling link; its C/C++ `check` coverage, its build time and three `explain` or `callers` queries compared with grep are noted in this ticket's comments.
- [ ] The common method names are tuned from `check`'s most frequent C/C++ names by name.
- [ ] The readers document has C/C++'s section (suffixes, grammar and version, nodes, links and confidence, quirks, `shortcut:` limits, sample host); the README's "Tested on" table has `protocolbuffers/protobuf`'s row, or its C/C++ column if the row exists, measures only.
- [ ] The existing hosts checked for C/C++ files: noted, kept or excluded; the existing readers' nodes and links unchanged.
- [ ] What the generic reader misses on `protocolbuffers/protobuf` is in BACKLOG.md, naming the host.
- [ ] The tests pass.

## Blocked by

T-0031.
