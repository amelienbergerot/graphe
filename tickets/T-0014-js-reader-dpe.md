Status: closed
Type: task
Part of: T-0001
Blocked by: T-0011
Created: 2026-11-17

# T-0014: JS reader with tree-sitter, plugged into dpe

## What to build

A reader based on tree-sitter (ADR 0002) reads the `.js` and `.mjs` files. It produces the modules, the functions, the classes and their methods, and resolves calls by the name and by the imports. The choice of grammars (one common package or one package per language) is made here. dpe becomes the second host: its `graphe.toml` excludes the debugging folder, and its XML data are ignored without setup.

## Acceptance criteria

- [x] A small sample JS project, with a named import, a default import and a method call, gives the expected links.
- [x] `graphe explain` works on a function of dpe's calculation engine, and names the ticket that cites it.
- [x] The coverage of `check` on dpe is noted in this ticket, as a reference.
- [x] The calls the reader misses on dpe are noted in the backlog, with the host.

## Comments

- **One package per language**: `tree-sitter-javascript` now, `tree-sitter-typescript` for T-0015 (it resolves for Python 3.14). The common package carries more than a hundred grammars for two. Svelte needs no grammar: the `<script>` block goes to the TS grammar.
- **The reader** (`src/graphe_js.py`, section and coverage `js`): a node per file, per top-level function (`function f`, `const f = () =>`), per class and per method (`Class.method`). A nested function is not a node: its calls belong to the function that contains it. Imports by relative specifier, re-exports (`export {...} from`, `export * from`) followed. A call is EXTRACTED by a top-level definition, an import, a namespace (`import * as`, `export * as`), `this.m()` (the parent classes too), `Class.m()`; INFERRED by the name alone when only one function or method of ours has it. A parameter or a variable of the calling function hides an import of the same name (`local`). The ids carry the extension (`src_zones_mjs`), and are made unique (`get x`/`set x`, `Foo`/`foo`): `zones.py` and `zones.mjs` do not merge. The core's `end`, by indentation, matches tree-sitter's on all 287 bodies of dpe: the core is unchanged.
- **dpe** (its commit 2060e0e): `graphe.toml` excludes `scratch_debug`; the XML of `dpe_reels/` have no reader. 108 files, none with a parse error. `graphe build`: 512 nodes, 1572 links, 38 communities, 0 dangling. `graphe explain summarize` (src/compute.mjs) gives `compute` as caller and T-0005, T-0029, T-0055 as the tickets that name it.
- **The coverage of `check` on dpe, as a reference**: `js`: 8593 sites, `external` 2556, `ours` 2425, `member` 2140, `global` 1054, `local` 362, `unknown` 46, `ambiguous` 9, `absent` 1; 0 alerts. (Before the review, 40 `ours?` were local functions taken for those of another file: all 40 are now `local`. 51 `global` became `member`: a global's receiver is now a bare name, so `Object.entries(x).map()` is a method of its result.) `python` (dpe's tools): `external` 55, `external?` 30, `ours` 9. `member` is a method of an object we do not know (`d.getElementById`); `local` a name the calling function declares (a parameter, a nested function); `unknown` a name neither ours nor declared (a callback in an object, `import()`).
- **Missed calls** (BACKLOG.md, dpe): the methods of an object literal (about 150 calls, `p.saisir()` in the UI tests), which the imports would not catch; a test's callback belongs to its file; a re-exported npm name classified `absent`.
- **Grid Zero** reads `tools/drift_references.mjs` too: one file node more, which moves every community number and position. Its snapshot is retaken on the user's decision (Grid Zero, T-0390, then with the id `tools_drift_references_mjs`); `simulation/tests/test_graphe.py` passes.
- The global command must be reinstalled after a new dependency: `uv tool install -e E:/dev/graphe --python 3.14 --reinstall`.
