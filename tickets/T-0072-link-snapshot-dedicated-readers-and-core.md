Status: closed
Part of: T-0071
Created: 2026-11-27

# T-0072: A snapshot of the links, for the dedicated readers and the core

## What to build

Nothing protects the links already resolved: the tests check chosen links, the sample hosts are measures taken by hand. This ticket sets the mechanism and covers the dedicated readers and the core.

For Python, JS/TS/Svelte, GDScript and PHP, one small sample host each, built as a real host is. One more for the core: a document citing code between backticks and another document by its identifier, a `graphe.toml` with `[keys]` and `displayed_text`. Each host's links are written one per line, sorted: source, relation, target, sure or by name. A test compares the built links with the committed snapshot. A script rewrites every snapshot, so that a deliberate change costs one command and a reviewed diff.

## Acceptance criteria

- [x] Each of the five sample hosts has a committed snapshot of all its links, and the test passes on them.
- [x] A link removed or turned from sure to by-name makes the test fail, naming the host and the line.
- [x] The script rewrites the snapshots, and running it twice changes nothing.
- [x] The sample hosts hold each reader's main kinds of link (calls, imports or references, reads, cites, names, sends), not one each only.
- [x] The way to accept a change (run the script, give the reason in the commit) is written where a contributor reads it (`docs/contribution.md`).

## Blocked by

None (can start immediately).

## Comments

- 2026-11-27: five sample hosts in `tests/fixtures/` (python, js with TS and Svelte, godot, php, core), each with its `.links` snapshot; `tests/snapshots.py` rewrites them, `tests/test_snapshots.py` compares them and fails on a snapshot left without its host. The snapshots hold 16 relations (calls sure and by name, imports, references, uses, reads, writes, inherits, emits, connects, dispatches, cites, names, sends, value). Left out, a `shortcut:` in the script: a link's locations and contexts; and `displayed_text`, which makes no link. A ticket naming `` `say()` `` names nothing (shorter than NAME_MIN), kept as such. graphe's own `graphe.toml` excludes the sample hosts from its graph. 105 tests pass.
