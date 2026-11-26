# graphe

The code graph of a host project: what calls what, what cites what. `graphe --help` lists the commands.

## Why

An agent that navigates code (or a person) finds its way with grep, then reads files to sort out what grep matched. Grep matches text: `.step(` finds the `step` of every class, plus comments and strings. Graphe reads the code once, links each call to its definition, and answers a question about a function in a few hundred bytes: what it calls, what calls it, and the tickets that cite it. One query costs 2 to 12 times fewer tokens than grep plus reading ([Tested on](#tested-on)), and it is more exact.

It also links code to its documents. A Markdown ticket that names a function between backticks cites it, so `explain` says which tickets motivated some code. A text shown on screen (the `displayed_text` pattern of `graphe.toml`) leads back to the function that displays it. A key both ends share, such as a route the front requests and the back answers, links them (a *keyed link*, `[keys]` of `graphe.toml`), where no name in the code does.

It says where it stops. A link guessed from the name alone is marked `[by name]` or `?`. When some calls cannot be attributed (a receiver of unknown type, a name several classes bear), the answer says so: "+ N calls named `f` the graph could not attribute: grep them".

```
$ graphe explain assemble
assemble()  [function]  src/graphe/cli.py:223-254

what it calls:
  calls (5)
    src/graphe/cli.py: _declared_extensions:153, _extension:157, _insert:174, _take_over:207, _sorted:263
  cites (2)
    T-0007, T-0008

what calls it:
  calls (2)
    src/graphe/cli.py: build:408, check:848
  names (3) [by name]
    T-0012, T-0025, T-0034
```

## What it reads

| How | What |
|---|---|
| Through imports and types (sure links) | Python, JavaScript, TypeScript, Svelte (script and markup), GDScript (Godot) |
| By name (the generic reader, `[by name]` links) | Go, Rust, Java, Kotlin, C, C++, C#, Ruby, Swift, PHP |
| Documents | Markdown: tickets and documents, and what they cite |
| Frameworks | None specifically: a front-to-back link (a route the front requests and the back answers) through `[keys]` of `graphe.toml` |
| Not read | `.jsx`, `.tsx`, Vue |

Each language in detail, with its suffixes: [docs/readers.md](docs/readers.md).

## Install

The same commands on Windows, macOS and Linux, with [uv](https://docs.astral.sh/uv/) (it fetches the Python graphe needs):

```
uv tool install graphe-code
```

The command is `graphe`. If `graphe-cli` (a CLI for the Graphe API) already installed a `graphe` command, uv refuses to replace it without `--force`.

The Claude Code skill, which teaches the command to the agent in every project, is a plugin; this repository is its marketplace:

```
claude plugin install graphe --marketplace amelienbergerot/graphe
```

Without an allow rule, each `graphe` query asks for approval (and a headless `claude -p` falls back to grep): add `Bash(graphe:*)` and `PowerShell(graphe *)` to `permissions.allow` in `~/.claude/settings.json`.

Another agent: copy the [`skills/graphe/`](skills/graphe) folder where that agent reads its skills (the Agent Skills format).

## First graph

From inside a git repository (graphe reads the files git tracks):

```
cd my-project
graphe install           # the git hooks that rebuild the graph after a commit, merge or checkout; graphe/ git-ignored
graphe explain main      # any function of the project: the first query builds the graph
```

No configuration is needed. A `graphe.toml` at the repository's root is optional; every key in it is too:

```toml
exclude = ["vendor", "**/fixtures"]       # folders graphe does not read
displayed_text = '\btr\("([^"]*)"'    # the call that shows a text on screen, the text in its group

[keys]                                    # a link from the code that names a key to the code that answers it
names = 'api\("([^"]+)"'                 # the front's api("zones")
answers = '"/api/([^"]+)"'                # the back's "/api/zones"
```

Every key, and the local extensions: [docs/contribution.md](docs/contribution.md).

A gap in the graph (a call it should have linked, a language it misreads) is welcome in the [GitHub issues](https://github.com/amelienbergerot/graphe/issues).

## How it works

1. **Files**: graphe reads the files git tracks, plus untracked files that are not ignored, minus the folders listed in `exclude` in the host's optional `graphe.toml`. Each file goes to the reader for its extension.
2. **Readers** turn the files into nodes (files, classes, functions, methods, fields, constants) and links between them (`calls`, `contains`, `uses`, `reads`). A *dedicated reader* (Python through its ast, JavaScript/TypeScript/Svelte, GDScript) follows imports and types, so it can link a call to its definition with certainty. The *generic reader* (tree-sitter: Go, Rust, Java/Kotlin, C/C++, C#, Ruby, Swift, PHP) links a call by name, and only when the language defines that name once. It never does this for a common name like `get` or `push`.
3. **The core** reads the text: where each body ends, its comment, the texts it displays, module variables and who reads them, and the Markdown documents with what they cite (code between backticks, other documents by identifier, `T-0012`). With `[keys]` in `graphe.toml`, it links the code that names a key to the code that answers it (`sends`).
4. **Local extensions** add enrichments that only make sense for one host. They live in the host's repository and are declared in its `graphe.toml` ([ADR 0001](docs/adr/0001-one-tool-local-extensions.md), [the contract](docs/contribution.md)). A `graphe.toml` that declares extensions runs their code at every build, the git hooks' included, like a Makefile: build a cloned repository only if you trust it.
5. **Output**, in the host's `graphe/` folder (git-ignored): `graphe.json` (the graph, its communities found with Louvain) and `REPORT.md` (counts, the most connected nodes). The page that draws the nodes by community, `graphe.html`, is made only on demand, whatever the host's size: `graphe view` writes and opens it, `graphe view X` on node X.
6. **Freshness**: the git hooks rebuild the graph in the background after a commit, merge, checkout or rewrite. A query on a graph older than the code or the tool rebuilds it first, so the answer can be trusted.

Words such as *reader*, *contribution* and *takeover* are defined in [GLOSSARY.md](GLOSSARY.md).

## Readers

The languages the graph reads, and how each is read: [docs/readers.md](docs/readers.md).

## Tested on

Public sample hosts, pinned in `docs/sample-hosts.md`. Measures only: the build on this machine (Windows, median of three, warm), one query against grep's lines for the same name.

| Host | Languages | Files | Build | One query, compared with grep |
|---|---|---|---|---|
| Django | Python, JavaScript | 7104 (2943 `.py`) | 54.8 s | `explain django/shortcuts.py::get_object_or_404`: 5 callers, 839 bytes; grep `get_object_or_404(`: 21 lines, 2130 bytes |
| gitea | Go, TypeScript | 6431 (3199 `.go`) | 31.4 s | `explain GetRepositoryByID`: 76 callers by name, 1778 bytes; grep `GetRepositoryByID(`: 80 lines in 63 files, 7973 bytes |
| libsignal | Rust, Java/Kotlin, Swift, TypeScript | 1852 (612 `.rs`, 344 `.java`, 218 `.swift`, 125 `.kt`) | 20.6 s | `explain Timestamp.from_epoch_millis`: 57 callers by name, 1577 bytes; grep `from_epoch_millis(`: 81 lines in 30 files, 8260 bytes |
| protobuf | C/C++, Java/Kotlin, C#, Ruby, Python, Rust, PHP, Go | 3795 (1363 C/C++, 293 `.java`, 224 `.cs`, 158 `.php`, 54 `.rb`) | 62.7 s | `callers ByteString.copyFromUtf8`: 128 callers by name, 11526 bytes; grep `copyFromUtf8(` in `.java` and `.kt`: 176 lines in 44 files, 26514 bytes |

## Developing graphe

The author's install, from the root of a clone, editable, so that a change in the clone serves every host at once ([ADR 0004](docs/adr/0004-published-install-editable-for-the-author.md)):

```
uv tool install -e .
```

An install made before the distribution became `graphe-code` is named `graphe` for uv: remove it once, then install as above.

```
uv tool uninstall graphe
```

The skill, as a link to the clone rather than the plugin (a plugin is a cached copy, which would lag the clone):

```powershell
# Windows: a junction.
New-Item -ItemType Junction -Path "$HOME\.claude\skills\graphe" -Target "$PWD\skills\graphe"
```

```sh
# macOS, Linux: a symbolic link.
ln -s "$PWD/skills/graphe" ~/.claude/skills/graphe
```

The gaps met while using the graph go in `BACKLOG.md`, naming the host (`AGENTS.md`).

A release (`.github/workflows/release.yml`), in one commit then a tag:

1. Set the same version `X.Y.Z` in `pyproject.toml` and `.claude-plugin/plugin.json`.
2. Add its entry `## X.Y.Z` to `CHANGELOG.md`, with a **Contract** section if it changes `contribute(project)`, `Project` or the shape of the nodes and links.
3. Commit, then push the tag: `git tag vX.Y.Z` and `git push origin vX.Y.Z`. The workflow stops before the upload if the tag and the two versions differ (`python .github/check_release.py vX.Y.Z` checks it locally), then uploads `graphe-code` to PyPI and creates the GitHub release.

Raising a grammar's cap, when the newest-versions job flags one, is an ordinary commit, not a release step.
