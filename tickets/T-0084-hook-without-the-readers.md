Status: closed
Part of: T-0071
Created: 2026-11-27

# T-0084: The hook answers without loading the readers

## What to build

The plugin's hook (T-0077) runs before every Bash, PowerShell and Grep call of the agent, in every project. Measured on 4cast, dpe, grid_zero and graphe (2026-11-27): 0.58 to 0.70 s per call, whatever the graph's size (grid_zero's 4.8 MB graph costs 0.05 s more), and 0.59 s for a `git status` that gets no hint. The cost is the import of `graphe.cli`: 0.47 s, networkx 0.30 s of it, then the readers.

`graphe hook` goes through an entry point that imports nothing of the tool before it knows the command, then a module of its own that imports only the standard library, and `graphe.root` only once the pattern is a name. Every other command runs as before.

## Acceptance criteria

- [x] `graphe hook` imports neither networkx nor a reader; on a command that is no grep, not even `graphe.root` (no git call).
- [x] Every other command, and `graphe.cli.main(["hook"])` (an install whose launcher still names `graphe.cli:main`), behaves as before.
- [x] The per-call time, measured again on the same hosts, in the comments.

## Comments

- 2026-11-27: done. The hook moves to `graphe/hook.py` (the standard library alone; `graphe.root` imported once the pattern is a name), the entry point to `graphe:main` (`graphe/__init__.py`), which imports `graphe.hook` for `graphe hook` alone and `graphe.cli` for every other command; `graphe.cli.main(["hook"])` still answers (an old launcher). A test checks the modules the hook imports. Measured again through Git Bash with the plugin's command, on the same four hosts: 0.25 to 0.32 s on a hint (0.58 to 0.70 before), 0.20 to 0.22 s for a `git status` (0.59): what is left is the launcher and Python's start. After the review of the tests: through `graphe.cli`, `graphe.root` is already imported with the starting directory's ROOT, so the hook calls `root()` again after its chdir (one more git call, on a name only).
