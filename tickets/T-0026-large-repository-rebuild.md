Status: needs-info
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0026: A large repository's rebuild

## What to build

BACKLOG.md (Django): 2943 Python files, 48 s per build, and an edit not yet committed makes the graph stale: every query waits. User story 8 of T-0001 forbids answering from a stale graph. Measure the build without the profiler, take the speedups that keep the graph identical; if only an incremental build remains, the decision goes to the user.

## Acceptance criteria

- [x] The build's breakdown on Django noted here, before and after.
- [x] Django, Grid Zero, dpe and 4cast give the same graph.

## Comments

- **The breakdown on Django** (no profiler, 2026-11-18), before -> after: Python reader 21.1 -> 18.0 s, layout 11.0 s (the `spring_layout` of the communities under 1000 nodes, and the spiral), Louvain communities 4.7 s, core 4.2 s, JS reader 1.7 s, insertion and sorting 2.6 s; total 47.8 -> 45.5 s.
- **Taken, the graph identical** (Django, Grid Zero, dpe, 4cast: graphe.json byte for byte, timestamps aside): `_read_locals` walks a function's nodes once, not twice; `_parent_id` reads a table, no longer every class and function per class.
- **What remains costs the graph or a decision:** the Python reader's time is its walk of the ast (`ast.iter_child_nodes`, 13 million calls); the layout and Louvain cannot be cut without moving positions and communities (the user kept positions in graphe.json, T-0016). The levers left, for the user to choose:
  1. an incremental build: only the files that changed are read again. The Python reader resolves types across modules, so it is a cache per file plus a resolution redone in full: a large change.
  2. the layout outside the queries: a query that rebuilds writes graphe.json without x, y, and `graphe build` (the hooks) computes them: about 12 s less per stale query on Django, the snapshot of Grid Zero without x, y.
  3. nothing: 45 s on a repository of Django's size, the hooks rebuild after each commit.
- **The user's decision** (2026-11-18): nothing for now; none of the hosts is of Django's size (Grid Zero builds in about 6 s). The ticket stays open, to take up when one is.
- **Lever 1, measured before writing it** (Django, each phase in its own process): parse 2.3 s, parse + definitions 10.0 s, the whole Python reader 22.6 s; the definitions of every module loaded from one pickle 2.7 s. So about 7 s at best out of ~45 s; the user chose it anyway (2026-11-18).
- **Taken**: each Python file's parse and definitions (its `Module`, its classes and functions) in `graphe/cache/<key>.pickle`, the key a hash of `graphe_python.py`, the Python version, the path and the content; an entry no file uses any more is removed. The resolution across modules (the emit) is redone in full. Django's definitions: 10.3 -> 5.7 s warm (one pickle per file costs more than one for all). The first read of entries just written is slower on this machine (16 to 29 s once, the antivirus probably); a commit rewrites only the files it changed.
- **The same graph** (graphe.json, timestamps aside): HEAD's tool = the new one without cache = with the cache = after a function added to one file, with the cache and without, on Django, Grid Zero, dpe and 4cast; Grid Zero's snapshot (`graphe_reference.py comparer`): identical.
- What remains: ~40 s per stale query on Django; lever 2 (the layout outside the queries, ~11 s) is still open if a host of that size comes: the ticket stays open, as decided.
