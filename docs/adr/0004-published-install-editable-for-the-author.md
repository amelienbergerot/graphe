# Published install, editable for the author

Replaces the install half of ADR 0001; its local extensions stand. graphe is published on PyPI as `graphe-code` (T-0049, T-0055): a user installs it with `uv tool install graphe-code`, the author keeps `uv tool install -e .` from the clone so that a change applies without reinstalling. No other install is promised.

Local extensions stay as ADR 0001 has them: stored in the host's repository, declared in its `graphe.toml`, loaded by path. Publishing changes three things about them:

- **The contract is public.** The schema of `contribute(project)` in `docs/contribution.md` is graphe's interface for strangers' extensions; changing it breaks them. How a change is announced belongs to the versioning.
- **An extension runs in graphe's environment.** `uv tool` isolates graphe, so an extension imports the standard library and graphe's dependencies, not the host's packages, and declares none of its own.
- **A `graphe.toml` runs code**, like a Makefile or a `conftest.py`: `graphe build` on a cloned repository, and the git hooks after it, run the extensions it declares. Said in the README; no opt-in flag, no trust prompt.

## Options set aside

- pipx or `git+https://` as supported installs: pipx never fetches a missing Python by default (T-0049); the README may mention it, the ADR promises uv only.
- Extensions as installable packages (entry points): an extension holds for one host only, and its package would be one more thing to publish and version.
- A trust prompt before running a host's extensions: the same trust as running its tests or its Makefile, which nobody asks for.
