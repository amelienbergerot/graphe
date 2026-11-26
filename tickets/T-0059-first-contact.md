Status: resolved
Type: grilling
Part of: T-0048
Created: 2026-11-26

# T-0059: A stranger's first contact

## Question

What a developer who has never seen graphe reads and runs, from the README to a first graph: the README's order and content (`uv tool install graphe-code`, the plugin `claude plugin install graphe --marketplace <owner>/graphe`, the `permissions.allow` line, the copy of `skills/graphe/` for other agents, T-0053); a minimal `graphe.toml`, and what `graphe build` does on a repository without one; the one-line warnings (the `graphe` command of `graphe-cli`, T-0055; a `graphe.toml` runs code, T-0051); what of today's README is the author's own (the editable install, the junction, ADR 0004) and moves to a contributor section.

## Answer

Decided with the user (grilling, 2026-11-26). The facts found: without `graphe.toml`, `graphe build` works (every file git tracks, no extension, no displayed text, no key); outside a git repository, a first query prints "rebuilding" then a full Python traceback ending in `RuntimeError: … is not a git repository: graphe reads the files git tracks`; the README's Why, example, How it works, Readers and Tested on already serve a stranger, its Install is the author's (`-e .`, `--python 3.14`, a PowerShell junction, gaps in BACKLOG.md).

- **The README's order**: Why, the example, **What it reads**, **Install**, **First graph**, How it works, Readers, Tested on, then **Developing graphe** last (the editable install, the junction, BACKLOG.md, ADR 0004).
- **What it reads**, a short table after the example (asked by the user): read through imports and types (sure links) — Python, JavaScript, TypeScript, Svelte (script and markup), GDScript (Godot); read by name (the generic tree-sitter reader, `[by name]` links) — Go, Rust, Java, Kotlin, C, C++, C#, Ruby, Swift, PHP; documents — Markdown, tickets and what they cite; frameworks — none specific, a front-to-back link (a route) through the generic `[keys]`; a "not read" line (`.jsx`/`.tsx`, Vue). The per-language detail stays in `docs/readers.md`, linked.
- **Install**, the same commands on the three OS: `uv tool install graphe-code` (uv fetches Python), one line that uv refuses without `--force` when `graphe-cli`'s `graphe` is there; `claude plugin install graphe --marketplace amelienbergerot/graphe`; the `permissions.allow` line (`Bash(graphe:*)`, `PowerShell(graphe *)`); for other agents, copy `skills/graphe/` where the agent reads skills.
- **First graph**: `cd` into a git repository, `graphe install` (the hooks), `graphe explain <a function>`. `graphe.toml` is said optional, with a short commented example (`exclude`, `displayed_text`, `[keys]`) linking to `docs/contribution.md`. No `graphe init`.
- **The code warning**, one line in How it works item 4: a `graphe.toml` declaring extensions runs their code at every build, git hooks included; build a cloned repository only if you trust it.
- **Gaps** go to the GitHub issues; BACKLOG.md, naming the host, is the author's (Developing graphe).
- **An expected error prints one line**: a `RuntimeError` (not a git repository, an extension not found…) is shown as `graphe: <message>`, no traceback, exit 1; a real bug keeps its traceback.

## Comments

- 2026-11-26: resolved.
