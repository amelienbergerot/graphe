Status: closed
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0023: A PHP file's top-level calls belong to the file

## What to build

BACKLOG.md (4cast): `api/index.php` routes at the top of the file (`route_zones($db, ...)`); the PHP reader reads calls only in bodies, so `explain route_zones` shows no caller. The lines outside any function (and outside any action) call from the file node, as the JS reader does.

## Acceptance criteria

- [x] A function called at the top of a PHP file has the file as caller.

## Comments

- The PHP reader: the lines outside every body (a function's or an action's, signature included) make one more body, the file's: their calls are the file's.
- **4cast**: 1110 -> 1127 links; `explain route_zones`: called by `api/index.php`.
- **Grid Zero** (snapshot to retake at the end of the batch): 62 links more, its pages that call their library at the top of the file (`web_admin_index -> web_lib_gabarit_gz_debut_de_page`, ...), 2 links that gain `calls` (`web_admin_retours -> web_admin_retours_h`, `web_api_scenarios -> web_api_scenarios_gz_repondre`); the communities are cut again: 4391 nodes change community, x, y.
- Grid Zero's snapshot retaken once for the batch, on the user's decision (Grid Zero 31a1317).
