Status: ready-for-human
Part of: T-0048
Blocked by: T-0060, T-0065, T-0066, T-0067
Created: 2026-11-26

# T-0068: The first release, 0.1.0

## What to build

graphe installable by anyone: the destination of T-0048. The author's steps, which only the author can take.

## Acceptance criteria

- [x] On PyPI, a pending Trusted Publisher for `graphe-code`: the repository, the release workflow, its environment if any.
- [x] The tag `v0.1.0` pushed; the workflow green; `graphe-code 0.1.0` on PyPI, the GitHub release made.
- [x] On a machine (or a fresh account) without graphe: `uv tool install graphe-code`, then `graphe build` and `graphe explain` in a git repository; the plugin installed and the skill loaded in Claude Code.
- [ ] GitHub's purge of the old, unreachable commits confirmed (asked on 2026-11-26).

## Comments

- 2026-11-27: the tag `v0.1.0` (7600e53) pushed; release run 45910794675 green (version, build, pypi, release). `graphe-code 0.1.0` on PyPI (wheel and sdist, licence MIT); the GitHub release https://github.com/amelienbergerot/graphe/releases/tag/v0.1.0. In a clean Linux container (`ghcr.io/astral-sh/uv:python3.13-bookworm`): `uv tool install graphe-code` from PyPI, then `graphe build` and `graphe explain greet` in a fresh git repository answer; outside a repository, one line, exit 1. Left for the author: the plugin installed and the skill loaded in Claude Code, on a machine without the junction; GitHub's purge.
- 2026-11-27: the author installed the plugin on another machine; the skill `graphe:graphe` loaded in Claude Code. Left: GitHub's purge.
