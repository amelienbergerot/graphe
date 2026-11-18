Status: closed
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0019: A Svelte prop called is `local`

## What to build

BACKLOG.md (4cast): `let { onouvrir } = $props()` at the top of the `<script>`; `onouvrir()` is `unknown`, since `_declared` sees the names of a function, not those the module declares. A name declared at the top of a module (a variable, a destructured prop) and called is `local`.

## Acceptance criteria

- [x] A prop destructured from `$props()` and called is `local` in `check`, not `unknown`.

## Comments

- The names a module declares (`_declared` of the module, minus its definitions and imports) hide like a function's: a called prop, or a module's `const f = async () => ...` inside a block, is `local`. 4cast: `unknown` 13 -> 4 (left: `super()`, two IIFEs, `taches[k]()`), `local` 53 -> 62. dpe: `unknown` 46 -> 23, `ambiguous` 9 -> 0 (`tools/capture_ecran.mjs` declares its own `evaluer`), `local` 362 -> 394.
- **Grid Zero** (snapshot to retake at the end of the batch): its coverage `js` only, `unknown` 4 -> 2, `local` 2; no node, no link.
- Grid Zero's snapshot retaken once for the batch, on the user's decision (Grid Zero 31a1317).
