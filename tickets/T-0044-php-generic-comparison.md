Status: closed
Type: task
Created: 2026-11-19

# T-0044: PHP read by the generic reader, compared with the PHP reader on 4cast

## What to build

A PHP entry of the generic reader, data only (its grammar, our queries in the capture convention, its common names), is built and compared on 4cast with the existing PHP reader, which reads by patterns. The entry is not put in the readers' registry: the PHP reader stays the one hosts get. The ticket ends on the user's decision: replace the PHP reader by the generic entry only if the generic one does at least as well, or keep it. BACKLOG.md: "PHP's pattern reader may be worse than the generic one".

## Acceptance criteria

- [x] The PHP `Language` is data only; its grammar pinned; a test at `read(language, file, source)` on a snippet: functions, methods `Class.method`, a top-level call owned by its file (as the PHP reader does since T-0023).
- [x] Both readers run on 4cast's PHP: nodes, links by confidence, `check` coverage (linked, by name, not attributed, external), and three `explain` or `callers` queries compared with grep, side by side in this ticket's comments. protobuf's PHP as a second measure.
- [x] What each reader finds that the other misses, named with examples.
- [x] The user's decision noted in this ticket, and the BACKLOG.md entry settled or updated; if the generic entry replaces the PHP reader, that change is its own ticket.
- [x] The existing hosts' graphs unchanged; the tests pass.

## Blocked by

None (can start immediately).

## Comments

- **The entry** (2026-11-19): `PHP` in `graphe_generic.py`, data only, not in `READERS`; `tree-sitter-php` 0.25.2 pinned, its grammar with the HTML (`language_php`), so `<p>aide(x)</p>` outside `<?php ?>` is no call (the PHP reader's `shortcut:`). Classes, interfaces, traits and enums are `@class`; a method without a body is none (as Java's); `x->m()`, `x?->m()`, `X::m()` are sends; `new C`, `extends`, `implements` and a trait's `use` are references by the last name. Tested at `read()` on a snippet (functions, `Zone.__construct`, two top-level calls owned by the file, no call from the HTML). One rule PHP needed, a data flag `apart`: a bare call is linked to a function only, a send to a method only. Without it, on protobuf, 219 bare calls to PHP's built-ins went to its methods of that name (`count()` 185, `substr()` 19, `unpack()` 7, `pack()` 4, `key`, `current`, `next`); tested at `contribute()`. Beyond the ticket's "data only": a flag, but a rule of `contribute()` it turns on, so ADR 0003 is amended (as for `tolerant` and `erased`) and `docs/readers.md` says it. Common names: none. Every linked send that bears a standard name on protobuf is one of its own methods (`$any->pack`, `getFile`), PHP's library being functions; 4cast and Grid Zero define no method, so none of their sends can be linked.
- **4cast** (`d224d6c`, 11 PHP files read, `.scratch` excluded), both readers in one build each, side by side:

  | | pattern | generic |
  |---|---|---|
  | all nodes / links | 509 / 1129 | 510 / 1131 |
  | PHP nodes | 11 files, 35 functions | 11 files, 35 functions, 1 class |
  | `calls` (distinct pairs, by (file, name)) | 81 `EXTRACTED` | 81 `INFERRED`, the same 81 |
  | `references` | 0 | 1 (`amont` -> `ErreurAmont`) |
  | `check` php | no section (no sites) | 448 sites: 153 `ours?`, 295 `external`, 0 ambiguous, 0 common |

  The confidences differ by label only: both link by name, the PHP reader calls it `EXTRACTED`. The PHP reader gives no sites, so `check` has no coverage of it to compare; the generic's 153 `ours?` sites (linked by name) are the 81 pairs both readers link, none not attributed (0 `ambiguous`, 0 `common`), 295 `external` (`$db->prepare`, `preg_match`). The ids change (`api_lib_cache_par_cache` -> `api_lib_cache_php_par_cache`).
