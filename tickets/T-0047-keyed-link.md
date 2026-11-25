Status: closed
Type: task
Created: 2026-11-25

# T-0047: The keyed link, 4cast's front to its PHP routes

## What to build

A **keyed link** (GLOSSARY.md): from the body that names a key (a string both ends share: a route, a command) to the code that answers it, where no name in the code joins them. 4cast first (BACKLOG.md, "The links a framework creates are outside the graph"): its front calls `api<Zone[]>("zones")`, `` api(`zones/${id}`) `` (`src/lib/*.ts`), its PHP answers `$chemin === '/api/zones'` or `preg_match('#^/api/zones/(\d+)$#', ...)` (`api/index.php`, `api/lib/*.php`). Today nothing leads from `listerZones` to `route_zones`.

The core makes it, from three patterns of the host's `graphe.toml`, as it finds the displayed texts (T-0009): the core holds no language's syntax, the host says where its keys are.

```toml
[keys]
names = '...'       # one group: the key, where the code names it
answers = '...'     # one group: the key, where the code answers it
parameters = '...'  # optional: what stands for a parameter in a key, replaced by `*` on both sides
```

- A key is the group, its parameters replaced by `*`: `` zones/${id} `` and `zones/(\d+)` are both `zones/*`. Two keys match when they are equal: `*` is no wildcard (a `` `/api/${chemin}` `` of `*` alone would match every route).
- The namer is the smallest body whose lines hold the naming line, its head line included (a one-line arrow, `listerZones = () => api("zones")`, names on its head), else the file.
- The answerer is what the answering line calls (`$chemin === '/api/meteo' => route_meteo(...)`, at `api/index.php`'s top: `route_meteo`), else the smallest body holding the line (`route_zones`). Not the file: `if ($chemin === '/api/session') {` at index.php's top answers nothing (see the comments).
- The link is `sends` (the relation Grid Zero's extension already gives an order to its command, in `CALLS`: `callers` and `path` follow it), `INFERRED` (by a string), the key as its context, at the naming line. A comment line names and answers nothing.

Decided (2026-11-25, with the user's go to write and implement it): in the core, configured by the host, not a reader (two languages) nor 4cast's extension (the next host would copy it); the relation `sends`, no new one; the HTTP method is not in the key (`shortcut:`: index.php checks it on another line than the path, `match ($methode)`), so `lireZone`, `modifierZone` and `supprimerZone` all lead to `route_zones`; one `[keys]` table, not a list (a host with two kinds of key, when one asks). Grid Zero's `sends` stay its extension's (its `"cmd"` and `"action"` keys could become a `[keys]` later: not this ticket).

## Acceptance criteria

- [x] `[keys]` in `graphe.toml`: `names` and `answers` with one group each, `parameters` optional; a bad pattern stops the build with a message, as `displayed_text`.
- [x] Tested at `enrich()`: a one-line arrow and a two-line one name; a top-level `match` arm answers by its call, an `if` in a function by its function, a top-level `if` without call answers nothing; a `preg_match` group and a `${}` are `*`; a query string stays out of the key; a key nobody answers and a key of `*` alone link nothing; a comment names nothing.
- [x] 4cast: its `graphe.toml` declares its keys (a commit of its own); each key its front names is answered, or the ones that are not are listed here; `graphe.json` before and after differ only by the new `sends` links.
- [x] `--help`, the README's "How it works", `docs/contribution.md` say it; BACKLOG.md's entry settled for the user's hosts, the frameworks left.
- [x] The tests pass.

## Comments

- **Done** (2026-11-25): `graphe_core._link_keys`, after the values, before the documents (a Markdown file names no route: the documents are not among the scanned files). `displayed_text_pattern` and `[keys]` share `_pattern` (a bad pattern, a missing group: the build stops, naming the key). The namer's body counts its head line, where the core's `owners` do not (a one-line arrow, `listerZones`, would have named from its file); the answerer's calls are the `calls` links located at its line. Tested at `enrich()` on a front and an `index.php` (the mutation that leaves the head line out fails it).
- **The file is no answerer**: first made, `if ($chemin === '/api/session') {` at index.php's top made the file answer `session`; but the file calls every route (its `match`), so `callers route_meteo` went at level 2 to `etatSession`, `seConnecter`, `seDeconnecter`, which never reach it. A false lead costs more than a missing link (ADR 0003): a top-level line without a call answers nothing.
- **4cast** (`d7091f9`, its `graphe.toml` declaring `[keys]`: `api(` or the tests' `appel(`, `/api/` optional, the query string out; `$chemin === '` or `preg_match('#^`, so that `amont(..., '/api/cadastre/parcelle')`, IGN's route, answers nothing; `${...}` and `(...)` are `*`): 35 `sends`, every node and every other link identical to the graph before (the communities move: 137 of 519 nodes, 23 groups as before; an untracked note, `research/52-...md`, appeared in 4cast meanwhile, one `ticket` node more, left out of the comparison). Front (`src/`): 22 of its 25 naming lines linked, each to its route (`listerZones` -> `route_zones` `zones`, `lireCommune` -> `route_commune` `communes/*`, `enregistrerNdvi` -> `route_ndvi` `ndvi/*/*`...); not linked, the 3 `session` (`etatSession`, `seConnecter`, `seDeconnecter`), answered at index.php's top. Tests (`tests/api/`): 13 links; not linked, `session`, `nimporte-quoi`, `inconnue` and `` `/api/proprietaires${q}` `` (`proprietaires*`). `callers route_meteo`: `lireMeteo`, then `PageCommune.charger`, `Tableau.chargerSemaine`, `suiviChamp`; `path listerZones zone_json`: 2 steps, through `sends`. `check`: 0 dangling, 0 alert. Build 0.8 s.
- **Not done**: Grid Zero's `sends` (`"cmd"`, `"action"`) stay its extension's: they could be `[keys]` (two kinds of key, so a list) when it asks; the HTTP method (`shortcut:` in `_link_keys`); the frameworks (BACKLOG.md).
