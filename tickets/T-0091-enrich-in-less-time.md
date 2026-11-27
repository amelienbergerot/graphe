Status: closed
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

- [x] The profile of `enrich` by part, on protobuf and Django, in a comment, before any change.
- [x] `graphe.json` identical, timestamps aside, on libsignal, protobuf and Django; REPORT.md too, but the import cycles' starting file (hash order, already so); the fixtures' snapshots unchanged.
- [x] The time of `enrich` and of the build, before and after, on the three hosts (medians of three alternated runs; say the machine's load), in the closing comment and docs/sample-hosts.md.
- [x] A process pool, if one is used, behind a threshold measured as T-0088's was, its `shortcut:` comment and a line in ADR 0005. None used (the closing comment says why).
- [x] CHANGELOG.md's entry.

## Comments

- 2026-11-27: the profile, before any change. `enrich` alone on the graph the readers leave (pickled from `assemble()` at HEAD 1946378, then `enrich` timed by phase, wall-clock, markers put into its source), the machine at about 25% load:

  | phase | libsignal | protobuf | Django |
  |---|---|---|---|
  | each file read again | 0.24 s | 0.45 s | 0.48 s |
  | the bodies: `extent`, texts, `notes` | 0.40 s | 1.76 s | 1.21 s |
  | the owners of each line | 0.03 s | 0.13 s | 0.07 s |
  | the module variables (`_variables`, their `extent` and `notes`) | 0.00 s | 0.03 s | 0.12 s |
  | the reads, writes and values, per owned line | 0.19 s | 1.13 s | 2.41 s |
  | `_link_values`, the keys | 0.00 s | 0.00 s | 0.01 s |
  | `_link_documents` | 0.29 s | 1.47 s | 0.77 s |
  | **total** | 1.17 s | 5.00 s | 5.10 s |

  Under cProfile (protobuf 13.7 s, Django 11.4 s, its overhead included), by own time: `_comment` 2.4 M calls on protobuf (2.3 s), 1.3 M on Django (1.1 s), from `extent` and from the per-line loop, each a loop of five `startswith`; `extent` 74302 calls on protobuf (1.3 s own, 8.1 s with what it calls), a class's extent going through its methods' lines again; `_scan` 1.2 M calls (1.2 s), `_indent` 1.6 M (1.1 s, `expandtabs` twice per call, up to three calls per line in `extent`); `_cited` 163345 calls on protobuf (1.1 s), the text of each body joined and searched again, a class's holding its methods'; on Django `re.Pattern.findall` 1.4 s, most of it `elsewhere`, an alternation of every module variable's name defined once in the host, tried at each `.` of each owned line.

- 2026-11-27: done, without a process pool. Four exact cuts in `core.py`, each checked by running HEAD's `enrich` and the new one on fresh loads of the same pickled graph (libsignal, protobuf, Django, Grid Zero, 4cast), the two graphs equal node for node and link for link, order aside:

  - `extent` takes each line's indentation once (it took it up to three times), `_indent` skips `expandtabs` on a line without a tab, `_scan` counts the brackets of a line without a quote in two `count` calls; `extent` and the per-line loop test a comment with one `startswith` on `COMMENTS`, not a call to `_comment` (2.4 M calls on protobuf), which stays for the comment's text.
  - `elsewhere` (the alternation of every module variable's name defined once in the host) runs only on a line where a word right after `x.` (`AFTER_DOT`) is one of those names: what `elsewhere` finds is such a word, so the filter drops no line where it finds something; it still decides what is found (a chain `a.X.Y` where `X` matches hides `Y`, as before). Django's `elsewhere` 1.24 -> 0.25 s, the filter included. A test: a name defined once read after `x.` and after `a.b.`, not where the word after the dot is another name; it fails with the filter broken.
  - `_link_documents`: with the default identifier (`\bT-\d{4}\b`), a file whose text has none has no body that cites one, a body's text being a piece of its file's cut at line ends, where `\b` holds as at a text's ends; its bodies' texts are no longer joined and searched. `T-` is looked for first, the pattern starting with `\b` that `re` tries at each character (the search alone was 0.77 s on protobuf). A custom identifier (4cast's has `^` and lookbehinds, which can match in a piece and not in the whole) searches each body as before: a `shortcut:` says so. protobuf's bodies 1.25 -> 0.13 s, Django's 0.74 -> 0.11 s (no file of either has a `T-NNNN`).

  **`enrich` alone**, by phase, on the same pickles as the profile above (load about 21%):

  | phase | libsignal | protobuf | Django |
  |---|---|---|---|
  | each file read again | 0.24 -> 0.28 s | 0.45 -> 0.55 s | 0.48 -> 0.47 s |
  | the bodies: `extent`, texts, `notes` | 0.40 -> 0.25 s | 1.76 -> 1.03 s | 1.21 -> 0.87 s |
  | the reads, writes and values, per owned line | 0.19 -> 0.15 s | 1.13 -> 0.62 s | 2.41 -> 1.35 s |
  | `_link_documents` | 0.29 -> 0.12 s | 1.47 -> 0.30 s | 0.77 -> 0.16 s |
  | **total** | 1.17 -> 0.84 s | 5.00 -> 2.68 s | 5.10 -> 3.09 s |

  **The build** (`graphe build`, HEAD 1946378 in a worktree against the new, alternated, medians of three, the readers' cache warm for both, the load measured before each run):

  | host | `enrich` in the build | the build | load |
  |---|---|---|---|
  | libsignal | 1.40 -> 0.88 s | 6.34 -> 5.81 s | 7 to 35% |
  | protobuf | 5.50 -> 3.07 s | 21.44 -> 19.02 s | 4 to 23% |
  | Django, first series | 5.58 -> 3.90 s | 34.99 -> 38.94 s | 6 to 23% |
  | Django, second series | 5.64 -> 3.57 s | 37.87 -> 36.74 s | 5 to 27% |

  Django's build spreads over 31 to 42 s from one run to the next, either side: no conclusion on its total, its `enrich` 2 s less in every run.

  **No pool**: what is left is 0.8 to 3 s, of which a pool would take back its start (0.64 s measured by T-0088 on a host of 4 files) and the transfer of each file's lines or results; the per-line loop needs what all the files define (`unique`, `variables`), so it would split in two passes. Left to T-0092's measures if the core weighs again. What remains, by own time: `extent`'s loop over a class's lines and then again over each of its methods', the files read again (the readers read them in their processes), the per-line loop of Django's Python (`AFTER_DOT`, `here`, `PY_QUALIFIED`, 0.5 s together).

  **The graph**: `graphe.json` identical, `built` and `built_s` aside, on libsignal, protobuf and Django; REPORT.md identical on libsignal and protobuf but its "Built on" line; on Django, 14 lines of "Import cycles" differ: the report keeps the first 20 of `nx.simple_cycles` sorted by their own order, which starts in hash order, so the cycles shown and their first file change between any two runs (already so). The fixtures' link snapshots unchanged (`test_snapshots`); 146 tests pass.