- **Three queries against grep** (bytes; grep by word over the `.php`, without the `function` line):
  - `callers repondre`: 21 callers, 510 bytes, identical for both; grep 67 lines in 7 files, 5827 bytes.
  - `explain par_cache`: 9 callers both, 810 bytes (pattern) and 824 (generic: `[by name]`); grep 11 lines in 3 files, 1275 bytes.
  - `explain ErreurAmont`: pattern "no node"; generic the class, `references` from `amont:17` (its two `throw new`), 269 bytes; grep 7 lines in 3 files, 551 bytes. The generic misses its three `catch (ErreurAmont $e)` (a caught type is no reference, as Java's).
- **Grid Zero** (`31a1317`, 23 PHP files read), the side the decision turns on:

  | | pattern | generic |
  |---|---|---|
  | all nodes / links | 4231 / 16356 | 4223 / 16325 |
  | PHP nodes | 23 files, 62 functions, 8 actions | 23 files, 62 functions |
  | `calls` (distinct pairs) | 127 | 114, 100 in common |
  | `dispatches` | 2 | 0 |
  | the extension's `sends` to the actions (T-0009) | 6 | 0 |

  `web/api/scenarios.php`'s `case 'liste':` and the seven others have no node in the generic graph: their 27 calls (`noter` -> `gz_votant`) become 14 calls of the file, the 2 `dispatches` (`signaler` -> `noter`) are lost, and the extension's 6 `sends` find no action (its `action_id` builds on the PHP reader's file id, without `_php`), and 2 `cites` of the actions (`defi_classement` -> Grid Zero's T-0310, `liste` -> T-0358) fall to the file, which cites them already: 45 links lost, 14 gained, the 31 of the table. `check`: 611 sites, 185 `ours?`, 426 `external`.
- **protobuf** (`e08e1e7`, 158 `.php`), both contributions without a build: the pattern reader 5 functions (the top-level ones; it reads no method), 9 actions that are protobuf's own `switch` arms, 4 calls; the generic 156 classes, 1723 methods, 5 functions, 1047 `calls` pairs and 292 `references`, 0 dangling; 7687 sites: 1696 `ours?`, 1343 `ambiguous` (`value` 104, `appendHelper` 84, `getType` 76: generated getters across messages), 4648 `external` (PHPUnit's `assertSame` 876, `isset` 316, `count` 185). `php/tests/generated_previous/Previous/readonly.php` does not parse (`class readonly`, a keyword since PHP 8.1): skipped, the PHP reader read it (no function).
- **What each finds that the other misses**:
  - the PHP reader alone: the `case 'x':` actions and their `dispatches` (Grid Zero's 8 actions, the 6 `sends` of its extension, the 2 tickets they cite); a file that does not parse is read (protobuf's `readonly.php`, no function in it);
  - the generic alone: classes, interfaces, traits, enums and their methods (`Class.method`), so protobuf's PHP (1723 methods against none); `new`, `extends`, `implements` (4cast's `ErreurAmont`); an indented function (the PHP reader reads `^function` at column 0); no call from a page's HTML (no such false call on the three hosts: on 4cast and Grid Zero the `calls` differ only by the actions).
- **The decision** (2026-11-19, the user): the generic entry replaces the PHP reader, its `case 'x':` actions kept, in its own ticket, T-0045. BACKLOG.md's entry settled into "PHP's pattern reader reads no class nor method", pointing to T-0045; the entry's actions `shortcut:` too.
- **The existing hosts**: the entry is not in `READERS`, so no host's graph moves: Grid Zero's reference test (`graphe_reference.py comparer`), identical; 4cast `check`, 0 dangling with the reinstalled tool. The tests pass (86), ruff clean. The `graphe` tool reinstalled (`uv tool install -e`), its environment now holding the grammar.
- **Not checked**: Linux and macOS wheels of the grammar; dpe and cadastre-poc carry no PHP.
- **The review** (2026-11-19, standards and spec): `apart` amended into ADR 0003 and said in `docs/readers.md`'s generic section (its switches, its links, adding a language); its filter moved under the existing `@call`/`@send` branch, on the function ids; the empty common names justified in the code; T-0045 to amend ADRs 0002 and 0003; the coverage and Grid Zero's links worded as measured (the 2 `cites`). Left as it is: the grammar imported with the others at the top of the module, whatever the registry holds (the Linux and macOS wheels not checked, as every grammar's).
