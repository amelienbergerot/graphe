Status: closed
Part of: T-0048
Blocked by: T-0061
Created: 2026-11-26

# T-0065: An expected error on one line

## What to build

A stranger who runs graphe outside a git repository, or with an extension not found, reads one line, not a traceback (T-0059): an expected error prints `graphe: <message>` and exits 1; a real bug keeps its traceback.

## Acceptance criteria

- [ ] Outside a git repository, a query prints one line naming the folder and that graphe reads the files git tracks; exit 1; no traceback. Tested at the command's seam.
- [ ] An extension not found, or without `contribute(project)`, likewise.
- [ ] Any other exception still shows its traceback.

## Comments

- 2026-11-26: done on `integration/installable`, code-reviewed: a `RuntimeError` prints `graphe: <message>`, exit 1; other errors keep their traceback.
