Status: closed
Created: 2026-11-27

# T-0089: A query checks the graph's freshness with one stat per file

## What to build

Every query (`explain`, `callers`, `path`, `affected`, `search`, `view`) first checks that the graph is not older than the host's files (`load()`, T-0006, T-0009). Measured on 2026-11-27 after T-0087, on Django's 7107 listed paths (medians of five):

- `root.files("")` builds the sorted list of the host's files: 0.71 s, of which `is_file()` 0.38 s, the `Path`s and their sort 0.10 s, `exclude`'s patterns 0.07 s.
- `load()` then stats each of those files again for its time: 0.29 s.

The check is 0.92 s once the listing is made (`git ls-files`, 0.25 s), protobuf 0.42 s, libsignal 0.21 s. It needs neither the sort nor the `Path`s, and one `stat` per file tells both that it is a file and its time: 0.31 s on Django, 0.16 s on protobuf, 0.07 s on libsignal, the same newest time. The files it looks at are unchanged: the listing minus `exclude` and the output folder, `graphe.toml`, the local extensions and the tool's files.

## Acceptance criteria

- [x] One `stat` per file for the freshness check, no `is_file()` before it, no sort.
- [x] The same files decide freshness as before: a change to an excluded file or to `graphe/` rebuilds nothing; a change to any other listed file, to `graphe.toml` or to an extension rebuilds (the existing tests, and one for `exclude`).
- [x] A fresh query's time before and after on Django, protobuf and libsignal (medians of three), in the closing comment.

## Comments

- 2026-11-27: done. `cli._newest(listed)` replaces `_sources()` and `_tool()`: the listing minus `root.excluded()` (the output and `exclude`, which `root.files` shares), graphe.toml, the extensions and the tool's files, each one `os.stat`, a folder or a file gone skipped. A test pins the files that make the graph stale: a host file and graphe.toml do, an excluded file and `graphe/REPORT.md` (the output, not ignored in the test host) do not; it passed before the change too. A fresh query, medians of three: Django (`explain django/shortcuts.py::get_object_or_404`) 2.57 -> 2.08 s, protobuf (`callers ByteString.copyFromUtf8`) 2.11 -> 1.71 s, libsignal (`explain Timestamp.from_epoch_millis`) 1.12 -> 0.91 s. Left, a `shortcut:`: `os.scandir` per folder reads the times from the folder on Windows, 0.17 s on Django against 0.31 s.
