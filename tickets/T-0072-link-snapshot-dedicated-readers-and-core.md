Status: ready-for-agent
Part of: T-0071
Created: 2026-11-27

# T-0072: A snapshot of the links, for the dedicated readers and the core

## What to build

Nothing protects the links already resolved: the tests check chosen links, the sample hosts are measures taken by hand. This ticket sets the mechanism and covers the dedicated readers and the core.

For Python, JS/TS/Svelte, GDScript and PHP, one small sample host each, built as a real host is. One more for the core: a document citing code between backticks and another document by its identifier, a `graphe.toml` with `[keys]` and `displayed_text`. Each host's links are written one per line, sorted: source, relation, target, sure or by name. A test compares the built links with the committed snapshot. A script rewrites every snapshot, so that a deliberate change costs one command and a reviewed diff.

## Acceptance criteria

- [ ] Each of the five sample hosts has a committed snapshot of all its links, and the test passes on them.
- [ ] A link removed or turned from sure to by-name makes the test fail, naming the host and the line.
- [ ] The script rewrites the snapshots, and running it twice changes nothing.
- [ ] The sample hosts hold each reader's main kinds of link (calls, imports or references, reads, cites, names, sends), not one each only.
- [ ] The way to accept a change (run the script, give the reason in the commit) is written where a contributor reads it (`docs/contribution.md`).

## Blocked by

None (can start immediately).
