Status: ready-for-agent
Part of: T-0071
Blocked by: T-0075, T-0082
Created: 2026-11-27

# T-0077: A Claude Code hook that points a grep to the graph

## What to build

The skill's description is the only thing that brings the agent to the graph: an agent that greps a name the graph knows is never told.

A new command, `graphe hook`, reads Claude Code's PreToolUse JSON on stdin and writes the hook's JSON answer on stdout. It answers only for the Grep tool and for `grep`/`rg` run through Bash or PowerShell, and only when the pattern is a name a node bears: one line of added context naming `graphe explain` on it. It never blocks the tool (fail-open), never rebuilds the graph (a stale graph is read as it is), and is silent without a graph, on any error, or for any other tool. No cap on the hints at first. The plugin declares the hook.

The JSON's shape and the way a plugin declares a hook are checked against Claude Code's documentation, not assumed.

## Acceptance criteria

- [ ] A Grep for a function's name gets one added line naming `graphe explain <name>`.
- [ ] `grep -rn name` and `rg name` through Bash or PowerShell get the same line.
- [ ] A pattern that is no node's name, another tool, a repository without a graph, malformed input: no output, exit 0.
- [ ] The hook never blocks the tool, and a stale graph is not rebuilt.
- [ ] Installing the plugin installs the hook; the README says what it does and how to turn it off.

## Blocked by

- T-0075 (both add a command to the CLI).
- T-0082 (both edit the README).
