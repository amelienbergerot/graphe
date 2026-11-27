Status: ready-for-agent
Part of: T-0071
Blocked by: T-0074
Created: 2026-11-27

# T-0075: `graphe affected [REV]`, what a diff reaches

## What to build

What a change reaches takes one `callers` per function, listed by hand from the diff. `graphe affected` answers it in one query.

Without `REV`, the working tree against `HEAD`; with `REV`, against that revision. Each changed line range maps to the node whose extent holds it; a range outside any body counts for its file. A function the diff removes, no longer in the graph, is listed by its name, without callers. Then the callers of each touched node to `--depth`, 1 by default, printed as `callers` prints them, with its marks (`[by name]`, `?`, the unattributed calls of T-0074). The diff comes from git, as the files do.

## Acceptance criteria

- [ ] An uncommitted change to a function lists that function and its callers.
- [ ] `affected REV` compares with the revision: a branch's changes against its base.
- [ ] `--depth 2` adds the callers' callers.
- [ ] A change at a module's top level lists its file.
- [ ] A removed function is listed by its name, apart.
- [ ] No change prints that nothing is touched, exit 0.
- [ ] `graphe --help`, the README and the skill name the command.

## Blocked by

- T-0074 (both change the answers' printing).
