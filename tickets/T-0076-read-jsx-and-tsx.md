Status: ready-for-agent
Part of: T-0071
Blocked by: T-0072, T-0075
Created: 2026-11-27

# T-0076: Read `.jsx` and `.tsx`

## What to build

A React host gets no graph of its `.jsx` and `.tsx` files (README, "Not read"). The JS reader takes them: `.jsx` with the JavaScript grammar, which parses JSX, `.tsx` with the TSX grammar the TypeScript package ships beside the one the reader loads. Their imports, calls and definitions are read as a `.js` or `.ts` file's.

A JSX `<Component/>` is not a call: it stays with the framework entry of the backlog (T-0047).

## Acceptance criteria

- [ ] A host with a `.tsx` component and a `.jsx` one answers `explain` on their functions with their callers across files, through the imports.
- [ ] A call inside a JSX expression (`onClick={() => save(x)}`) belongs to its enclosing function.
- [ ] The JS sample host of T-0072 gains a `.jsx` and a `.tsx` file, its snapshot updated.
- [ ] The README's "What it reads" and `docs/readers.md` say so; `.jsx`/`.tsx` leave the "Not read" row.
- [ ] BACKLOG.md's entry "`.jsx`, `.tsx` and Vue are not read." says what is left (Vue, T-0082).

## Blocked by

- T-0072 (the JS sample host and its snapshot).
- T-0075 (both edit the README).
