Status: resolved
Type: grilling
Part of: T-0048
Created: 2026-11-26

# T-0050: The licence

## Question

Which licence for the public repository (MIT, Apache-2.0, other)? Check the dependencies' licences (networkx, numpy, scipy, the tree-sitter grammars) allow it.

## Answer

Decided with the user (grilling, 2026-11-26):

- **MIT.** The dependencies allow it: networkx, numpy, scipy BSD-3-Clause (numpy also MIT, Zlib, 0BSD, CC0 for bundled parts), tree-sitter and its thirteen grammars MIT, pytest MIT; none copyleft, and graphe installs them, it bundles none.
- **The holder**: `Copyright (c) 2026 Amélien Bergerot`.
- **The scope**: the repository's own files. Grid Zero and 4cast are the user's own projects; what of them the repository quotes (tests, tickets, docs) is the user's to publish. The tests marked `grid_zero` read Grid Zero beside the repository and are skipped without it. Which local extensions go public stays in the map's fog.
- **The declaration**: a `LICENSE` file at the root, `license = "MIT"` and `license-files = ["LICENSE"]` in `pyproject.toml` (PEP 639, `setuptools>=77`); no per-file headers.
