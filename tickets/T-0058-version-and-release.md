Status: resolved
Type: grilling
Part of: T-0048
Blocked by: T-0057
Created: 2026-11-26

# T-0058: The version and the release

## Question

The first version number and its scheme; what a release does and who runs it (the build, the upload to PyPI as `graphe-code`, the grammar caps raised, T-0052; the plugin's `version` set with the package's, T-0053); how a change to the `contribute(project)` contract is announced to strangers' extensions (T-0051).

## Answer

Decided with the user (grilling, 2026-11-26). The facts found: `version = "0.1.0"` in `pyproject.toml`, no git tag, no `graphe --version`; one number for skill and CLI (T-0053); the newest-versions CI job (T-0052).

- **SemVer, the first release `0.1.0`**, staying `0.x` while the `contribute(project)` contract may still move.
- **A release is a tag `vX.Y.Z` the author pushes**: a GitHub Actions workflow runs `uv build`, uploads `graphe-code` to PyPI by Trusted Publishing (no stored token; works on a private repository too), and creates the GitHub release. Rejected: a hand `uv publish` with a token on the author's machine.
- **One number in two files**, set by hand in the release commit: `pyproject.toml` and `.claude-plugin/plugin.json`; the workflow fails when the tag, the package and the plugin differ. No bump tool, no version in `marketplace.json`.
- **The grammar caps are not the release's**: when the newest-versions job flags a newer grammar, raising its cap (the cap, the queries, `uv.lock`) is an ordinary commit, shipped by the next release.
- **No `graphe --version`**: `uv tool list` shows the installed version; nobody asked.
- **A contract change is announced in `CHANGELOG.md`** at the root, one entry per release; a release changing `contribute(project)`, `Project` or the shape of the nodes and links carries a **Contract** section: what breaks, how to adapt an extension. Such a change is at least a minor bump in `0.x` (never a patch), a major from `1.0`. The GitHub release links to its entry. Rejected: a contract number declared in `graphe.toml` and checked by graphe (the version bump says it).

## Comments

- 2026-11-26: resolved; the fog "a stranger's first contact" graduates as T-0059.
