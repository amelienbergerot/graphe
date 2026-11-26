Status: resolved
Type: grilling
Part of: T-0048
Blocked by: T-0049
Created: 2026-11-26

# T-0051: ADR 0001 revised

## Question

ADR 0001 says "one tool installed once, for a single user", in editable mode from a clone. What replaces it: the published install for a user, the editable one kept for the author? Does "local extensions in each host" stand as it is? Write the amendment or the new ADR.

## Answer

Decided with the user (grilling, 2026-11-26): a new ADR, `docs/adr/0004-published-install-editable-for-the-author.md`, replaces the install half of ADR 0001, which now points to it; the local extensions stand.

- **Two installs**: `uv tool install graphe-code` for a user, `uv tool install -e .` from the clone for the author; pipx and `git+` not promised (the README may mention pipx).
- **Local extensions unchanged**: in the host, declared in `graphe.toml`, loaded by path; not packages (no entry points).
- **The `contribute(project)` contract is public**; how a change to it is announced goes to the versioning (map fog).
- **An extension runs in graphe's environment**: the standard library and graphe's dependencies, not the host's, none of its own. To say in `docs/contribution.md`.
- **A `graphe.toml` runs code**, like a Makefile: to say in the README; no opt-in flag, no trust prompt.
