# Issue tracker: local Markdown tickets

This repository's tickets are Markdown files in `tickets/` at the root. No remote tracker, no GitHub Issues. The graph reads these files as documents: a ticket cites another by its identifier.

## Conventions

- One file per ticket: `tickets/T-NNNN-short-title.md` (four digits, then the title in kebab-case, as in Grid Zero).
- The identifier is `T-NNNN` (pattern `T-\d{4}`, the one the graph's documents recognise). To cite a ticket, write its identifier, for example `T-0012`.
- Next number: the largest number present in `tickets/`, plus one. Create the folder if it does not exist.
- A spec is a ticket like any other. Its implementation tickets cite it by a `Part of: T-NNNN` line at the top.
- The triage state is a `Status:` line at the top of the file (values in `triage-labels.md`).
- Exchanges are appended at the bottom of the file, under a `## Comments` heading.
- Closing: add a last comment, then set `Status:` to `closed`.

## When a skill says "publish to the issue tracker"

Create `tickets/T-NNNN-short-title.md` with the next number.

## When a skill says "fetch the relevant ticket"

Read `tickets/T-NNNN-*.md`. The user normally gives the identifier or the path.

## Wayfinding operations

Used by `/wayfinder`. The map and its children are all tickets in `tickets/`.

- **Map**: a `Type: map` ticket, with the sections Notes / Decisions-so-far / Fog.
- **Child ticket**: a ticket with `Part of: T-<map>` and `Type:` (`research`/`prototype`/`grilling`/`task`), the question in the body. `Status:` moves to `claimed`, then `resolved`.
- **Blocking**: a `Blocked by: T-NNNN, T-NNNN` line at the top. The ticket is unblocked when each listed ticket is `resolved`.
- **Frontier**: the map's children still open, unblocked and unclaimed. The smallest number goes first.
- **Claim**: `Status: claimed`, recorded before any work.
- **Resolve**: the answer under `## Answer`, `Status: resolved`, then a pointer (summary + identifier) in the map's Decisions-so-far.
