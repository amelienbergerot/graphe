Status: ready-for-agent
Type: task
Part of: T-0001
Blocked by: T-0011
Created: 2026-11-17

# T-0014: JS reader with tree-sitter, plugged into dpe

## What to build

A reader based on tree-sitter (ADR 0002) reads the `.js` and `.mjs` files. It produces the modules, the functions, the classes and their methods, and resolves calls by the name and by the imports. The choice of grammars (one common package or one package per language) is made here. dpe becomes the second host: its `graphe.toml` excludes the debugging folder, and its XML data are ignored without setup.

## Acceptance criteria

- [ ] A small sample JS project, with a named import, a default import and a method call, gives the expected links.
- [ ] `graphe explain` works on a function of dpe's calculation engine, and names the ticket that cites it.
- [ ] The coverage of `check` on dpe is noted in this ticket, as a reference.
- [ ] The calls the reader misses on dpe are noted in the backlog, with the host.
