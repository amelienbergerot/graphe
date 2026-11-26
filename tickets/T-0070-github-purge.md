Status: ready-for-human
Created: 2026-11-27

# T-0070: GitHub's purge of the old commits

## What to build

The history rewrite (T-0056, T-0054) left the old commits, which carry the author's private address, unreachable but possibly still served by GitHub by their SHA. The author asked GitHub Support to purge them on 2026-11-26; moved here from T-0068 so the first release and its map could close.

## Acceptance criteria

- [ ] GitHub confirms the purge; an old SHA no longer opens on github.com.
- [ ] Then, if the old history is no longer wanted, the local backup `graphe-backup-2026-11-26.git` deleted (it holds the private address).
