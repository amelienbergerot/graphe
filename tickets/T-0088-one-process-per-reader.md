Status: ready-for-agent
Blocked by: T-0087
Created: 2026-11-27

# T-0088: The readers run in parallel, one process each

## What to build

A stale query waits for a whole build: 36 s on Django (the Python reader 15.9 s warm), 30.6 s on protobuf (the C/C++ reader 7.4 s), 9.3 s on libsignal, every reader in turn (measured 2026-11-27, medians of three runs). The readers are independent: each returns its contribution, which `assemble` takes in the order of `READERS`.

The readers of this repository run at once, one process each (`concurrent.futures`, the standard library only); their contributions are taken in the order of `READERS`, so the graph is the same. Processes, not threads: py-tree-sitter 0.26.1 holds the GIL while it parses and while a `QueryCursor` matches (4 to 8 threads: x0.85 to x1.02), and the Python reader's ast walk is Python. A pool's fixed cost on Windows, measured: 0.16 to 0.30 s to start, 0.3 s to bring back protobuf's C/C++ contribution (25 MB pickled).

- The local extensions (`contribute(project)` declared in `graphe.toml`) stay in the main process, as today.
- No setting. A build where a single reader has files stays serial. The start-up cost (about 0.6 s with the imports) is measured on the fixtures and Grid Zero; if it shows, a measured threshold, as a `shortcut:`.
- A reader that raises stops the build with the same message as today. The order of the lines on stderr between readers is no longer guaranteed.
- What stays serial, whatever the split: `core.enrich` and the communities, about 9 to 10 s on protobuf and Django; the floor.

Estimated: Django 36 -> about 30 s, protobuf 30.6 -> about 20 s, libsignal 9.3 -> about 5.5 s.

An ADR: processes rather than threads (the GIL measured), and the rule that a reader of this repository and its contribution must pickle.

## Acceptance criteria

- [ ] The readers run in parallel processes, their contributions taken in the order of `READERS`; the local extensions in the main process.
- [ ] `graphe.json` identical, timestamps aside, on libsignal, protobuf and Django; the fixtures' snapshots unchanged.
- [ ] The build's time before and after on the three hosts, and the start-up cost on a small host (the fixtures, Grid Zero), in the closing comment and docs/sample-hosts.md.
- [ ] A reader's error stops the build with the same message as before.
- [ ] The ADR, and CHANGELOG.md's entry.

## Blocked by

- T-0087 (its listing once and parsing once, measured first, so this ticket's gain is its own).

## Comments
