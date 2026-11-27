---
name: graphe
description: Locate code with the `graphe` command before grep or reading files - where X is defined, who calls it, what a change reaches, how A leads to B, which ticket motivated some code, the code behind a text seen on screen.
allowed-tools: Bash(graphe *) PowerShell(graphe *)
---

# graphe

`graphe` is the code graph of the current git repository (the host): what calls what, what cites what. One query costs 2 to 12 times fewer tokens than grep plus reading, and is more exact: grep on `.step(` finds every class's `step`; the graph finds the one caller.

## Locate code

1. Query from inside the host repository:
   - `graphe explain X` - what X calls, what calls X, the documents that cite it. `--source` prints its body; `--all` lifts the truncation.
   - `graphe callers X --depth N` - the reach of a change. Keep N small (1 to 3).
   - `graphe path A B` - how A leads to B; `--undirected` when the direction is unknown.
   - `graphe search PATTERN` - by name, then by displayed texts and comments.
2. Designate X by its name (`step`), `Class.method`, `file::name` (`engine.py::step`), its id, or in GDScript `Script.function` (the constant that preloads the script). A file by its path (`simulation/core/engine.py`). When a name is ambiguous, the answer lists the candidates, each by the text that designates it alone: type that text.
3. The answers list the neighbours one line per file, `file: Class.method:line, ...`, and the tickets by their identifier. Designate the next one as `file::Class.method` (`engine.py::Engine.step`), or a file by its path. `[by name]` on a relation, or `?` after a neighbour, marks a link the reader guessed from the name alone. "+ N calls named `f` the graph could not attribute:" means the graph's callers are not all of them; the lines under it give each cause its count, and the next step:
   - "between K definitions: A.f, B.f" - several definitions bear the name. The candidates are listed when five at most: query the one you mean (`graphe callers B.f`), then grep `.f(` to tell its calls from the others'. Above five, the count only: grep.
   - "on a common name" - a name the language's library uses too (`each`, `get`): a grep returns every use; narrow it to a file or a receiver.
   - "on a receiver of unknown type" - the reader could not tell what `f` is called on: grep `f(`.
   - "to a definition outside the host" - the reader looked where the definition should be (a module or a class of ours, a dependency) and found none: a dependency's, or one of ours set at run time or re-exported. Grep `f(` when you need every call.
4. Read only the lines the answer points to.

The graph rebuilds itself when the code or the tool is newer than it: trust the answer. Done when the answer names the code you need, or when it falls short (next section).

The readers: Python, GDScript, PHP, JavaScript/TypeScript/Svelte, Go, Rust, Java, C/C++, C#, Ruby, Swift, Kotlin..., and the Markdown documents (a document cites code between backticks, and other documents by identifier, `T-0012`). In a host whose code no reader takes yet, use grep and read the files. Outside the graph too: dynamic calls (`getattr`, stored callbacks), tests a host excludes, `.toml`, shaders - grep is the tool there.

A new host: `graphe install` sets the git hooks that rebuild it and ignores its `graphe/` output folder. `graphe check` gives each contribution's coverage.

## When the graph falls short

Grep and read the files.

A gap in the tool itself (a relation the graph should have known, an answer that misled you): tell the user in one line, what you looked for and what the graph answered. The user may report it on the repository's issues, https://github.com/amelienbergerot/graphe/issues; the report is the user's to file. A gap the language's missing reader explains (no reader for that host yet) is already known: skip it.
