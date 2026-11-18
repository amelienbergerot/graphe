Status: closed
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0021: A test's callback is a node

## What to build

BACKLOG.md (dpe): `test('...', () => { compute(...) })`: the caller is `compute.test.mjs`, not the test. `explain compute` lists 20-odd test files rather than the tests. The callback of `test(...)`/`it(...)` (and `describe`) becomes a node named by its title, contained in its file, and its calls belong to it.

## Acceptance criteria

- [x] `explain f` names the test that calls f, by its title.

## Comments

- The JS reader (`_test`): `test`, `it`, `describe` (none of ours) with a title and a callback make a node of kind `test`, named by its title, held by its file or its `describe`; the callback's calls are its own. Neither `test.only` nor `describe.each` (a shortcut, in the code).
- **dpe**: 601 -> 1140 nodes; `explain compute.mjs::compute` names 73 callers, the tests by their titles (`test/compute.test.mjs: compute : déterministe (deux appels identiques):17, ...`) rather than 20-odd files. 4cast: 413 -> 509 nodes. Grid Zero: nothing more than T-0019's coverage.
