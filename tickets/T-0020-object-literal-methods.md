Status: ready-for-agent
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0020: The methods of an object literal are nodes

## What to build

BACKLOG.md (dpe, 4cast): a page object (`return { async saisir(id, v) {...} }`, dpe's UI tests, about 150 calls) or a test harness (`faux.de()`, 4cast, 31 sites `ours?`) has methods that are not nodes; `p.saisir()` is `member`, linked to nothing. Each method of an object literal at the top of a function or a module becomes a node, and `x.m()` is linked to it by the name as for class methods.

## Acceptance criteria

- [ ] A method of an object literal returned by a function is a node; `p.m()` calls it (INFERRED when the name is unique).
- [ ] dpe's and 4cast's coverage noted here.
