# What the graph could not tell

The tool's single backlog, for all its hosts. Each time `graphe` is not
enough and a search is done by hand (grep, sed, reading), an entry here: the
host, what we were looking for, what the graph answered, how we found it.
Material to improve the tool later (the user's request, 2026-11-02).

A settled entry moves to "Settled", with the commit. The entries settled
before T-0003 come from Grid Zero, and their commits are Grid Zero's.

## Open

- **On a large repository, a stale query waits for a whole build.** [T-0026] (Django,
  sample host, 2026-11-18, T-0016) 2943 Python files: 48 s per build, and
  one edit not yet committed is enough to make the graph stale. The Python
  reader takes most of it now. A rebuild of only the files that changed
  (or a query that answers from the old graph and says so) would avoid it.
  T-0026: 45 s, then a cache of each Python file's definitions (about
  4.6 s less); the layout outside the queries is the lever left.
- **A host in another language gets no graph.** (All hosts, 2026-11-18,
  the user's request) Only Python, GDScript, PHP and JS/TS/Svelte have a
  reader: a Java, C#, Go, Rust... host is grep only. Decided in a grilling
  session: a generic reader first, every link by name, for many languages
  at once; a dedicated reader for one language only when this backlog shows
  the generic one falls short on a real host (as ADR 0002 does for the
  TypeScript compiler). First languages: Java, C#, Go, Rust, Ruby, C, C++,
  Swift, Kotlin, by queries of ours, specified per language in
  `docs/readers.md`; their grammars pinned in the main dependencies. A call is
  linked only when its name has a single definition, the others counted as
  not attributed. A language is done on a public sample host: builds, 0
  dangling, `check` coverage, 3 queries compared with grep (ADR 0003). The
  sample hosts, pinned, in `docs/sample-hosts.md`, summed up in the README:
  protobuf, libsignal, gitea (and Django). T-0030; Go is read since T-0031
  (gitea), Rust since T-0032 (libsignal), the other languages follow in
  T-0033 to T-0038.
- **A Go file in Go 1.26's syntax is skipped whole.** (gitea, sample host,
  2026-11-19, T-0031) `tree-sitter-go` 0.25.0, the last on PyPI, knows
  neither `new(expr)` nor generic methods (`func (f *Flash) Error[T ...]`):
  47 of gitea's 3199 Go files have an error node and are skipped, 15 of them
  outside the tests. A definition in such a file is lost everywhere:
  `ctx.ServerErrorAuto` (`services/context/context_response.go`) is
  `external` at its 1226 calls; `DecodeJSON` has 533 callers' calls, grep
  155 more in skipped files. A newer grammar, or reading the valid part of a
  tree with errors, would avoid it.
- **The generic reader cannot tell a Go package's function from another's.**
  (gitea, sample host, 2026-11-19, T-0031) `pkg.F()` is a send linked by the
  name alone: 27174 calls are `ambiguous` (`t.Context` 3885, `MakeRequest`
  1871, `NewRequest` 1647, `ctx.Tr` 849) and 23957 `common` (`t.Run`,
  `fmt.Errorf`, `log.Error`, `filepath.Join`), against 52902 linked by name.
  Go's imports name the package of `pkg.F()` for sure: a dedicated Go reader
  (ADR 0003) would link most of them, and would leave `strings.Join` out of
  the host's `Join` without a common name.
- **A Rust call inside a macro is not seen.** (libsignal, sample host,
  2026-11-19, T-0032) tree-sitter-rust leaves a macro's arguments as tokens:
  `assert_eq!(f(x), y)`, `vec![g()]`, `format!("{}", h())` hold no call.
  libsignal has 8604 macro invocations (`assert_eq!` 1624, `vec!` 1155,
  `assert!` 716); `Timestamp::from_epoch_millis(` has 81 grep lines, 64 calls
  the graph sees, most of the 17 others inside a macro. Parsing a token tree
  as expressions when it parses would recover them.
- **A Rust type's `impl` in another file than its `struct` is another class
  node.** (libsignal, sample host, 2026-11-19, T-0032) The classes of one
  name are merged per file only: 506 of libsignal's 2053 class names have
  nodes in several files (`Error` 26, `Redact` 16), so 605 of its 3250
  `T { .. }` are `ambiguous` and not linked. `impl<T> Tr for T` draws a class
  `T` (15 files), `impl Tr for Vec<X>` a class `Vec` (10). Swift's
  extensions (T-0037) take the same shape: merging a class's nodes across
  files, or a `@class` that only extends, is the generic reader's own ticket.
