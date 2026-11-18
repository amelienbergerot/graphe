---
name: graphe
description: Locate code with the `graphe` command before grep or reading files - where X is defined, who calls it, what a change reaches, how A leads to B, which ticket motivated some code, the code behind a text seen on screen. Also use when the graph falls short and the gap goes in the tool's backlog.
---

# graphe

`graphe` is the code graph of the current git repository (the host): what calls what, what cites what. One query costs 2 to 12 times fewer tokens than grep plus reading, and is more exact: grep on `.step(` finds every class's `step`; the graph finds the one caller.

## Locate code

1. Query from inside the host repository:
   - `graphe explain X` - what X calls, what calls X, the documents that cite it. `--source` prints its body; `--all` lifts the truncation.
   - `graphe callers X --depth N` - the reach of a change. Keep N small (1 to 3).
   - `graphe path A B` - how A leads to B; `--undirected` when the direction is unknown.
   - `graphe search PATTERN` - by name, then by displayed texts and comments.
2. Designate X by its name (`step`), `Class.method`, `file::name` (`engine.py::step`), its id, or in GDScript `Script.function` (the constant that preloads the script). When a name is ambiguous, the answer lists the candidates: pick one by `file::name`.
3. Read only the lines the answer points to.

The graph rebuilds itself when the code or the tool is newer than it: trust the answer. Done when the answer names the code you need, or when it falls short (next section).

The readers: Python, GDScript, PHP, and the Markdown documents (tickets cite code between backticks and each other by identifier). In a host whose code no reader takes yet, use grep and read the files. Outside the graph too: dynamic calls (`getattr`, stored callbacks), tests a host excludes, `.toml`, shaders - grep is the tool there.

A new host: `graphe install` sets the git hooks that rebuild it and ignores its `graphe/` output folder. `graphe check` gives each reader's coverage.

## Note a gap

Each time the graph does not answer and you search by hand (grep, reading), add an entry to the tool's single backlog, `E:/dev/graphe/BACKLOG.md`, under "Open", as soon as the gap appears:

```markdown
- **What the graph could not tell, in one line.** (Host, YYYY-MM-DD)
  What you were looking for, what the graph answered, how you found it,
  and the improvement that would have avoided the search.
```

- One entry per gap: when it is already noted, extend that entry.
- Commit it in the `E:/dev/graphe` repository, apart from the host's work.
- A gap the language's missing reader explains (no reader for that host yet) is already known: skip it.
