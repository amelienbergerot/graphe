Status: ready-for-agent
Created: 2026-11-27

# T-0092: One generic language's files read in several processes

## What to build

Since T-0088 each reader runs in a process of its own, so a build waits for its slowest reader. When one generic language holds most of a host (gitea: 3199 `.go` of its 6431 files; protobuf's C/C++, 1363 files, the longest reader there), that reader is the build's critical path, and the other cores wait.

BACKLOG.md measured it (2026-11-27): `read()` of protobuf's 1363 C/C++ files, 6.26 s serial, 1.92 s over 4 processes, 1.60 s over 8 (x3.9), the results equal to the serial run's. The linking (the registry of names, the candidates, the sites) needs every file's definitions and stays serial.

In `generic.contribute`, the `read(language, rel, source)` of the files is split in batches over processes (`concurrent.futures`, the standard library), each batch returning its files' `(definitions, uses, generated)` in the files' order; the linking stays as it is, on the results in the same order, so the graph is the same. A file that does not parse is named on stderr as today.

- It nests in T-0088's pool: a reader already in a worker. Either the generic reader's batches go to a pool of their own (a worker that starts a pool: measure the cost), or T-0088's pool takes the batches of the largest generic language beside the other readers. Choose by measure, and write the choice in ADR 0005.
- A threshold, measured as T-0088's was (the batches' start-up cost against the files read), as a `shortcut:`.
- What `read()` returns must pickle (tree-sitter nodes do not: check what `definitions` and `uses` hold).

Sample host: gitea (docs/sample-hosts.md: clone it at its pinned commit, `git config core.longpaths true`), and protobuf.

## Acceptance criteria

- [ ] `graphe.json` identical, timestamps aside, on gitea, protobuf and libsignal; the fixtures' snapshots unchanged.
- [ ] The build's time before and after on gitea, protobuf and libsignal (medians of three alternated runs; say the machine's load), in the closing comment and docs/sample-hosts.md; gitea's row of the README's "Tested on" table updated if measured on an idle machine.
- [ ] A file that does not parse is still named, once.
- [ ] ADR 0005 amended; CHANGELOG.md's entry; BACKLOG.md's entry "The generic reader reads its files one after the other" settled.

## Comments
