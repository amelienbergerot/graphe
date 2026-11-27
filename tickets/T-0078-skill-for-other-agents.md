Status: closed
Part of: T-0071
Blocked by: T-0077
Created: 2026-11-27

# T-0078: The skill for Codex, Cursor, Copilot and Gemini CLI

## What to build

The skill reaches Claude Code alone; another agent's user is told to copy a folder (BACKLOG.md, "The skill reaches Claude Code alone, and only for the questions it names.").

For Codex, Cursor, Copilot and Gemini CLI: where the agent has a plugin or skill format, a manifest beside Claude Code's, carrying the same skill text; otherwise a README line saying where to copy the skill's folder. The skill's text is kept free of anything Claude Code alone understands (T-0048, T-0049's precedent). The README marks each agent "untested, reports welcome in the issues", until users report back. The hook of T-0077 stays Claude Code's.

Each agent's format is checked against its own documentation when the ticket is worked, and the source cited in the ticket's comments.

## Acceptance criteria

- [x] Each of the four agents has a manifest or a README line, from its documentation.
- [x] Every manifest carries the package's version; a test checks it, as for Claude Code's plugin.
- [x] One skill text serves every agent.
- [x] The README names each agent as untested, and where to report.
- [x] BACKLOG.md's entry says what is settled and what waits on users' reports.

## Blocked by

- T-0077 (both edit the plugin and the README).

## Comments

- 2026-11-27: done. One skill text (`skills/graphe/`) for every agent; its `allowed-tools` is a field of the Agent Skills format (https://agentskills.io), not Claude Code's alone. Each format, from its documentation:
  - Codex: a root `plugin.json` with the Agent Plugins `$schema` (https://agent-plugins.org/schemas/1.0.0/plugin.schema.json) discovers `skills/` without a `skills` field; `version`, `description` and `author.name` are required for Codex (https://developers.openai.com/plugins/build/plugins, https://developers.openai.com/plugins/deploy/submission). The CLI adds a marketplace with `codex plugin marketplace add owner/repo`; the repository's is `.agents/plugins/marketplace.json`, an entry `{"source": "local", "path": "./..."}` with `policy.installation`, `policy.authentication` and `category`. A path at the marketplace's own root (`./`) has no example there. Hooks load only for plugins installed by hand in Codex desktop.
  - GitHub Copilot CLI: a root `plugin.json` that targets Agent Plugins takes precedence over `.claude-plugin/plugin.json`; skills are the subfolders of `skills/`; in that format a root `hooks/hooks.json` is not read; `copilot plugin install OWNER/REPO` (https://docs.github.com/en/copilot/reference/cli-plugin-reference, https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-cli-plugins).
  - Cursor: "A plugin that conforms to the Agent Plugins specification loads in Cursor"; a local plugin goes in `~/.cursor/plugins/local/<plugin>`; personal skills in `~/.cursor/skills/` or `~/.agents/skills/` (https://cursor.com/docs/plugins, https://cursor.com/docs/reference/plugins, https://cursor.com/docs/context/skills). The GitHub import needs `.cursor-plugin/marketplace.json`, whose sources are subfolders holding `.cursor-plugin/plugin.json`; a source at the root is undocumented: left out, the README gives the local clone and the skills folder. Cursor reads `hooks/hooks.json` by default, under its own event names (`preToolUse`), not `PreToolUse`.
  - Gemini CLI: `gemini-extension.json` at the root (`name`, `version`, `description`), `skills/<name>/SKILL.md` exposed, `gemini extensions install <GitHub URL>` (https://geminicli.com/docs/extensions/reference/, https://geminicli.com/docs/cli/skills/). It reads `hooks/hooks.json` by default, under its own event names. Every page carries "Gemini CLI was replaced by Antigravity CLI on June 18th, 2026": noted in the README.
  - `.github/check_release.py` compares the tag with pyproject.toml and the three manifests (`MANIFESTS`); the Codex marketplace carries no version. None tried in a live session of these agents: the README marks each untested.
