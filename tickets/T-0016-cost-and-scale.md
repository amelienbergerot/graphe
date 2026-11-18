Status: closed
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0016: Cheaper answers, and a large repository

## What to build

The user's request (2026-11-18): make the tool cheaper for the agent and more precise than grep, above all on large repositories. Measured before any change: Grid Zero (801 files) and a shallow clone of Django (7104 files, 2943 Python), the large host.

Baseline:

- **Django does not build**: one file written to fail parsing (`tests/test_runner_apps/tagged/tests_syntax_error.py`) stops the Python reader, so the whole build stops.
- **Build, Django** (under the profiler, once that file is skipped): 467 s, 49936 nodes, 153089 links, 919 communities. The layout of `graphe.html` takes 358 s of it: 270 s of `spring_layout` on the 19 communities above 1000 nodes (up to 4800), and 65 s of the spiral that places the communities (it tests each step against every disc already placed). Every stale query waits for this build. Grid Zero: 7.5 s, 5 of them in the layout; its largest community has 539 nodes.
- **A fresh query, Django**: 2.9 s, 1.4 s of them in the freshness check (`git ls-files`, then `is_file` twice and `stat` once per file). Grid Zero: 0.7 s.
- **Answers, Grid Zero**: `search engine`, 8.2 KB for 60 lines: each line padded to 40 and 45 columns, then the id, which repeats the file and the name. `explain engine.py::step`, 7.0 KB: every neighbour with its full path, its 21 tickets one per line with their file, and its methods without their class (`.advance()` twice, two different classes). An ambiguous name lists ids, whereas the skill tells the agent to use `file::name`.

## Acceptance criteria

- [x] A file that does not parse is skipped, named on stderr, and the build goes on.
- [x] A community above 1000 nodes gets a cheap layout; the graphs of Grid Zero, 4cast, dpe and the tool itself do not move (the user's decision: their communities stay below 1000, their snapshot stands).
- [x] The spiral and the freshness check cost less, without changing the graph.
- [x] `search`, `explain`, `callers` and an ambiguous name answer in fewer bytes, every neighbour designated by what the agent types next (`file::Class.method`).
- [x] Before and after, measured on the same queries, noted here.

## Comments

- **Fixed query set** (Grid Zero, then Django), on the graph as it is, bytes before -> after: `explain engine.py::step` 7031 -> 3569 (and it now shows its 16 reads and 10 references whole), `search engine` 8257 -> 1852, `callers engine.py::step --depth 2` 121 -> 131, the ambiguous `step` 218 -> 141, `path provoke ...` 222 -> 145; Django: `explain shortcuts.py::get_object_or_404` 936 -> 839, `search queryset` 9270 -> 2864, `callers ... --depth 2` 627 -> 580, the ambiguous `get_object_or_404` 216 -> 183.
- **The answers** (`_by_file`): a neighbour by its `name` (`Engine._apply_dispatch`, no longer `._apply_dispatch()`), one line per file with its line (`simulation/core/engine.py: Engine._bus_vm_pu:1027, ...`); the kinds outside the code (tickets, values, documents) by their name on one line; `[by name]` once on a relation whose links are all guessed, otherwise `[N by name: ?]` and a `?` after each guessed one. An ambiguous name lists the shortest text that designates each node alone (`Engine.provoke`, `django/shortcuts.py::get_object_or_404`), with its location. `search` no longer prints the ids nor pads its columns.
- **A file that does not parse** is skipped with its error on stderr (the Python reader; the tree-sitter readers already went on).
- **The layout**, the same positions to the byte: the spiral discards with numpy, by batches of 1024 steps, the steps surely blocked, and decides the others by the old exact test in order; the steps blocked even for the smallest disc are not walked again. Above 1000 nodes, a community is laid out on a sunflower spiral in the order of its files. Checked: Grid Zero's reference test (`graphe_reference.py comparer`: identical), dpe, 4cast and the tool itself built by the tool of HEAD and by this one: identical, timestamps aside; Django's 49936 positions recomputed: identical to those of the old exact test alone (the sunflower included).
- **Django's build**: 290 s with the tool of HEAD (the parse fix alone) -> 48 s; the layout went from 358 s to 11 s under the profiler. Grid Zero: 7.5 s -> about 6 s.
- **A fresh query, Django**: 2.6 s, of which 1.3 s is the freshness check (`git ls-files`, then `is_file` and `stat` on the 7104 files; the second `is_file` is gone). Grid Zero: 0.5 s.
- **Left in the backlog** (Django): a stale query on a large repository waits for a whole build (the Python reader now takes most of it), and `explain` does not say how many calls by the name it could not attribute (`QuerySet.filter`: 3 callers, hundreds by grep).
- **After the review**: a file is designated by its path, as the answers print it (`explain paquet/moteur.py`); in a file, the exact name wins (`generation.py::cle` is the variable, not `Gabarit.cle` too); an ambiguous name lists 20 candidates at most (Django's 971 `__init__`: 19 s and 972 lines before, 2.8 s now); `search` prints the hits by name before those by text and comment; `docs/contribution.md` says where `label` and `name` are shown. Not covered by an automated test: the layout's equivalence (Grid Zero's reference test, in Grid Zero, and the checks above), the sunflower, the mixed `[N by name: ?]`.
