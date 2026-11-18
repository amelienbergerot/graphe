Status: ready-for-agent
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0026: A large repository's rebuild

## What to build

BACKLOG.md (Django): 2943 Python files, 48 s per build, and an edit not yet committed makes the graph stale: every query waits. User story 8 of T-0001 forbids answering from a stale graph. Measure the build without the profiler, take the speedups that keep the graph identical; if only an incremental build remains, the decision goes to the user.

## Acceptance criteria

- [ ] The build's breakdown on Django noted here, before and after.
- [ ] Django, Grid Zero, dpe and 4cast give the same graph.
