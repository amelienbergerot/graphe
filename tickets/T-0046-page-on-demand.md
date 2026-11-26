Status: closed
Type: task
Created: 2026-11-23

# T-0046: The page on demand, `graphe view`

## What to build

`build` stops writing `graphe.html` and stops laying out the nodes: the layout was about half of a build (graphe on itself: assembly 0.69 s, communities 0.01 s, layout 0.78 s), paid by every hook for a page nobody asked for. `graphe.json` loses each node's `x` and `y`; the communities stay (`explain` and `REPORT.md` use them).

A new command, `graphe view [X]`, makes the page whenever the user asks, whatever the host's size: it rebuilds a stale graph first (as a query does), reads `graphe.json`, lays out the nodes with `layout()` as it is, writes `graphe/graphe.html` and opens it in the browser, on node X when given (`#<id>`, X designated as in `explain`). It rewrites the page each time; a page left from an earlier build stays (it shows its date and commit).

Decided with the user (grilling, 2026-11-23): the layout leaves the build; a subcommand rather than a `build` option; no size threshold, either to make the page or to refuse it; `view` reads `graphe.json` rather than assembling again; the positions stay those of the fixture `layout_01a698e.json`; no `--no-open`; the skill does not mention `view` (an agent has no use for the page); Grid Zero follows in this ticket.

## Acceptance criteria

- [x] `build` writes neither `graphe.html` nor `x`/`y`.
- [x] `graphe view` writes the page and opens it; `graphe view X` opens it on X; an unknown or ambiguous X answers as `explain` does.
- [x] The positions of the page are the fixture's (T-0017), and a community above 1000 nodes stays in its disc (T-0016), both tested through `view`.
- [x] `--help` and the README say it; the skill does not.
- [x] Grid Zero: its reference snapshot retaken without `x`/`y`, its `tools/README.md` corrected, in a commit of its own.
- [x] The tests pass.

## Comments

- **Done** (2026-11-23): `build()` no longer calls `layout()` nor writes the page; `view(graph, x)` reads `graphe.json` back through `load()` (which rebuilds a stale graph), lays it out by the `community` of each node and writes the page, then `webbrowser.open` on its `file://` address, `#<id>` with X (`_one`, as `explain`: 2 for an unknown or ambiguous X). The fixture's positions come out identical, as T-0381's order promised. The tests' `_run` replaces `webbrowser.open` by `print`, so `view` prints the address. Grid Zero (`comparer`): only `x` and `y` changed, on every node; the snapshot retaken, then identical; its build 3.3 s, `view Engine.step` 12 s with the rebuild.
