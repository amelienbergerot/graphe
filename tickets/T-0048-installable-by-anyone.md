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
- T-0055, the name: the command stays `graphe`, the distribution is `graphe-code`; the import name left to the packaging.
- T-0050, the licence: MIT, `Copyright (c) 2026 Amélien Bergerot`, a root `LICENSE` and PEP 639 fields; the dependencies are all permissive.
- T-0051, ADR 0001 revised: ADR 0004 replaces its install half (uv from PyPI for a user, editable for the author); local extensions stand, their contract now public, run in graphe's environment, a `graphe.toml` runs code (said in the README).
- T-0052, Python and the pins: `>=3.13` uncapped (3.12 lacks `full_match`); ranges in `pyproject.toml` (grammars capped at the next minor), exact versions in `uv.lock`; the layout reproducible per set of versions; CI locked on 3 OS × 3.13/newest, plus one newest-versions job.
- T-0053, shipping the skill: a plugin, the repository its own marketplace; `allowed-tools` in the skill, the lasting rule a README line; "note a gap" leaves the shipped skill for `AGENTS.md`; the author keeps the junction; one version for skill and CLI.
- T-0056, what going public publishes: Grid Zero and 4cast stay named, their extensions private; the history rewritten for the author alone (GitHub noreply), the cited hashes and the layout fixture renamed after it, as T-0054's first steps; the GitHub repository goes public, by the user, when the effort is done.

## Not yet specified

- A stranger's first contact: the README, a minimal `graphe.toml`, what happens on a repository without one; one line on the `graphe` command of `graphe-cli` (T-0055); one line that a `graphe.toml` runs code (T-0051); the plugin install, the `permissions.allow` line, the copy for other agents (T-0053). Waits on the package (T-0057), and the release (T-0058).

## Out of scope

- The readers' precision (the rest of BACKLOG.md), the incremental build (Django), the keyed links of the frameworks: features, not the install.
- The other agents' integration: the door stays open (Notes), the work is another effort.
