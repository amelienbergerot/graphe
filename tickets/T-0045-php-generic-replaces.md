Status: needs-triage
Type: task
Created: 2026-11-19
Blocked by: T-0044

# T-0045: The generic entry replaces the PHP reader, its actions kept

## What to build

The readers' `php` entry becomes the generic reader's `PHP` (T-0044), and `graphe_php.py` goes, as the user decided on T-0044's comparison. The PHP reader's `case 'x':` actions are kept: a node per action (kind « action »), owning its body's calls, two `case` in a row leading one to the next (`dispatches`), so that Grid Zero's 8 actions in `web/api/scenarios.php` and the 6 `sends` of its T-0009 extension survive. The node ids change (`api_lib_cache_par_cache` -> `api_lib_cache_php_par_cache`): what builds on them (`graphe_php.action_id`, Grid Zero's extension, its reference test) follows.

## Acceptance criteria

- [ ] `READERS["php"]` is the generic reader's `PHP`; `graphe_php.py`, its tests and its mentions go, or move to the generic reader.
- [ ] A `case 'x':` is an action node, its calls its own, `dispatches` to the next `case` when it has no body; tested at `read()` or `contribute()`.
- [ ] Grid Zero: its 8 actions, 2 `dispatches` and the extension's 6 `sends` as before; its reference test (`graphe_reference.py comparer`) updated for the new ids only.
- [ ] 4cast: the same 81 `calls` pairs (T-0044), the class `ErreurAmont`.
- [ ] The readers document has PHP's section (suffixes, grammar and version, nodes, links and confidence, `apart`, `shortcut:` limits, sample hosts); the README's "Tested on" table and protobuf's PHP column; `docs/contribution.md`, `--help` and the skill name the reader.
- [ ] ADR 0002 ("the PHP (patterns) reader stays as it is") and ADR 0003 (the languages it serves) amended.
- [ ] The tests pass.

## Blocked by

T-0044.

## Comments
