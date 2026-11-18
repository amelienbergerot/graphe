Status: closed
Type: task
Part of: T-0001
Blocked by: T-0011
Created: 2026-11-17

# T-0013: The Claude Code skill

## What to build

A Claude Code skill, shipped in this repository and installed once for the account. It teaches the tool to the agent in every project: when to prefer the graph to grep, how to designate a node (id, name, `Class.method`, `file::name`), which queries exist, and where to note a gap (the tool's backlog, `BACKLOG.md`, naming the host). It replaces Grid Zero's two "graphe" memories.

## Acceptance criteria

- [x] The skill is installed and triggers in a repository other than Grid Zero, when the agent looks for code.
- [x] Grid Zero's two "graphe" memories are removed, and their useful content is in the skill.
- [x] The repository documents how to install it.

## Comments

**2026-11-18, done.** The skill is `skills/graphe/SKILL.md`, installed for the account by a junction `~/.claude/skills/graphe` -> `E:/dev/graphe/skills/graphe` (a fix here serves at once, like `uv tool install -e`). `README.md` documents both installs.

- Trigger: a headless `claude -p "Who calls the function install in this repo?"` in this repository (not Grid Zero) invoked the `graphe` skill first, then `graphe callers install --depth 1`, and answered `main()` without grep. Without an allow rule the command waits for approval, and the headless run fell back to grep: the README gives the `Bash(graphe:*)` / `PowerShell(graphe *)` rule.
- Grid Zero's memories (`~/.claude/projects/E--dev-grid-zero/memory/`, outside git): `feedback_graphe_avant_grep.md` and `feedback_noter_les_manques_du_graphe.md` deleted, their two lines removed from `MEMORY.md`; `project_graphe_outil_autonome.md` now points to the skill. Their Grid Zero-only content (the Python 3.14 path, the `ambiguous` of `pilote/humain.py`) stays out of the skill.
