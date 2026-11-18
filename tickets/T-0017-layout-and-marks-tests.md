Status: ready-for-agent
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0017: Automated tests for the layout and the by-name marks

## What to build

T-0016 checked by hand that the layout keeps the positions of the tool of 7681fac, and left untested the sunflower above 1000 nodes and the mixed `[N by name: ?]` marks of `explain`. Tests at the `graphe` command's seam (the user's choice, 2026-11-18).

## Acceptance criteria

- [ ] A generated sample host of many files of varied sizes (many communities) keeps the positions the tool of 7681fac gave it, captured once as a fixture.
- [ ] A community above 1000 nodes builds, its positions finite, distinct and inside its disc.
- [ ] A relation with a sure link and a guessed one shows `[1 by name: ?]` and the `?` on the guessed one only.
