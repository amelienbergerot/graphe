Status: closed
Part of: T-0048
Blocked by: T-0061, T-0064
Created: 2026-11-26

# T-0066: The README for a stranger

## What to build

A developer who has never seen graphe goes from the README to a first graph on Windows, macOS or Linux (T-0059), and an extension author knows what the contract promises (T-0051, ADR 0004).

## Acceptance criteria

- [ ] The order: Why, the example, What it reads, Install, First graph, How it works, Readers, Tested on, Developing graphe last (the editable install, the junction, the backlog, ADR 0004).
- [ ] What it reads: through imports and types (Python, JavaScript, TypeScript, Svelte, GDScript); by name (Go, Rust, Java, Kotlin, C, C++, C#, Ruby, Swift, PHP); Markdown documents; no framework specific, a front-to-back link through `[keys]`; a "not read" line (`.jsx`/`.tsx`, Vue); the detail linked.
- [ ] Install, the same commands on the three OS: `uv tool install graphe-code`, with the line on `graphe-cli`'s `graphe` and `--force`; the plugin; the `permissions.allow` line; for other agents, copy the skill folder.
- [ ] First graph: a git repository, `graphe install`, `graphe explain <a function>`; `graphe.toml` said optional, a short commented example (`exclude`, `displayed_text`, `[keys]`); no `init`.
- [ ] One line: a `graphe.toml` declaring extensions runs their code at every build, git hooks included.
- [ ] Gaps go to the GitHub issues.
- [ ] The contribution doc says the contract is public, an extension runs in graphe's environment (the standard library and graphe's dependencies), and shows a small invented extension, not Grid Zero's.

## Comments

- 2026-11-26: done on `integration/installable`, code-reviewed: the README for a stranger and the contribution doc (the contract public, an invented extension).
