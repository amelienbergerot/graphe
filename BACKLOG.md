# What the graph could not tell

The tool's single backlog, for all its hosts. Each time `graphe` is not
enough and a search is done by hand (grep, sed, reading), an entry here: the
host, what we were looking for, what the graph answered, how we found it.
Material to improve the tool later (the user's request, 2026-11-02).

A settled entry moves to "Settled", with the commit. The entries settled
before T-0003 come from Grid Zero, and their commits are Grid Zero's.

## Open

- **The translation files are outside the graph.** [T-0027, wontfix] (Grid Zero, 2026-11-02)
  - `godot/i18n/*.po` are read by grep. Probably to be kept that way:
    `tools/i18n.py etat` already says what is missing.
- **A "where does X work" question needs a bench, not a query.** [T-0028, wontfix]
  (Grid Zero, 2026-11-02, prévisionniste) To know in which scenarios the aid
  acts, every scenario had to be played. The graph says who reads
  `PREVISIONNISTE`, not which data make it active (a weather window that
  contains line incidents). To be kept outside the graph.
- **The tests that compare a whole message** stay outside the graph. [T-0029, wontfix]
  (Grid Zero) The tests are excluded from it.

- **The methods of an object literal are not nodes.** [T-0020] (dpe, 2026-11-18, T-0014)
  dpe's UI tests build a page object (`return { async saisir(id, v) {...} }`)
  and call `p.saisir()`, `p.clic()`, `p.ep()`, `p.stocke()`: about 150 member
  calls classified `member`, linked to nothing. The imports would not catch
  them (the object is returned, not exported); the types would (ADR 0002).
  The JS reader could make a node of such a method, then link `x.m()` by the
  name as it does for class methods.
- **A call in a test's callback belongs to the file.** [T-0021] (dpe, 2026-11-18, T-0014)
  `test('...', () => { compute(...) })`: the caller is `compute.test.mjs`,
  not the test, which is not a node. `explain compute` lists 20-odd test
  files rather than the tests.
- **The calls in a Svelte component's markup are not read.** [T-0022] (4cast,
  2026-11-18, T-0015) Only the `<script>` goes to the grammar; the markup is
  blanked out. About 213 calls in the markup of 17 components
  (`onclick={() => rafraichir(1)}`, `{jourCourt(j.date)}`) are missed: 36 of
  the 77 component functions have no caller. The reader could parse each
  `{...}` of the markup as an expression, its calls belonging to the file.
  A component used as `<Mini />` is only an `imports` link, never a call.
- **The test harness's methods are linked by the name.** [T-0020] (4cast,
  2026-11-18, T-0015) `faux.de()`, `faux.vider()`... in `tests/api` (31
  sites, `ours?`): the right method, but INFERRED. Same cause as the methods
  of an object literal (dpe, above).
