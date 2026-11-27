Status: closed
Created: 2026-11-27

# T-0070: GitHub's purge of the old commits

## What to build

The history rewrite (T-0056, T-0054) left the old commits, which carry the author's private address, unreachable but possibly still served by GitHub by their SHA. The author asked GitHub Support to purge them on 2026-11-26; moved here from T-0068 so the first release and its map could close.

## Acceptance criteria

- [ ] GitHub confirms the purge; an old SHA no longer opens on github.com.
- [ ] Then, if the old history is no longer wanted, the local backup `graphe-backup-2026-11-26.git` deleted (it holds the private address).

## Comments

- 2026-11-27: closed by the author's choice, **the purge still pending**: GitHub still serves old commits by their SHA (7 of 8 rewritten SHAs probed answer on the public API; `0a4d70ff` carries the private address). The request to GitHub Support (2026-11-26) is followed outside the tickets. The backup `graphe-backup-2026-11-26.git` kept for now.
