Status: resolved
Type: research
Part of: T-0048
Created: 2026-11-26

# T-0049: The distribution channel, the facts

## Question

Is `graphe` free on PyPI (and close names)? How do `uv tool install` and `pipx` install a command from PyPI and from a git URL, on the three OS, and with which Python? How does a Claude Code plugin work: can it ship a skill, permission rules (`Bash(graphe:*)`), and does it install the command or only point at it? How do other tools that pair a CLI with a Claude Code skill ship today? Primary sources only.

## Answer

Findings: `docs/research/distribution-channel.md` on the branch `research/distribution-channel` (09a129d, not merged).

- **PyPI name**: `graphe` is taken (an unrelated graph-algorithms package, its module also `graphe`; PEP 541 gives no way to reclaim it). `graphe-cli` (May 2026) installs a `graphe` command: a clash on the command whatever the distribution name; uv refuses to overwrite a command it did not install without `--force`. Free: `graphe-code`, `code-graphe`, `pygraphe`, `graph-e`.
- **uv**: `uv tool install <dist>` or `git+https://...`, isolated, the command in `~/.local/bin`; it picks a Python matching `requires-python` and downloads a missing one (3.14 builds on the three OS). The smoother channel.
- **pipx**: matches `requires-python` but never downloads a Python by default: with `==3.14.*` and no 3.14, it fails unless `--fetch-python missing`.
- **Claude Code plugin**: ships the skill (named `graphe:graphe`) and hooks; no manifest key for permission rules, `allowed-tools` lasts one turn: `permissions.allow` stays the user's. Its `bin/` reaches Claude's shell only, not the terminal nor git hooks: a plugin points at the CLI, it does not install it. One repository can be the plugin and its own marketplace.
- **Examples** (Mergify, Preset, Sentry): none installs its CLI from the plugin; the CLI from PyPI, the plugin beside it (Preset's carries Codex and Cursor manifests too).
- **Uncertain**: uv downloading 3.14 not seen; 3.14 wheels checked for 5 of 15 dependencies; `bin/` under Windows PowerShell untested; `@tag` on `uv tool install git+` documented for `uvx --from` only.