- **A function named with its arguments is not linked.** [T-0024] (4cast,
  2026-11-18, T-0015) Issue 48 writes `` `ndviRecent(geometrie, aujourdhui)` ``:
  the core's backticks take `name` and `name()` only, so `explain
  ndviRecent` names no issue. 4 such citations in 4cast. Taking any
  `(...)` would change Grid Zero's links (its snapshot).
- **A PHP file's top-level calls belong to nothing.** [T-0023] (4cast, 2026-11-18,
  T-0015) `api/index.php` routes at the top of the file (`route_zones($db,
  ...)`, `match` on `$chemin`): the PHP reader reads calls only in bodies, so
  `explain route_zones` shows no caller. The JS reader gives them to the
  file node; the PHP reader could do the same.
- **On a large repository, a stale query waits for a whole build.** [T-0026] (Django,
  sample host, 2026-11-18, T-0016) 2943 Python files: 48 s per build, and
  one edit not yet committed is enough to make the graph stale. The Python
  reader takes most of it now. A rebuild of only the files that changed
  (or a query that answers from the old graph and says so) would avoid it.
- **`explain` does not say what it misses.** [T-0025] (Django, sample host,
  2026-11-18, T-0016) `explain query.py::QuerySet.filter` gives 3 callers,
  but grep finds hundreds of `.filter(` calls: a manager
  (`Model.objects.filter`) is a receiver whose type the reader does not
  know. The graph could count the unresolved calls by name in each body
  (the `check` sites have them) and show "plus N `.filter()` not
  attributed" so that the agent knows when to grep.

## Settled

Settled by tickets (2026-11-18):

- **A Svelte prop called is `unknown`.** [T-0019] (4cast, 2026-11-18, T-0015)
  `let { onouvrir } = $props()` declares it at the top of the component,
  which `_declared` does not see (functions only): `onfini()`, `onouvrir()`,
  `onchoix()`, about ten sites. Nothing missed, the verdict only.
- **A re-exported npm name is `absent`, not `external`.** [T-0018] (dpe, 2026-11-18,
  T-0014) `ui_helpers.mjs` re-exports `VirtualConsole` from `jsdom`;
  `new VirtualConsole()` in `ui.test.mjs` follows the import to a name of
  ours that is not defined. One site; nothing missed.

Settled together (2026-11-05, T-0354):

- **A value exchanged between the two languages.** (T-0351) `"coupee"`,
  written by `InterconnectionFleet.settle_severed` and compared by
  `texte_d_interconnexion`; `"reparer_liaison"`, from the game's thread to
  the debrief. A `value` node per string written in Python and in GDScript:
  `search coupee`, `explain '"coupee"'`. Also covers the keys of the other
  messages (`"tiree"`, `"defi"` of the catalogue).
- **A field written by keyword.** (T-0351) `EngineState(...,
  interconnection_unavailable_reason=...)`: `Engine.step` writes it.
- **The scenarios' hints.** (T-0337) A `hint` node per `[[hints]]`, linked
  to the functions whose text it cites between « ».
- **The Moonshot journal.** A node per iteration, linked to the tickets it
  cites (« T-0350 à T-0352 » included).

Settled together (2026-11-03, commit « graphe : champs, clés de l'état,
alias d'import, tickets »):

- **A class has its extent, and its fields are nodes.**
  `explain GenSpec --source` prints the class; `explain
  EtatDeJeu.manque_prevu_tranche` says who writes it (`_prevoir_le_manque`)
  and who reads it, on the Python side when the receiver's type is known.
- **The keys of the state lead to the client.** `state.get("demand_mw")` or
  `state["demand_mw"]` in a GDScript script reads the field (by the name):
  the field `manque_prevu_tranche` leads to `_manque_prevu_text`.
- **A Python import alias is sure.** `aides_de_camp.PREVISIONNISTE`
  reads the constant of `simulation/game/aides.py` as EXTRACTED.
- **Tickets are nodes.** The code that cites `T-0307` leads to it by
  `cites`; a ticket leads by `names` to the functions it writes between
  backticks. `explain _rafales` says T-0307 and T-0328. They form their own
  community, so as not to merge those of the code.

- **Accents came out as « D?fi » when a program reads the output.**
  (2026-11-02, T-0310) `explain envoyer_defi` printed « D�fi du
  jour »: Python writes cp1252 into a pipe. The output switches to UTF-8
  outside a terminal.

- **A Python `X.name` read a GDScript variable.** (2026-11-02,
  tempête) `explain ecrire_le_catalogue` said it reads `graine` of
  `godot/menu/fond_menu.gd` "by name", for an `examen.graine`. The link by
  name now stays within its language.

Settled together (commit « graphe : variables, source, PHP, textes et
commentaires »):

- **Module variables and constants are not nodes.** `variable` and
  `constant` nodes, `reads` and `writes` links; `explain _tirage` says who
  writes it and who reads it.
- **The graph says where the code is, not what it contains.** Each body has
  its end line; `explain X --source` prints its lines.
- **`search` takes a name, not a line of code.** `def`, `func`, `class`,
  `function`, `const` and `var` at the head are removed.
- **The online service's PHP is outside the graph.** `tools/graphe_php.py`:
  functions, actions, calls; the client's `{"action": ...}` lead to the
  actions by `sends`.
- **A name written through its preload constant is not recognised.**
  `callers Progress.record` finds `godot/settings/progress.gd`.
- **A displayed text does not lead to its code.** The texts of `I18n.t`
  are stored on their function; `search "Réseau stable"` leads to
  `_update_ui_from_state`.
- **A concept said in French in the comments cannot be found.** The
  comment above each function is stored on it; `search clarte` finds the
  functions of daylight.
