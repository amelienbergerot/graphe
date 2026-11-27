Status: ready-for-agent
Created: 2026-11-27

# T-0087: A build lists the host's files once and parses each file once

## What to build

Two serial costs of a build, measured on 2026-11-27 while weighing a parallel build (the grilling of that day):

- `Project.files(suffix)` walks the whole host at each call: about 0.23 s per suffix on Django, 5.6 s per build; the C reader spends 1.4 s listing there and finds no file. protobuf: 1.6 s.
- `generic.generated()` parses again each file that carries a generator's marker (T-0079): 2.7 s on protobuf (C/C++ 1.01, C# 1.05, Java 0.68).

The host's files are listed once per build, each suffix served from that one listing. `read()` looks for the marker on the tree it has just parsed, so a file is parsed once. The graph is unchanged.

## Acceptance criteria

- [ ] The host is walked once per build, whatever the number of readers and suffixes.
- [ ] A generic file is parsed once; the generated files named are the same.
- [ ] `graphe.json` identical, timestamps aside, on libsignal, protobuf and Django (docs/sample-hosts.md, their pinned commits); the fixtures' snapshots unchanged.
- [ ] The build's time before and after on the three hosts (medians of three runs), in the closing comment and docs/sample-hosts.md.

## Comments
