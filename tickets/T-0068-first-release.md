Status: ready-for-human
Part of: T-0048
Blocked by: T-0060, T-0065, T-0066, T-0067
Created: 2026-11-26

# T-0068: The first release, 0.1.0

## What to build

graphe installable by anyone: the destination of T-0048. The author's steps, which only the author can take.

## Acceptance criteria

- [ ] On PyPI, a pending Trusted Publisher for `graphe-code`: the repository, the release workflow, its environment if any.
- [ ] The tag `v0.1.0` pushed; the workflow green; `graphe-code 0.1.0` on PyPI, the GitHub release made.
- [ ] On a machine (or a fresh account) without graphe: `uv tool install graphe-code`, then `graphe build` and `graphe explain` in a git repository; the plugin installed and the skill loaded in Claude Code.
- [ ] GitHub's purge of the old, unreachable commits confirmed (asked on 2026-11-26).
