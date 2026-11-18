Status: ready-for-agent
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0023: A PHP file's top-level calls belong to the file

## What to build

BACKLOG.md (4cast): `api/index.php` routes at the top of the file (`route_zones($db, ...)`); the PHP reader reads calls only in bodies, so `explain route_zones` shows no caller. The lines outside any function (and outside any action) call from the file node, as the JS reader does.

## Acceptance criteria

- [ ] A function called at the top of a PHP file has the file as caller.
