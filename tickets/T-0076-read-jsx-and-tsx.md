Status: closed
Part of: T-0071
Blocked by: T-0072, T-0075
Created: 2026-11-27

# T-0076: Read `.jsx` and `.tsx`

## What to build

A React host gets no graph of its `.jsx` and `.tsx` files (README, "Not read"). The JS reader takes them: `.jsx` with the JavaScript grammar, which parses JSX, `.tsx` with the TSX grammar the TypeScript package ships beside the one the reader loads. Their imports, calls and definitions are read as a `.js` or `.ts` file's.

A JSX `<Component/>` is not a call: it stays with the framework entry of the backlog (T-0047).

## Acceptance criteria

- [x] A host with a `.tsx` component and a `.jsx` one answers `explain` on their functions with their callers across files, through the imports.
- [x] A call inside a JSX expression (`onClick={() => save(x)}`) belongs to its enclosing function.
- [x] The JS sample host of T-0072 gains a `.jsx` and a `.tsx` file, its snapshot updated.
- [x] The README's "What it reads" and `docs/readers.md` say so; `.jsx`/`.tsx` leave the "Not read" row.
- [x] BACKLOG.md's entry "`.jsx`, `.tsx` and Vue are not read." says what is left (Vue, T-0082).

## Blocked by

- T-0072 (the JS sample host and its snapshot).
- T-0075 (both edit the README).

## Comments

- 2026-11-27: done. `js.PARSERS` takes `.jsx` with the JavaScript grammar and `.tsx` with `tree_sitter_typescript.language_tsx()` (TypeScript's own grammar reads `<T>x` as a cast); `js.SUFFIXES` lets a relative specifier leave either out (`./Panel` is `./Panel.tsx`). Nothing else changed: the JSX grammars give an arrow function in `onClick={() => save(x)}` as a nested function, whose calls already belonged to the enclosing one. The JS sample host gains `src/ui/Panel.tsx` and `src/ui/Form.jsx`; the snapshot's twelve new lines were written by hand before the reader took them, and the build gave exactly those (no link from a JSX tag). After the review: a bare handler in JSX (`onSubmit={save}`, a `jsx_expression`) is a `references`, as Svelte markup's `onclick={fermer}` is (T-0022).
