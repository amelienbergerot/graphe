Status: closed
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0020: The methods of an object literal are nodes

## What to build

BACKLOG.md (dpe, 4cast): a page object (`return { async saisir(id, v) {...} }`, dpe's UI tests, about 150 calls) or a test harness (`faux.de()`, 4cast, 31 sites `ours?`) has methods that are not nodes; `p.saisir()` is `member`, linked to nothing. Each method of an object literal at the top of a function or a module becomes a node, and `x.m()` is linked to it by the name as for class methods.

## Acceptance criteria

- [x] A method of an object literal returned by a function is a node; `p.m()` calls it (INFERRED when the name is unique).
- [x] dpe's and 4cast's coverage noted here.

## Comments

- The JS reader (`_members`, shared with the classes): the methods of an object literal returned by a function (`return {...}`, `() => ({...})`, `const p = {...}; return p`) are nodes `f.m`, held by f; a module's `const outils = {...}` is a node of kind `object`. A variable assigned `new C()` or `[await] f()` takes C's or f's methods (`_typed`, a scope's own, the inner hiding the outer): `p.saisir()`, `faux.de()` are EXTRACTED. An object's methods are never linked by the name alone: dpe's fake objects define `click`, `getItem`, which the DOM's calls would take (tried: 47 `ours?` and 72 more `ambiguous`, all wrong).
- **dpe**: `ours` 2425 -> 2658, `member` 2140 -> 1907, `ours?`, `ambiguous` 0. **4cast**: `ours?` 31 -> 0, `ours` 627 -> 658 (`faux = new FauxAmont()`). Grid Zero: nothing more than T-0019's coverage.
- `tests/test_graphe.py`: `b = new Builder(); b.build()` was INFERRED, the test said so; now EXTRACTED.

