Status: ready-for-agent
Created: 2026-11-27

# T-0091: The core's enrichment in less time

## What to build

`core.enrich` runs after the readers, in the build's process: 11.1 s of protobuf's 53.5 s build, 3.1 s of libsignal's 16.6 s (measured 2026-11-27, the main process timed by phase, the machine at about 85% CPU load: about 2.5 times the idle times). Of protobuf's 11.1 s: `extent()` 3.7 s, `_link_documents()` 2.7 s, `notes()` 0.5 s; the remaining 4.2 s are not broken down (reading each file again, the bodies' texts, the owners of each line, the reads and writes of module variables).

`enrich` has two parts:

- **Per file**: each file read again (`read_bytes().decode().splitlines()`, the readers read it already, in another process since T-0088), the end of each body (`extent`), its displayed texts, its comment (`notes`), its module variables (`_variables`).
- **Across files**: the owners of each line, the reads and writes (a variable defined once in the host, `elsewhere`), the values written in one language and read in another (`_link_values`), the keyed links, the documents.

First profile the remainder (per phase, wall-clock, on protobuf and Django), then cut what weighs, for example:

- the per-file part in processes (as T-0088's readers, `concurrent.futures`, behind a measured threshold), each worker returning, per node, its `end`, `texts` and `notes`, and per file its variables;
- the regular expressions compiled per file (`here`, per file with local variables) or matched per line where one pass over the file's text would do;
- `_link_documents` (2.7 s on protobuf) once profiled apart.

The graph is unchanged: `graphe.json` identical, timestamps aside.

## Acceptance criteria

- [ ] The profile of `enrich` by part, on protobuf and Django, in a comment, before any change.
- [ ] `graphe.json` identical, timestamps aside, on libsignal, protobuf and Django; REPORT.md too, but the import cycles' starting file (hash order, already so); the fixtures' snapshots unchanged.
- [ ] The time of `enrich` and of the build, before and after, on the three hosts (medians of three alternated runs; say the machine's load), in the closing comment and docs/sample-hosts.md.
- [ ] A process pool, if one is used, behind a threshold measured as T-0088's was, its `shortcut:` comment and a line in ADR 0005.
- [ ] CHANGELOG.md's entry.

## Comments
