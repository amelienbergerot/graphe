Status: closed
Created: 2026-11-27

# T-0087: A build lists the host's files once and parses each file once

## What to build

Two serial costs of a build, measured on 2026-11-27 while weighing a parallel build (the grilling of that day):

- `Project.files(suffix)` walks the whole host at each call: about 0.23 s per suffix on Django, 5.6 s per build; the C reader spends 1.4 s listing there and finds no file. protobuf: 1.6 s.
- `generic.generated()` parses again each file that carries a generator's marker (T-0079): 2.7 s on protobuf (C/C++ 1.01, C# 1.05, Java 0.68).

The host's files are listed once per build, each suffix served from that one listing. `read()` looks for the marker on the tree it has just parsed, so a file is parsed once. The graph is unchanged.

## Acceptance criteria

- [x] The host is walked once per build, whatever the number of readers and suffixes.
- [x] A generic file is parsed once; the generated files named are the same.
- [x] `graphe.json` identical, timestamps aside, on libsignal, protobuf and Django (docs/sample-hosts.md, their pinned commits); the fixtures' snapshots unchanged.
- [x] The build's time before and after on the three hosts (medians of three runs), in the closing comment and docs/sample-hosts.md.

## Comments

- 2026-11-27: done. `root.listing()` is the one `git ls-files` of a build: `assemble()` makes it and hands it to every `Project` (readers and extensions) and to `core.enrich` for the documents; `root.files(suffix, root, listed)` filters it, and lists by itself when called outside a build (the staleness check, the tests). A test counts the `git ls-files` of a build with two readers, a document and an extension: 25 before, 1 now. `read(language, file, source)` returns a third value, whether the file is generated, found on the tree it parsed (`_marked`); the leading comments' text is taken from the source before erasure, but the leading comments are those of the erased tree, so a C# `#if` line, or a C/C++ macro, before the marker no longer hides it (a test; none on protobuf); `generated()` is gone. On the pinned hosts, `graphe.json` identical to the build before, timestamps aside, and REPORT.md too, its 204 generated files of protobuf among it, except Django's import cycles: the same cycles, each started from another file, as `simple_cycles` starts from the hash order of the run (it was so before). The build, medians of three runs alternating the old code and the new: Django 44.6 -> 35.8 s, protobuf 34.5 -> 30.3 s, libsignal 10.9 -> 9.1 s. A first series, the old code's three runs before the new code's three, gave Django 65.2 -> 36.1 s: the old runs were 65.2, 73.8, 41.9 s, the Python reader's slowness BACKLOG.md notes, which the alternated series avoids.
