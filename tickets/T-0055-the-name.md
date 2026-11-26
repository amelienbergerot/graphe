Status: resolved
Type: grilling
Part of: T-0048
Created: 2026-11-26

# T-0055: The name, on PyPI and as a command

## Question

`graphe` is taken on PyPI (a graph-algorithms package) and as a command (`graphe-cli` installs one; T-0049). Which distribution name (`graphe-code`, `code-graphe`, other), and does the command stay `graphe` (a clash for a user of `graphe-cli`) or change? The command name reaches the skill, the hooks (`graphe build`), `graphe.toml`, the `graphe/` output folder and the permission rules.

## Answer

Decided with the user (grilling, 2026-11-26):

- **The command stays `graphe`.** Renaming it would reach the skill, the hooks, `graphe.toml`, the `graphe/` folder, the permission rules and the glossary, for one niche clash (`graphe-cli`, a CLI for the Graphe API). The clash is loud, not silent: `uv tool install` refuses to overwrite a command it did not install without `--force`. The README says so in one line.
- **The distribution name is `graphe-code`**: `uv tool install graphe-code`. The cost, on the ephemeral path only: `uvx --from graphe-code graphe`.
- **The import name is left to the packaging**, with a constraint: PyPI's `graphe` installs a `graphe` module too, so two `graphe` packages pip-installed in one environment overwrite each other silently; `uv tool` (isolated) avoids it.
