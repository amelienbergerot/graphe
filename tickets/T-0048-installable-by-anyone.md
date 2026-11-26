Status: open
Type: map
Created: 2026-11-26

# T-0048: graphe installable by anyone (wayfinder map)

## Destination

A spec, ready for `/to-spec` then `/to-tickets`: any developer, on Windows, macOS or Linux, installs and uses `graphe`, the command and its Claude Code skill, from a public repository. ADR 0001 revised is among its decisions.

## Notes

- Chosen with the user (grilling, 2026-11-26): any developer, not only trusted people; the repository goes public, with a licence; the command and the skill ship together; the three OS from the start, checked on a CI rather than promised.
- Claude Code alone for this map, the door open to the other agents (Codex, Cursor, Copilot, `AGENTS.md`): a decision here never ties the command, or the skill's text, to Claude Code where a neutral form costs nothing; what is Claude Code's own (a plugin, `permissions.allow`) stays apart from it.
- The facts the code gives (2026-11-26): the git hooks are `/bin/sh`, the page opens through `webbrowser`, the core holds no path of this machine. What is this machine's: the editable install from a clone, the skill's PowerShell junction, the `permissions.allow` rules by hand, Python `==3.14.*` and every dependency pinned (Grid Zero's layout fixture), seven top-level modules.
- Each ticket: `/grilling` and `/domain-modeling` (GLOSSARY.md, docs/adr/), `/research` for a research ticket.

## Decisions so far

- T-0049, the distribution channel: `graphe` taken on PyPI and as a command (`graphe-cli`); uv the smoother channel (it fetches the Python); a plugin ships the skill, not the CLI nor the permission rules.

## Not yet specified

- The packaging: a `src/graphe/` package in place of the seven top-level modules (`graphe_core` and the others would collide in a user's environment).
- The version number and the release process.
- A stranger's first contact: the README, a minimal `graphe.toml`, what happens on a repository without one.
- The local extensions of Grid Zero and 4cast: public examples, or kept private.

## Out of scope

- The readers' precision (the rest of BACKLOG.md), the incremental build (Django), the keyed links of the frameworks: features, not the install.
- The other agents' integration: the door stays open (Notes), the work is another effort.
