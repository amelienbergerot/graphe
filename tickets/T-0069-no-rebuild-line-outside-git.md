Status: closed
Created: 2026-11-27

# T-0069: Outside a git repository, the error alone

## What to build

Outside a git repository, `graphe explain` printed "(the graph is older than the code or the tool: rebuilding)" before the one-line error T-0065 gives: a stranger reads that graphe was rebuilding something that never existed (seen on 0.1.0 in a clean container, T-0068). The error is the only line.

## Acceptance criteria

- [x] Outside a git repository, a query prints `graphe: <folder> is not a git repository: ...` and nothing else on stderr; exit 1.
- [x] In a git repository, a stale or missing graph is still rebuilt with its line.

## Comments

- 2026-11-27: `load()` now lists the sources (git) before deciding to rebuild, so outside a repository the error comes first and alone. T-0065's test asserted the old order; it now asserts a single stderr line. 98 tests pass.
