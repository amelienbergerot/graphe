Status: resolved
Type: grilling
Part of: T-0048
Created: 2026-11-26

# T-0057: The package

## Question

The seven top-level modules (`graphe_core` and the others) would collide in a user's environment: they become one package under `src/`. Its import name: `graphe` (as the command, but PyPI's `graphe` installs a `graphe` module too, T-0049) or `graphe_code` (as the distribution, T-0055)? What a local extension imports from it (the `contribute(project)` contract, T-0051), the entry point of `[project.scripts]`, and what moves with the modules (the git hooks, the tests, the fixtures).

## Answer

Decided with the user (grilling, 2026-11-26). The facts found: the seven modules already sit under `src/`; a local extension is loaded by its path and runs in graphe's environment, so it can import any module; Grid Zero's imports internals (`from graphe_core import BODIES, _comment`, `from graphe_godot import Script`), 4cast has no Python extension (dpe and cadastre-poc not searched); the hooks call `graphe build` from the PATH, untouched by the move; the layout fixture is Grid Zero's graph, not graphe's, unchanged by renamed modules.

- **The import name is `graphe`**, as the command, the output folder, `graphe.toml` and the glossary. The clash with PyPI's `graphe` needs both pip-installed in one environment, which `uv tool` (ADR 0004) never does. From a host's root, its `graphe/` output folder (no `__init__.py`) loses to the installed package. Rejected: `graphe_code`, a third name.
- **One package, `src/graphe/`, the prefix dropped**: `cli` (today's `graphe.py`), `core`, `root`, `python`, `godot`, `js`, `generic`; an empty `__init__.py`; absolute imports (`from graphe import core`, `from graphe.root import ROOT`). The entry point is `graphe = "graphe.cli:main"`; `py-modules` gives way to the package. Rejected: the CLI in `__init__.py` (the package importing itself while it initialises). `python -m graphe` not added: nobody asked, the entry point does.
- **The public contract is `contribute(project)` alone**: the function, the `Project` object, and the shape of the nodes and links in `docs/contribution.md`. Anything else an extension imports from the package is internal, without guarantee, changed without notice. Rejected: a public `graphe.extension` module (until a stranger's extension needs one), the whole package public.
- **What moves with the modules**: the tests' imports and their runner (`import graphe.cli; graphe.cli.main(...)`), the docs naming a module (README.md, docs/contribution.md, docs/readers.md); the hooks and the fixtures stay. **Grid Zero follows at once**, in its own commit when the package lands: its two imports become `from graphe.core import BODIES, _comment` and `from graphe.godot import Script`. A line of the implementation ticket, not a ticket of this map.

## Comments

- 2026-11-26: resolved; T-0058 unblocked.
