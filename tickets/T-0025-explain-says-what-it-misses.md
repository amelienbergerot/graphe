Status: closed
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0025: `explain` says the calls it could not attribute

## What to build

BACKLOG.md (Django): `explain query.py::QuerySet.filter` gives 3 callers, grep hundreds of `.filter(`: a receiver of unknown type (`Model.objects.filter`). The build keeps, per name, the number of call sites no reader attributed; `explain` shows "N calls named `filter` not attributed: grep" so that the agent knows when to grep.

## Acceptance criteria

- [x] `explain` of a method called on an unknown receiver says how many calls of its name are not attributed.
- [x] SKILL.md says what the line means.

## Comments

- `build` keeps the sites `assemble` returns: `unattributed` in graphe.json, per name of a function or a method of ours, the calls whose verdict is `ambiguous`, `unknown`, `absent`, `attribute`, `member` or `external?`. `explain` (under "what calls it") and `callers` add "+ N calls named `f` the graph could not attribute: grep them"; SKILL.md says so.
- **Django**: `explain query.py::QuerySet.filter`: 3 callers, then "+ 2595 calls named `filter` ...".
- **Grid Zero** (snapshot to retake at the end of the batch): the key `unattributed` is new (`degager`: 1, `delester`: 1, ...).
