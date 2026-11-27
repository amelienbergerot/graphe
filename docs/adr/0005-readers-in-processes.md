# The readers in processes of their own, not threads

A build runs the readers that have files at once, one process each (`concurrent.futures.ProcessPoolExecutor`, the standard library), when the readers beside the largest have 250 files or more; otherwise, and for the readers without files, in the build's process, as before (T-0088). Their contributions are taken in the order of `READERS`, so the graph is the same, and the first error in that order stops the build with its own message. The local extensions, the core and the communities stay in the build's process, one after the other.

Processes, because threads gain nothing: py-tree-sitter 0.26.1 holds the GIL while it parses and while a `QueryCursor` matches (4 to 8 threads: x0.85 to x1.02, measured 2026-11-27), and the Python reader's walk of the `ast` is Python.

Two rules follow, for any reader of this repository:

- **A reader is sent by its name, its contribution by value.** The worker (`graphe.readers.run_reader`) looks the reader up in `READERS`, so a reader need not pickle (a `functools.partial` over a `Language` holding grammars does not have to); its contribution comes back pickled, so it holds dictionaries, lists, strings and numbers only. A worker builds its own `Project`, whose graph is empty: the readers receive it empty (docs/contribution.md).
- **A reader's module stays light, and fixes nothing at run time.** On Windows a worker is a new interpreter that imports `graphe.readers` and the readers, and nothing the build's process set after its imports (a patched module, a changed directory). `graphe.readers` imports neither networkx nor `graphe.cli`: networkx alone took 0.86 s of `graphe.cli`'s 1.3 s import, and moving the readers out of `graphe.cli` cut a pool's cost on a small host from 1.5 s to 0.64 s (measured under load).

The threshold is a `shortcut:` in `cli.py`, counted in files: on libsignal's Rust and Java, 200 files each lost 0.26 s, 300 each gained 0.4 s. A reader that is slow on few files (Godot's engine) is not weighed.

A reader that raises in a worker stops the build once the readers still running have finished: the build waits for them, where a serial build stopped at the first error. The order of their lines on stderr is no longer guaranteed.

## Options set aside

- Threads: the GIL, measured above.
- A process per file, or per batch of a reader's files: a reader links its files together (a registry of names, the imports), so its files would have to be read apart and linked after, a change of every reader for a gain the largest reader bounds anyway.
- A setting to turn it off: the graph is the same either way, and a small host stays serial by the threshold.
