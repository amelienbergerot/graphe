# The `contribute(project)` contract

Readers and local extensions have one interface only: a function `contribute(project)` that returns a **contribution**. The schema below is the contract. networkx is not part of it: an extension only ever sees dictionaries and lists.

## Assembly

1. The readers (`python`, `godot`, `php`, `js`, `go`, `rust`, `java`, `c`, `csharp`, `ruby`: docs/readers.md) contribute, then the extensions declared `with_readers`. Their nodes come in together, sorted by id, after the takeovers (`takeovers`).
2. The core enriches the graph: extents, comments, displayed texts, module variables, documents, etc. A displayed text is the only group of the `displayed_text` pattern of `graphe.toml` (for example `'\btr\("([^"]*)"'`); without a pattern, the core looks for none. The documents are the host's Markdown files, or those that the `[documents] patterns` list designates (like `exclude`). One whose name starts with an identifier (`[documents] identifier`, a regular expression, `\bT-\d{4}\b` by default) is a ticket, with id `ticket_<identifier>`; the others are `document`s.
3. The other local extensions contribute one by one, in the order in which `graphe.toml` declares them. Each sees the graph the previous ones left.

A link one end of which is missing from the graph creates no node. It is counted as **dangling** (`dangling`): `graphe check` then fails, and `build` prints the first ones.

## Declaring a local extension

In the host's `graphe.toml`, one table per extension, in assembly order:

```toml
[[extensions]]
path = "tools/graphe_grid_zero.py"     # relative to the host's root
with_readers = true                   # optional: contribute with the readers, before the core
# the other keys of the table: the extension's configuration (project.configuration)
```

A `with_readers` extension contributes like a reader: it sees the empty graph, and its nodes go through the core, which gives them an end, a comment and, for a body, its lines. That is the case of a body cut out of another, like the branch of a command in the function that dispatches. It alone may return takeovers.

An extension after the core sees what the core added: the end (`end`) of each body, its texts (`texts`), the documents. The same file may be declared twice, with and without `with_readers`: it knows which of the two contributes through `project.configuration["with_readers"]`. Only one of the two returns `sites`, otherwise the second replaces the coverage of the first.

An extension that adds nodes outside the code (hints, a journal) gives them their own community through `graphe.toml`, as the core does for its tickets, its values and its documents:

```toml
[communities]
separate = { hint = "hints" }       # kind -> community name, after the tickets, the values and the documents
strip_prefixes = ["src/"]           # optional: removed from a community's name
```

The file is a Python module that defines `contribute(project)`. An extension that is declared but not found stops the build, with a message that gives its path. So does a module without `contribute`.

The extension's file is a host file like any other: the Python reader reads it too, unless `exclude` excludes it.

## `project`

| Attribute | What it is |
|---|---|
| `project.root` | The host's root (`Path`). |
| `project.files(suffix)` | The host's files that end with `suffix` (`".py"`), sorted. These are the ones git tracks, plus untracked files that are not ignored, minus `exclude`. |
| `project.configuration` | The section of the one who contributes. For a reader, it is the table that bears its name (`[godot]`). For an extension, it is its `[[extensions]]` table. |
| `project.graph` | The graph already assembled, in the form `{"nodes": {id: node}, "links": [assembled link]}`. It is a copy: changing it changes nothing in the graph. The readers receive it empty. |
| `project.checking` | True under `graphe check`. A reader may then add its costly checks, like the recount of GDScript calls. |

An **assembled link** has a single copy per pair of nodes: `source`, `target`, `relations` (a sorted list), `confidence`, `locations` (`"file:line"`) and `contexts`. It is the form of the links of `graphe.json`.

## The contribution

It is a dictionary. Each key is optional.

```python
{"nodes": [...], "links": [...], "sites": [...], "takeovers": [...]}
```

### A node

| Field | Required | What it is |
|---|---|---|
| `id` | always | A unique identifier in the graph (`outils_aider`). |
| `label` | new node | What `explain` displays at the head of its answer (`aider()`). |
| `kind` | new node | `file`, `function`, `method`, `class`, `field`, `command`, `action`, `signal`, … or a kind specific to the extension. |
| `source_file` | new node | The path relative to the root, with `/`. |
| `source_location` | new node | The line, in the form `"L12"`. |
| `name` | new node | The name by which the node is designated (`aider`, `Class.method`), and shown among the neighbours of another. |
| others | no | Free attributes. The core reads some: `texts` (a list, shown by "displays:"), `notes` (a comment), `end` (the last line, for `--source`). |

A node returned with an id that already exists **merges** its attributes into that node: only `id` is then required, and each attribute returned replaces the old one. A new node lacks a required field? The build stops, with a message that names the contributor and the id.

### A link

All fields are required.

| Field | What it is |
|---|---|
| `source`, `target` | The ids of both ends. |
| `relation` | `calls`, `contains`, `imports`, `reads`, `writes`, `cites`, `sends`, `dispatches`, … or a relation specific to the extension. `callers` follows only the call relations (`CALLS`, in `graphe.py`). |
| `confidence` | `"EXTRACTED"` (a sure link) or `"INFERRED"` (a link made by the name alone). Between two nodes, an `EXTRACTED` link wins. |
| `source_file`, `source_location` | The location of the link (`"L12"`). |
| `context` | A word about the link (the alias of an import, the name of an order), or `""`. |

Two links between the same nodes make only one, which keeps all their relations and all their locations.

### A takeover (`takeovers`)

Only for a `with_readers` extension. The links that leave `from` from the lines `lines` of `source_file` now leave from `to`. A takeover touches only the readers' links, before assembly. Takeovers apply in order: a takeover sees the previous ones. For a branch in a branch, return the outer one first.

| Field | What it is |
|---|---|
| `from`, `to` | The node that loses the links, the one that takes them. |
| `source_file` | The file of the lines, as in a link. |
| `lines` | `[start, end]`, bounds included. |

### A coverage site

A site is a place in the code that the contributor has classified. It is for example a call, and what became of it.

| Field | What it is |
|---|---|
| `file`, `line`, `text` | Where the site is, and what it says (`runner.set_dispatch`). |
| `name` | The name called, where relevant. |
| `verdict` | Optional: the classification (`ours`, `ours?`, `ambiguous`, `external`, `engine`, …). |
| `alert` | Optional: why the site is a defect ("not linked to the name of one of our functions"). |

If a contribution has the `sites` key, even empty, `graphe.json` carries its coverage: `coverage[<who>]` counts its verdicts. `<who>` is the name of the reader or the path of the extension. `graphe check` shows, for each contribution, the count of each verdict, its most frequent texts and each alert. It fails if there is an alert or a dangling link.
