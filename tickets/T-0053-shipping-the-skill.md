Status: resolved
Type: grilling
Part of: T-0048
Blocked by: T-0049
Created: 2026-11-26

# T-0053: Shipping the skill

## Question

How does a user get the skill and its permission rules: a Claude Code plugin, a `graphe skill install` command, a documented copy? Today a junction to the clone. The skill's text kept neutral enough for another agent (map Notes).

## Answer

Grilling with the user, 2026-11-26 (facts from T-0049).

- **The channel: a Claude Code plugin, the repository its own marketplace** (as Mergify): `.claude-plugin/plugin.json` and `marketplace.json` at the root, the skill stays in `skills/graphe/`; `claude plugin install graphe --marketplace <owner>/graphe`. The skill becomes `graphe:graphe`. Other agents: one README line, copy `skills/graphe/` where the agent reads skills (the Agent Skills standard). No `graphe skill install` command: it would tie the CLI to Claude Code.
- **The permission rules**: the skill's frontmatter carries `allowed-tools: Bash(graphe *) PowerShell(graphe *)` (the turn that loads it); the lasting `permissions.allow` rule stays one README line the user adds. graphe never writes the user's settings.
- **"Note a gap" leaves the shipped skill**: it points at a clone (`<graphe>/BACKLOG.md`, a commit there) a uv user does not have. The shipped skill says: when the graph falls short, grep; a gap in the tool, tell the user, who may report it on the public repository's issues. The agent never files an issue itself.
- **The author's setup**: the junction and the editable install (ADR 0004), never the plugin (cached, it would lag the clone; with the junction, two copies). The backlog rule moves to this repository's `AGENTS.md`, with a short pointer in the author's own `~/.claude/CLAUDE.md` for sessions in a host.
- **The readers list**: the skill drops the `<graphe>/docs/readers.md` path and keeps its inline list of languages; the public repository's URL added once it exists.
- **Skill and CLI**: one version number for both, the plugin's `version` set with the package's at each release; the mechanics belong to the release process (map fog).
