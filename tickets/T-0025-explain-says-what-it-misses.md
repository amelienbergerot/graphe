Status: ready-for-agent
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0025: `explain` says the calls it could not attribute

## What to build

BACKLOG.md (Django): `explain query.py::QuerySet.filter` gives 3 callers, grep hundreds of `.filter(`: a receiver of unknown type (`Model.objects.filter`). The build keeps, per name, the number of call sites no reader attributed; `explain` shows "N calls named `filter` not attributed: grep" so that the agent knows when to grep.

## Acceptance criteria

- [ ] `explain` of a method called on an unknown receiver says how many calls of its name are not attributed.
- [ ] SKILL.md says what the line means.