- **A Rust `Type::f()` path is not linked when `f` is a common name.**
  (libsignal, sample host, 2026-11-19, T-0032) `T::f()` is a send, like
  `x.f()`: `DeviceId::new` (183 calls), `ProtocolAddress::new` (132),
  `TestStoreBuilder::new` (64) are `common`, never linked, though the path
  names the type; 14660 sends are `common`, 8944 calls `ambiguous`
  (`KeyPair::generate` 118, defined in 6 `struct KeyPair`), against 6702 linked by
  name. Linking `T::f` to the method `T.f` when `T` is a class of the host
  would link most of them, and Java's `C.f()` too: outside "by the name
  alone" (ADR 0003), to decide.
- **A Rust file with `dyn 'a + Trait` is skipped whole.** (libsignal,
  sample host, 2026-11-19, T-0032) `tree-sitter-rust` 0.24.2 rejects a
  lifetime first in a trait object (`Box<dyn 's + FnOnce(..)>`):
  `rust/bridge/shared/types/src/net/tokio.rs`, 1 of 612 files.
- **PHP's pattern reader may be worse than the generic one.** (4cast,
  2026-11-18, the readers' grilling) Once the generic reader exists, compare
  it with `graphe_php.py` on 4cast; replace the pattern reader only if the
  generic one does at least as well.
- **Only its author can install the tool.** (All hosts, 2026-11-18, the
  user's request) The install depends on `E:/dev/graphe`, an editable
  `uv tool install` and PowerShell (README); ADR 0001 says "for a single
  user". The direction is other people's repositories: a published package,
  any OS, and ADR 0001 revisited. A separate effort, after the readers; until
  then a reader holds nothing specific to this machine.
- **The links a framework creates are outside the graph.** (All hosts,
  2026-11-18, the user's request) A Django URL to its view, a JSX
  `<Component/>`, a Spring injection, a Rails route: no call carries them.
  Neither the core, nor a reader (one language), nor a local extension (one
  host): a notion to name. Its own session, after the readers. The bridges
  between languages belong with it (JNI, FFI, protobuf's generated code):
  the generic reader never links a call by name across languages (ADR 0003).

## Settled

Settled by tickets (2026-11-18):

- **The tests that compare a whole message** stay outside the graph. [T-0029, wontfix]
  (Grid Zero) The tests are excluded from it.
- **A "where does X work" question needs a bench, not a query.** [T-0028, wontfix]
  (Grid Zero, 2026-11-02, prévisionniste) To know in which scenarios the aid
  acts, every scenario had to be played. The graph says who reads
  `PREVISIONNISTE`, not which data make it active (a weather window that
  contains line incidents). To be kept outside the graph.
- **The translation files are outside the graph.** [T-0027, wontfix] (Grid Zero, 2026-11-02)
  - `godot/i18n/*.po` are read by grep. Probably to be kept that way:
    `tools/i18n.py etat` already says what is missing.
- **`explain` does not say what it misses.** [T-0025] (Django, sample host,
  2026-11-18, T-0016) `explain query.py::QuerySet.filter` gives 3 callers,
  but grep finds hundreds of `.filter(` calls: a manager
  (`Model.objects.filter`) is a receiver whose type the reader does not
  know. The graph could count the unresolved calls by name in each body
  (the `check` sites have them) and show "plus N `.filter()` not
  attributed" so that the agent knows when to grep.
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
- **The calls in a Svelte component's markup are not read.** [T-0022] (4cast,
  2026-11-18, T-0015) Only the `<script>` goes to the grammar; the markup is
  blanked out. About 213 calls in the markup of 17 components
  (`onclick={() => rafraichir(1)}`, `{jourCourt(j.date)}`) are missed: 36 of
  the 77 component functions have no caller. The reader could parse each
  `{...}` of the markup as an expression, its calls belonging to the file.
  A component used as `<Mini />` is only an `imports` link, never a call.
- **A call in a test's callback belongs to the file.** [T-0021] (dpe, 2026-11-18, T-0014)
  `test('...', () => { compute(...) })`: the caller is `compute.test.mjs`,
  not the test, which is not a node. `explain compute` lists 20-odd test
  files rather than the tests.
- **The test harness's methods are linked by the name.** [T-0020] (4cast,
  2026-11-18, T-0015) `faux.de()`, `faux.vider()`... in `tests/api` (31
  sites, `ours?`): the right method, but INFERRED. Same cause as the methods
  of an object literal (dpe, above).
- **The methods of an object literal are not nodes.** [T-0020] (dpe, 2026-11-18, T-0014)
  dpe's UI tests build a page object (`return { async saisir(id, v) {...} }`)
  and call `p.saisir()`, `p.clic()`, `p.ep()`, `p.stocke()`: about 150 member
  calls classified `member`, linked to nothing. The imports would not catch
  them (the object is returned, not exported); the types would (ADR 0002).
  The JS reader could make a node of such a method, then link `x.m()` by the
  name as it does for class methods.
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
