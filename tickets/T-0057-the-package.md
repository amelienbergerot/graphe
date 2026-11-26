Status: open
Type: grilling
Part of: T-0048
Created: 2026-11-26

# T-0057: The package

## Question

The seven top-level modules (`graphe_core` and the others) would collide in a user's environment: they become one package under `src/`. Its import name: `graphe` (as the command, but PyPI's `graphe` installs a `graphe` module too, T-0049) or `graphe_code` (as the distribution, T-0055)? What a local extension imports from it (the `contribute(project)` contract, T-0051), the entry point of `[project.scripts]`, and what moves with the modules (the git hooks, the tests, the fixtures).
