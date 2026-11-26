Status: closed
Type: task
Part of: T-0001
Blocked by: T-0014
Created: 2026-11-17

# T-0015: TypeScript and Svelte, plugged into 4cast

## What to build

The JS reader also reads the `.ts` files and the `<script>` block of the `.svelte` files. 4cast becomes the third outside host. Its `graphe.toml` gives the identifier pattern of its issues, and its PHP API is read by the existing PHP reader.

## Acceptance criteria

- [x] A small sample TS and Svelte project gives the expected links, including from a Svelte component to a TS function.
- [x] In 4cast, `graphe path` links a Svelte component to the TS function it calls, and `explain` names the issue that cites it.
- [x] The coverage of `check` on 4cast is noted in this ticket, as a reference.
- [x] The missed calls are noted in the backlog, with the host.

## Comments

- **The reader** (`src/graphe_js.py`, still section and coverage `js`): `.ts` and the `<script>` blocks of a `.svelte` go to the TypeScript grammar (`tree-sitter-typescript`, `language_typescript`); the markup is blanked out byte for byte, so the lines and the offsets stay those of the file. A relative specifier may leave out `.ts` (`./lib/eau`). Typed parameters hide an import like the others; `extends` in a TS class is followed; Svelte's runes (`$state`, `$derived`...) are `global`. Neither `.tsx`, nor the `.js` -> `.ts` mapping of NodeNext, nor aliases (`$lib`): 4cast has none.
- **Two fixes found on 4cast**, outside the JS reader. The Python reader looped forever on `for l in t11: l = l[1:]` at the top of a module (`donnees/fao56/extraire.py`): a module variable is now guarded like a local. The core's `end` stopped a PHP function at its signature when its `{` is alone on the next line (PSR-12): 4cast's PHP API had 35 functions and 0 calls, now 64. The same fix adds 38 calls in Grid Zero's `web/lib/gabarit.php`: its snapshot is retaken on the user's decision (Grid Zero c0807d7).
- **4cast** (its commit d224d6c): `graphe.toml` excludes `.scratch/4cast-v1/tasks` (a one-off PHP script), and its identifier `(?i)(?:(?<=\bticket )|(?<=\btickets ))\d{2}\b|^\d{2}(?=-)` makes the 51 issues `.scratch/4cast-v1/issues/NN-slug.md` tickets, cited by « ticket NN » (the first number of « tickets 33, 34 »). 53 TS and Svelte files, none with a parse error; the core's `end` matches tree-sitter's on all 201 bodies (and still on dpe's 287). `graphe build`: 389 nodes, 873 links, 23 communities, 0 dangling. `graphe path rafraichirNdvi aRafraichir`: from `Tableau.svelte` to `src/lib/ndvi.ts` in one call, and `graphe explain aRafraichir` names issue 48, which names it between backticks (`rafraichirNdvi`'s comment cites it too). `ndviRecent`, which it also calls, gets no issue: issue 48 writes it with its arguments (BACKLOG.md). `graphe install` and the `graphe/` output in its `.gitignore` are left to the user (the working tree held changes of theirs).
- **The coverage of `check` on 4cast, as a reference**: `js`: 2537 sites, `member` 881, `ours` 627, `external` 555, `global` 377, `local` 53, `ours?` 31, `unknown` 13; 0 alerts. `python` (its data scripts): `external` 111, `ours` 25, `external?` 10. `php` classifies no calls (64 links). `unknown`: the props called (`onfini()`), `super()`, two IIFEs, `taches[k]()`; `ours?`: the test harness `faux`.
- **Missed calls** (BACKLOG.md, 4cast): the calls in the Svelte markup (about 213, 36 of the 77 component functions without a caller), the props `unknown`, the harness `faux` INFERRED, the top-level calls of `api/index.php` (the router) linked to nothing; and a function an issue names with its arguments.
- The global command must be reinstalled after the new dependency: `uv tool install -e <graphe> --python 3.14 --reinstall`.
