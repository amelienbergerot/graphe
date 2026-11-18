Status: ready-for-agent
Type: task
Part of: T-0001
Blocked by: T-0011
Created: 2026-11-17

# T-0013: The Claude Code skill

## What to build

A Claude Code skill, shipped in this repository and installed once for the account. It teaches the tool to the agent in every project: when to prefer the graph to grep, how to designate a node (id, name, `Class.method`, `file::name`), which queries exist, and where to note a gap (the tool's backlog, `BACKLOG.md`, naming the host). It replaces Grid Zero's two "graphe" memories.

## Acceptance criteria

- [ ] The skill is installed and triggers in a repository other than Grid Zero, when the agent looks for code.
- [ ] Grid Zero's two "graphe" memories are removed, and their useful content is in the skill.
- [ ] The repository documents how to install it.
