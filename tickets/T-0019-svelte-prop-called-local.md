Status: ready-for-agent
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0019: A Svelte prop called is `local`

## What to build

BACKLOG.md (4cast): `let { onouvrir } = $props()` at the top of the `<script>`; `onouvrir()` is `unknown`, since `_declared` sees the names of a function, not those the module declares. A name declared at the top of a module (a variable, a destructured prop) and called is `local`.

## Acceptance criteria

- [ ] A prop destructured from `$props()` and called is `local` in `check`, not `unknown`.
