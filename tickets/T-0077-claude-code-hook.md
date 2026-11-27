Status: closed
Part of: T-0071
Blocked by: T-0075, T-0082
Created: 2026-11-27

# T-0077: A Claude Code hook that points a grep to the graph

## What to build

The skill's description is the only thing that brings the agent to the graph: an agent that greps a name the graph knows is never told.

A new command, `graphe hook`, reads Claude Code's PreToolUse JSON on stdin and writes the hook's JSON answer on stdout. It answers only for the Grep tool and for `grep`/`rg` run through Bash or PowerShell, and only when the pattern is a name a node bears: one line of added context naming `graphe explain` on it. It never blocks the tool (fail-open), never rebuilds the graph (a stale graph is read as it is), and is silent without a graph, on any error, or for any other tool. No cap on the hints at first. The plugin declares the hook.

The JSON's shape and the way a plugin declares a hook are checked against Claude Code's documentation, not assumed.

## Acceptance criteria

- [x] A Grep for a function's name gets one added line naming `graphe explain <name>`.
- [x] `grep -rn name` and `rg name` through Bash or PowerShell get the same line.
- [x] A pattern that is no node's name, another tool, a repository without a graph, malformed input: no output, exit 0.
- [x] The hook never blocks the tool, and a stale graph is not rebuilt.
- [x] Installing the plugin installs the hook; the README says what it does and how to turn it off.

## Blocked by

- T-0075 (both add a command to the CLI).
- T-0082 (both edit the README).

## Comments

- 2026-11-27: done. `graphe hook` (cli.py) reads the PreToolUse input on stdin and, for Grep's `pattern` or the first `grep`/`rg` of a Bash or PowerShell `command` (`-e`'s value, else the first operand, the values of the options that take one skipped), strips `def`/`function`..., `\b` and a trailing `(`, then answers `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "..."}}` when the name is one find() designates a node by (a document's suffix `md` aside). No `permissionDecision`: the user's permission rules stay in force. It reads graphe.json itself, never `load()` (which rebuilds a missing graph or one of before T-0074), in the repository of the input's `cwd`; every error is silent with exit 0. The plugin declares it in `hooks/hooks.json` (matcher `Grep|Bash|PowerShell`, timeout 10 s). Checked against https://code.claude.com/docs/en/hooks ("PreToolUse decision control": `additionalContext` is added beside the tool result; exit 0 with no output is no decision) and https://code.claude.com/docs/en/plugins-reference (`hooks/hooks.json`, its top-level `hooks` wrapper); turning it off, from https://code.claude.com/docs/en/discover-plugins (`claude plugin disable`) and the hooks page (`disableAllHooks`): no switch for one plugin hook. About 0.5 s per Bash call on Windows (the CLI's imports); a command that is no grep stops before any git call. Not tried in a live Claude Code session. The `shortcut:` in `_grep_pattern`: the first grep only, a value glued to its option, PowerShell split by POSIX rules.
- 2026-11-27, after the review: the plugin declares `graphe hook; exit 0`. graphe 0.1.1 (PyPI) answers an unknown command with exit 2, which Claude Code reads as a block of the tool: an updated plugin over an old command would have denied every Grep, Bash and PowerShell call. `; exit 0` holds in Git Bash and in PowerShell, the shells a shell-form hook runs in (hooks page, "Exec form and shell form"); a missing `graphe` is silent too.
