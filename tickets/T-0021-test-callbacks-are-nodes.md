Status: ready-for-agent
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0021: A test's callback is a node

## What to build

BACKLOG.md (dpe): `test('...', () => { compute(...) })`: the caller is `compute.test.mjs`, not the test. `explain compute` lists 20-odd test files rather than the tests. The callback of `test(...)`/`it(...)` (and `describe`) becomes a node named by its title, contained in its file, and its calls belong to it.

## Acceptance criteria

- [ ] `explain f` names the test that calls f, by its title.
