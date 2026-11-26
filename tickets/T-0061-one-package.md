Status: ready-for-agent
Part of: T-0048
Created: 2026-11-26

# T-0061: One `graphe` package

## What to build

The seven top-level modules become one package imported as `graphe` (T-0057), so they no longer collide in a user's environment: `cli` (today's command module), `core`, `root`, `python`, `godot`, `js`, `generic`, the `graphe_` prefix dropped, an empty package init, absolute imports. The command's entry point is the `cli` module's `main`. Behaviour unchanged: the same graph, the same answers.

## Acceptance criteria

- [ ] `graphe` (every subcommand) works as before from an editable install; the 89 tests pass, their imports and their command runner moved to the package.
- [ ] A local extension is still loaded by path and may import `graphe.*`; the public contract stays `contribute(project)`, `Project` and the shape of the nodes and links, nothing else.
- [ ] The docs naming a module (the README, the contribution contract, the readers) name the new modules.
- [ ] Grid Zero follows in its own commit: its extension's two imports read from `graphe.core` and `graphe.godot`; its `graphe build` and reference test pass.
- [ ] The git hooks and the layout fixture unchanged.
