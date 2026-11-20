Status: closed
Type: task
Created: 2026-11-19
Blocked by: T-0044

# T-0045: The generic entry replaces the PHP reader, its actions kept

## What to build

The readers' `php` entry becomes the generic reader's `PHP` (T-0044), and `graphe_php.py` goes, as the user decided on T-0044's comparison. The PHP reader's `case 'x':` actions are kept: a node per action (kind « action »), owning its body's calls, two `case` in a row leading one to the next (`dispatches`), so that Grid Zero's 8 actions in `web/api/scenarios.php` and the 6 `sends` of its T-0009 extension survive. The node ids change (`api_lib_cache_par_cache` -> `api_lib_cache_php_par_cache`): what builds on them (`graphe_php.action_id`, Grid Zero's extension, its reference test) follows.

## Acceptance criteria

- [x] `READERS["php"]` is the generic reader's `PHP`; `graphe_php.py`, its tests and its mentions go, or move to the generic reader.
- [x] A `case 'x':` is an action node, its calls its own, `dispatches` to the next `case` when it has no body; tested at `read()` or `contribute()`.
- [x] Grid Zero: its 8 actions, 2 `dispatches` and the extension's 6 `sends` as before; its reference test (`graphe_reference.py comparer`) updated for the new ids only.
- [x] 4cast: the same 81 `calls` pairs (T-0044), the class `ErreurAmont`.
- [x] The readers document has PHP's section (suffixes, grammar and version, nodes, links and confidence, `apart`, `shortcut:` limits, sample hosts); the README's "Tested on" table and protobuf's PHP column; `docs/contribution.md`, `--help` and the skill name the reader.
- [x] ADR 0002 ("the PHP (patterns) reader stays as it is") and ADR 0003 (the languages it serves) amended.
- [x] The tests pass.

## Blocked by

T-0044.

## Comments

- **The reader** (2026-11-20): `READERS["php"]` is `graphe_generic.PHP`; `graphe_php.py` deleted, its test moved to `tests/test_generic.py` at `contribute()` (its fixture, the brace on its own line included). The actions are a new capture, `@action` (`case 'x':` of a single-quoted word, as the PHP reader's): a definition named as it is, in no class, id `<file>_action_<name>`, label its bare name, the file's; no call reaches it (not among the callables, so `liste()` and `$x->liste()` stay `external`); its body's calls its own. One holding nothing past its name leads to the next (`dispatches`, `EXTRACTED`, no site), a use `dispatches` that `read()` emits and `contribute()` links in the file. `graphe_php.action_id` had no caller left but its test: gone. Grid Zero's extension finds the actions by kind and name, so it needs no change.
- **A `case` in a function is no action** (beyond the PHP reader, which read only `^function`): on protobuf the 9 `case 'x':` of `Message.__debugInfo` and conformance's `doTest` would have taken 7 `calls` pairs from their methods (`__debugInfo` -> `Value.getBoolValue`...), and `path` through them. Not an entry point's router: `read()` drops an `@action` with a definition open (a function, a method, or an action: a nested switch's `case` leaves its calls to the outer action); protobuf's PHP is then T-0044's generic measure exactly (1047 `calls` pairs, 292 `references` pairs, 1696 `ours?`, 1343 `ambiguous`, 4648 `external`), 0 actions where the PHP reader made 9.
- **Grid Zero** (`31a1317`, `graphe_reference.py comparer`, then each id of a PHP file `f` mapped to `f_php`): nodes 93 renamed, none lost or gained, every field identical; links 235 renamed, none lost or gained; of the links' fields, 127 `locations` (a call's own line where the PHP reader gave its body's first: `web/api/scenarios.php:93` -> `:118`) and 125 `confidence` (`EXTRACTED` -> `INFERRED`, by name; the 2 others merged with a sure link). `coverage` gains `php`: 185 `ours?`, 426 `external`. The communities move: Louvain (`seed=0`) runs over the nodes sorted by id, and the ids changed (46 -> 47 groups), the weighted graph being the same. The 8 actions, their 27 `calls`, the 2 `dispatches`, the extension's 6 `sends` and the 2 `cites`, as before. No file skipped. The snapshot retaken in Grid Zero (`8bec293`, on `moonshot`), `comparer` then identical. Beyond the ids, as listed: the user accepts the lines, confidence, coverage and communities, or asks back.
- **4cast** (`d224d6c`): 510 nodes, 1131 links; 11 files, 35 functions, 1 class (`ErreurAmont`, `references` from `amont`); the same 81 `calls` pairs, `INFERRED`; `check` php 153 `ours?`, 295 `external`, 0 dangling: T-0044's generic column. No file skipped.
- **protobuf** (`e08e1e7`): its one skipped file as in T-0044 (`readonly.php`), now named at each build (docs/sample-hosts.md).
- **The documents**: `docs/readers.md` (the table, `@action` in the capture convention, the nodes and links, PHP's section, PHP out of the dedicated readers), `--help`, the README's protobuf row (158 `.php` among its files), docs/sample-hosts.md, ADR 0002 and 0003 amended (`@action` is code written once, any language's), BACKLOG.md's entry settled. `docs/contribution.md` and the skill already named `php` and PHP: unchanged.
- **The build** (protobuf, median of three, this machine today): 74.3 s with T-0045, 78.3 s at `7c10dbb` (the PHP reader); the README's 62.7 s, measured on T-0043's day, left as it is: the generic PHP costs nothing measurable.
- **The review** (2026-11-20, standards and spec): fixed: a `dispatches` only to the case right after the empty one (`next_named_sibling`, comments skipped), so not past a `default:` or a `case "x":` nor into the next switch, where the PHP reader's carried on (marked sure, it would have lied); a nested switch's `case` no action; an action named by a word in any script (`\w`, `case 'défi':`, as the PHP reader's), where the query had ASCII; no `x dispatches x`; tested at `contribute()`. "Every link a use makes is `INFERRED`" reworded (`dispatches` is sure) in `docs/readers.md` and the module's docstring; PHP's limits in BACKLOG.md; `READERS` one entry a line; the README row. Left: `@action` special-cased in `read()` and `contribute()` (a kind of its own, as ADR 0003's amendment says), `dispatches` carried as a `Use` (a `read()` result of its own for one relation would cost more); a case on one line with its body, or in an `endswitch`, an action where the PHP reader's was not (documented).
- **Not checked**: Linux and macOS (the grammar's wheels, as T-0044); a host whose router's `case` is in double quotes.
