Status: ready-for-agent
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0018: A re-exported npm name is `external`

## What to build

BACKLOG.md (dpe): `ui_helpers.mjs` re-exports `VirtualConsole` from `jsdom`; `new VirtualConsole()` in `ui.test.mjs` follows the import to a name of ours that is not defined: `absent`. A re-export from a package leads to the package: `external`.

## Acceptance criteria

- [ ] A name re-exported from a package and called in another file is `external` in `check`.
