Status: closed
Part of: T-0071
Created: 2026-11-27

# T-0085: The hook names the nodes of a name that designates several

## What to build

The hook's line (T-0077) says `graphe explain X` "gives its definition". When X designates several nodes, `explain X` answers "designates N nodes; pick one" instead, and the agent needs a second call: `ouvrir` on 4cast (2 nodes), `stocke` on dpe (6), measured 2026-11-27.

When the name designates several nodes, the line says how many and gives the designation of each, the one `explain` takes (`Class.method` when that is unique, else `file::name`), five at most, then how many more. One node: the line as before.

## Acceptance criteria

- [x] A name defined in two files gets one line naming both `file::name`, each of which `graphe explain` answers.
- [x] A name defined once keeps T-0077's line.
- [x] Above five, five are named and the rest counted.

## Comments

- 2026-11-27: done. `hook.hint`: one node, T-0077's line; several, their count and their designations, sorted, `Class.method` when no other node bears that name, else `file::name`, five then "and N more". On the hosts: `ouvrir` on 4cast names `src/App.svelte::ouvrir` and `src/lib/sentinel.ts::ouvrir`, `stocke` on dpe five of its six `file::ouvrir.stocke`, `__init__` on grid_zero five of its 24 `Class.__init__`; `graphe explain` answers each designation named (rc 0).
