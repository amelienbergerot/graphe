Status: ready-for-agent
Part of: T-0048
Blocked by: T-0061
Created: 2026-11-26

# T-0062: Python 3.13 and version ranges

## What to build

A user installed by `uv tool install` gets what the ranges allow, on any Python from 3.13 (T-0052): `requires-python` `>=3.13` uncapped; networkx, numpy, scipy a lower bound only; tree-sitter and its thirteen grammars the lower bound plus a cap at the next minor (`<2` for kotlin 1.1); pytest exact in the dev group; exact versions only in the lock file.

## Acceptance criteria

- [ ] The tests pass on 3.13 and 3.14 at the locked versions.
- [ ] The stale "scipy does not exist yet for 3.15" comment and the "pinned for Grid Zero's reference test" comment go; the ruff target follows 3.13.
- [ ] The README's install line no longer forces `--python 3.14`.
