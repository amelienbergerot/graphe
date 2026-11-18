Status: closed
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0024: A document names a function written with its arguments

## What to build

BACKLOG.md (4cast): issue 48 writes `` `ndviRecent(geometrie, aujourdhui)` ``; the core's backticks take `name` and `name()` only, so `explain ndviRecent` names no issue (4 such citations in 4cast). Grid Zero's snapshot will move: the user decided to retake it once at the end of this batch (2026-11-18).

## Acceptance criteria

- [x] A document that names `` `f(a, b)` `` cites f.

## Comments

- The core's `NAMED` takes `f(a, b)` too, whatever is between the parentheses (no backtick). **4cast**: `explain ndviRecent` names issue 48.
- **Grid Zero** (snapshot to retake at the end of the batch): 37 `names` links more, from tickets that write a function with its arguments (`ticket_t_0013 -> simulation_grid_network_build_network`, ...).
