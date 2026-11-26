Status: closed
Part of: T-0048
Created: 2026-11-26

# T-0064: The Claude Code plugin

## What to build

A Claude Code user installs the skill from the public repository, its own marketplace (T-0053): `claude plugin install graphe --marketplace amelienbergerot/graphe` gives the skill `graphe:graphe`. The skill stays where it is; the author keeps the junction and the editable install.

## Acceptance criteria

- [ ] A plugin manifest (carrying the package's version) and a marketplace manifest (no version) at the root; the install command above works.
- [ ] The skill's frontmatter allows `Bash(graphe *)` and `PowerShell(graphe *)`; graphe never writes the user's settings.
- [ ] The shipped skill no longer says "note a gap" in a clone's backlog: when the graph falls short, grep; a gap in the tool, tell the user, who may report it on the repository's issues; the agent files none. The backlog rule moves to this repository's `AGENTS.md`.
- [ ] The skill drops the clone path to the readers doc, keeps its inline list of languages, and gives the public repository's URL once.
- [ ] Nothing in the skill's text ties it to Claude Code where a neutral wording costs nothing.

## Comments

- 2026-11-26: done on `integration/installable`, code-reviewed: the plugin and marketplace manifests (validated), `allowed-tools` in the skill, the backlog rule moved to AGENTS.md. Untested: the install from the public repository before the push.
