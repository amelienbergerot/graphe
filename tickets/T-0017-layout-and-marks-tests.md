Status: closed
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0017: Automated tests for the layout and the by-name marks

## What to build

T-0016 checked by hand that the layout keeps the positions of the tool of 7681fac, and left untested the sunflower above 1000 nodes and the mixed `[N by name: ?]` marks of `explain`. Tests at the `graphe` command's seam (the user's choice, 2026-11-18).

## Acceptance criteria

- [x] A generated sample host of many files of varied sizes (many communities) keeps the positions the tool of 7681fac gave it, captured once as a fixture.
- [x] A community above 1000 nodes builds, its positions finite, distinct and inside its disc.
- [x] A relation with a sure link and a guessed one shows `[1 by name: ?]` and the `?` on the guessed one only.

## Comments

- `tests/test_host.py`: 40 files of 1 to 40 chained functions give 40 communities (860 nodes); their positions, captured once by the tool of 7681fac (`tests/layout_7681fac.json`), are those of today's build. Checked that it bites: steps taken for blocked forever too early (`smallest + 6.0`) fail it.
- A star of 1101 functions makes a community of 1102 nodes: its positions are finite, distinct, inside its disc (the radius `graphe.html` draws).
- `explain f` with `g()` sure and `x.m()` guessed: `calls (2) [1 by name: ?]`, then `outils.py: A.m:2?, g:6`.
