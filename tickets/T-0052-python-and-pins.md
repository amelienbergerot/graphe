Status: resolved
Type: grilling
Part of: T-0048
Created: 2026-11-26

# T-0052: Python and the dependency pins

## Question

`requires-python = "==3.14.*"` and every dependency at an exact version, so that Grid Zero's layout fixture and its communities stay put. For a stranger's environment: ranges in `pyproject.toml`, exact versions only in `uv.lock` and the tests? Which Python versions are promised (3.13? 3.15 once scipy exists for it)? What does a user lose if the layout or the communities differ by a version?

## Answer

Decided with the user (grilling, 2026-11-26), on facts measured that day (the 89 tests, the layout fixture included, at the exact pins):

- **Python: `requires-python = ">=3.13"`, no upper bound.** 3.13, 3.14 and 3.15 pass; 3.12 fails on `PurePath.full_match` (3.13+, `graphe_root.py`), not worth replacing. A cap would make uv refuse a newer Python where everything works; the CI confirms the newest. The `pyproject.toml` comment "scipy does not exist yet for 3.15" is stale: scipy 1.18.1 runs on 3.15.
- **Ranges in `pyproject.toml`, exact versions only in `uv.lock`.** `uv tool install` (T-0049) ignores `uv.lock`: a user gets what the ranges allow. networkx, numpy, scipy: a lower bound only (today's version). tree-sitter and its thirteen grammars: the lower bound plus a cap at the next minor (`<2` for kotlin 1.1), since the queries name the grammars' node types and a rename breaks or silently empties them. pytest stays exact in the `dev` group. On 2026-11-26 the newest versions equal the pins.
- **What a user loses**: only the picture's shape after an upgrade; communities and positions (`seed=0`) are reproducible for a given set of versions, nothing is kept between two `view`. The fixture `layout_01a698e.json` stays a check of graphe's own code, valid on the locked versions.
- **What the CI tests (for T-0054)**: the locked versions on the three OS, with 3.13 and the newest Python; one job on Linux, newest Python, `uv sync --upgrade` (the newest the ranges allow), skipping the layout fixture.
