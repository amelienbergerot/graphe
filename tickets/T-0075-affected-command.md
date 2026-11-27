Status: closed
Part of: T-0071
Blocked by: T-0074
Created: 2026-11-27

# T-0075: `graphe affected [REV]`, what a diff reaches

## What to build

What a change reaches takes one `callers` per function, listed by hand from the diff. `graphe affected` answers it in one query.

Without `REV`, the working tree against `HEAD`; with `REV`, against that revision. Each changed line range maps to the node whose extent holds it; a range outside any body counts for its file. A function the diff removes, no longer in the graph, is listed by its name, without callers. Then the callers of each touched node to `--depth`, 1 by default, printed as `callers` prints them, with its marks (`[by name]`, `?`, the unattributed calls of T-0074). The diff comes from git, as the files do.

## Acceptance criteria

- [x] An uncommitted change to a function lists that function and its callers.
- [x] `affected REV` compares with the revision: a branch's changes against its base.
- [x] `--depth 2` adds the callers' callers.
- [x] A change at a module's top level lists its file.
- [x] A removed function is listed by its name, apart.
- [x] No change prints that nothing is touched, exit 0.
- [x] `graphe --help`, the README and the skill name the command.

## Blocked by

- T-0074 (both change the answers' printing).

## Comments

- 2026-11-27: done. `cli.affected` reads `git diff -U0` against `git merge-base REV HEAD` (the working tree since it left REV, HEAD by default: a branch's changes, not what REV did since) plus the untracked files (`git ls-files --others`), new as a whole. Each added non-blank line maps to the innermost node whose extent holds it, else to its file; lines removed from a body map to the line before them; a whole definition removed maps to its class when it was indented, else to its file. A removed definition is seen by its keyword on a removed line (`cli.DEFINITION`) and listed when no node of the file bears its name any more; shortcut noted: Java's, C#'s and C's methods have no keyword and are not listed. The callers of each touched node print as `callers` prints them (`cli._callers`, shared); the nodes nothing calls are on one line. `callers` now marks a caller linked by name alone, `[by name]` on the level when every one is, `?` after it otherwise. After the review: a deleted file's definitions, a path with a space, Ruby's `def self.f`, Go's methods; a function moved to another file is not removed. Tests in `tests/test_host.py`. Found on the way: a module variable holding a multi-line string runs to the end of its file (BACKLOG.md, Open).
