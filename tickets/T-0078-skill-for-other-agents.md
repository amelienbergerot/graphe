Status: ready-for-agent
Part of: T-0071
Blocked by: T-0077
Created: 2026-11-27

# T-0078: The skill for Codex, Cursor, Copilot and Gemini CLI

## What to build

The skill reaches Claude Code alone; another agent's user is told to copy a folder (BACKLOG.md, "The skill reaches Claude Code alone, and only for the questions it names.").

For Codex, Cursor, Copilot and Gemini CLI: where the agent has a plugin or skill format, a manifest beside Claude Code's, carrying the same skill text; otherwise a README line saying where to copy the skill's folder. The skill's text is kept free of anything Claude Code alone understands (T-0048, T-0049's precedent). The README marks each agent "untested, reports welcome in the issues", until users report back. The hook of T-0077 stays Claude Code's.

Each agent's format is checked against its own documentation when the ticket is worked, and the source cited in the ticket's comments.

## Acceptance criteria

- [ ] Each of the four agents has a manifest or a README line, from its documentation.
- [ ] Every manifest carries the package's version; a test checks it, as for Claude Code's plugin.
- [ ] One skill text serves every agent.
- [ ] The README names each agent as untested, and where to report.
- [ ] BACKLOG.md's entry says what is settled and what waits on users' reports.

## Blocked by

- T-0077 (both edit the plugin and the README).
