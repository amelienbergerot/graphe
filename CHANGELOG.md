# Changelog

One entry per release, newest first. graphe follows [SemVer](https://semver.org) and stays `0.x` while the extension contract may still move.

A release that changes `contribute(project)`, `Project`, the shape of the nodes and links, or another field of `graphe/graphe.json` carries a **Contract** section: what breaks, and how to adapt an extension or a tool that reads the file. Such a release is at least a minor bump in `0.x` (never a patch), a major from `1.0`.

## Unreleased

## 0.4.0

The generic reader reads a language's files over 8 processes of its own when they weigh 4 MB or more, then links them in its own process on the results in the files' order: the graph is unchanged, and a file that does not parse is still named once. On an idle machine, the code before against this one: gitea 9.62 -> 7.16 s, protobuf 15.47 -> 12.93 s, libsignal 5.24 -> 5.26 s (T-0092, ADR 0005).

The Python reader resolves a module by its import name, its path without its leading folders that are no package (no `__init__.py`): in a `src/` layout, `from graphe import core` reaches `src/graphe/core.py`, and Django's `tests/admin_views/models.py` is `admin_views.models`, as its test runner imports it. `import a.b.c` imports `a.b` and `a.b.c` as well as `a` (`as d`: not `a`), and `a.b.f()` reaches the submodule's `f`, `models.lookups.Lookup` after `from django.db import models` too, unless the package binds that name otherwise (`from .x import g as b` makes `a.b` the function `g`, also for `from a import b`); the package's own import of the submodule wins over a fallback beside it (`except ImportError: b = None`). A name two modules bear resolves to neither; a leading namespace package (no `__init__.py`) is left out of the name, so an import through it resolves to nothing. The `tools.` shortcut, Grid Zero's, is gone: the rule gives its scripts the same names. The nodes are unchanged, a file node keeping its path's name; the core's `alias.CONSTANT` finds its module the same way, an import line with a trailing comment included, and is read in a host where no constant is defined once. On graphe, `callers run_reader`, `enrich` and `tickets` name their callers; on Django 930 links more, 26 reads and 9 calls by name become sure, 1 lost through a leading namespace package; on Grid Zero one read by name becomes sure, nothing else changes (T-0096).

A host whose tickets are its GitHub issues says so in `graphe.toml`: `[tickets] github = true` (the one github.com repository its remotes name, fetch and push) or `github = "owner/repo"`. An issue whose title starts with an identifier is then that ticket, before a Markdown file of the same identifier (which stays a document): the code that cites it, its body and its comments cite and name as a document's text does, and `explain` gives it with its URL. The issues and their comments, not the pull requests, come from GitHub's REST API by the standard library, at most every 10 minutes and only what changed since (`since`), into `graphe/issues.json`; a token if one is there (`GH_TOKEN`, `GITHUB_TOKEN`, `gh auth token`). GitHub unreachable, the build uses that cache, or goes without the issues, in one line; no github.com remote, or several, one line too, and `graphe install` asks which of several. Without the setting nothing changes: Grid Zero's and 4cast's `graphe.json` are identical. graphe's own tickets are its issues: the code's `cites` links identical ticket by ticket, T-0001 to T-0093, files against issues; `tickets/` is deleted (T-0095, ADR 0006).

The core's enrichment takes about half the time: a comment and a line's indentation tested once per line, a line without a quote counted without the string scan, the names of module variables defined once tried only on the lines that name one after a `.`, and, with the default ticket identifier, the bodies of a file that cites no ticket not searched. The graph is unchanged; `enrich` 5.50 -> 3.07 s in protobuf's build (21.4 -> 19.0 s), 1.40 -> 0.88 s in libsignal's (6.34 -> 5.81 s), 5.6 -> 3.6 s in Django's (T-0091).

The communities fold each node of one neighbour into that neighbour, up the chain, before Louvain runs, its links kept as the neighbour's own weight: a node of one neighbour always shares its community. The nodes and links are unchanged; the partition moves, its modularity 0.9131 -> 0.9130 on protobuf, higher on libsignal and Django. `communities()` 12.1 -> 7.6 s on protobuf, 4.4 -> 3.1 s on libsignal, no gain on Django (T-0090).

A build lists the host's files once, every reader and suffix served from that listing, and the generic reader looks for a generator's marker on the tree it has just parsed, so each file is parsed once. The graph is unchanged; the build 44.6 -> 35.8 s on Django, 34.5 -> 30.3 s on protobuf, 10.9 -> 9.1 s on libsignal. A query that finds the graph stale rebuilds it on the listing that found it stale (T-0087). A query checks the graph's freshness with one stat per file: a fresh query 2.57 -> 2.08 s on Django, 2.11 -> 1.71 s on protobuf, 1.12 -> 0.91 s on libsignal (T-0089). A build runs the readers that have files at once, one process each, when the readers beside the largest have 200 files or more; their contributions are taken in the same order, so the graph is unchanged, and a reader's error stops the build with the same message. On a loaded machine, old and new alternated: libsignal 25.3 -> 17.8 s, protobuf 73.3 -> 54.6 s; Django (111 JavaScript files beside its Python) and Grid Zero stay in one process, unchanged. The readers, `READERS` and `Project` move from `graphe.cli` to `graphe.readers`, which a reader's process imports without networkx (T-0088, ADR 0005). Measured again on an idle machine, the threshold is 200 files (250 as measured under load) and a pool costs 0.18 s; the build, the code before T-0088 against this one: libsignal 8.03 -> 4.79 s, protobuf 25.65 -> 15.09 s, Django 39.62 -> 38.10 s (T-0093).

The generic reader makes a node of a method without a body, Java's abstract or an interface's (not a `native` one), and of a Swift protocol's `func` requirement; a method overrides the one of its class or of a class its base list names directly (Swift's `extension C: P` too). A call whose candidates all override one declaration is linked to it, by name: protobuf's `input.pushLimit(n)` goes to `CodedInputStream.pushLimit`, libsignal's `nativeHandle.const()` to `SignalMutPointer.const`. A single concrete definition is linked as before. On protobuf, 3802 Java call sites linked more, on libsignal 1161 Swift and 4 Java ones; none lost or moved (T-0081).

The generic reader links a send qualified by a class of the host, Rust's `T::f()`, Java's and Kotlin's `C.f()`, to that class's method `f`, by name, a common name too (`DeviceId::new`), when the classes so named define one; several leave it unattributed, none leave it to the name alone, as before. A type the host only implements a trait for (Rust's `impl From<X> for HashMap`) is not its class. On libsignal, 2629 links more, on protobuf 3112 (T-0080).

`graphe check` and REPORT.md list the generated files read, as git's `linguist-generated` says, or, for the generic reader's languages, a known header (protobuf's compiler, Go's `// Code generated ... DO NOT EDIT.`, before the first code), each with the count of ambiguous calls on the names it defines, and the `exclude` line to paste that drops those whose names are ambiguous, the host's own entries kept. The links are unchanged (T-0079).

The skill reaches Codex, GitHub Copilot CLI and Cursor through a `plugin.json` at the root (the Agent Plugins format) and Codex's marketplace (`.agents/plugins/marketplace.json`), Gemini CLI through `gemini-extension.json`; each untested, the README says how to install it (T-0078).

### Contract

With `[tickets] github`, a `ticket` node may come from an issue: its `source_file` is the issue's URL (`https://github.com/owner/repo/issues/N`), its `source_location` empty (no line), and it has no `end`; a link from an issue's text is located at the issue's or the comment's URL, without `:line`. A tool that opens `source_file` as a path, or splits a location at its last `:`, skips those. Without the setting, nothing changes (T-0095).

A new node kind, `abstract` (`Class.method`, its id `<file>_abstract_<name>`), and a new relation, `overrides`, from a method to the declaration it implements (`INFERRED`); `overrides` is no call relation (not in `CALLS`), but `callers` of a method adds the callers of the declarations it overrides. A tool that lists the callable nodes by kind (`function`, `method`) adds `abstract`; the ids of the nodes already there are unchanged (T-0081).

A contribution may return `generated`, the paths of the generated files it read; nothing breaks, an extension that returns none is read as before.

## 0.3.0

The hook skips a grep that filters a pipe (`ls | grep x`): it searches no code (T-0086).

The hook's line names the nodes of a name that designates several, as `explain` takes them (`Class.method`, else `file::name`), five at most (T-0085).

`graphe hook` no longer loads networkx nor the readers: about 0.27 s per call instead of 0.6 on Windows, 0.20 s for a command that is no grep (T-0084). The command's entry point is now `graphe:main`; an editable install made before (`uv tool install --editable`) keeps the old launcher, which still works, until it is installed again.

## 0.2.0

`graphe hook`, Claude Code's PreToolUse hook, which the plugin installs: a Grep, or a `grep`/`rg` through Bash or PowerShell, whose pattern is a name the graph knows gets one line of context naming `graphe explain` on it; silent otherwise, it never blocks the tool nor rebuilds the graph (T-0077).

The JS reader takes a Vue component (`.vue`): its `<script>` (and `<script setup>`) in TypeScript when its `lang` says so, its template's expressions (`{{ }}`, `@click`, `:prop`, `v-if`, `v-for`) read for their calls, which belong to the component; an expression it cannot parse costs only itself (T-0082).

The JS reader takes `.jsx` (the JavaScript grammar) and `.tsx` (the TSX grammar): their imports, calls and definitions are read as a `.js` or `.ts` file's, a bare handler (`onClick={save}`) is a `references` as in Svelte's markup, and a relative specifier may leave either suffix out (T-0076).

A body's extent (`end`) reads its strings as strings: a parenthesis inside one no longer stretches a constant to the end of its file, and an unindented line of a string over several lines no longer ends its block (T-0083).

`graphe affected [REV] [--depth N]`: what the working tree changes since it left REV (HEAD by default), the nodes touched, the definitions removed, then the callers of each node; `callers` marks a caller linked by name alone, `[by name]` on the level when every one is, `?` after it otherwise (T-0075).

`explain` and `callers` say why they could not attribute the calls of a name: a count per cause (several definitions, with the candidates when five at most; a common name; a receiver of unknown type; a definition outside the host) under the line "+ N calls named `f` the graph could not attribute:" (T-0074).

### Contract

`graphe.json`'s `unattributed` maps each name to its counts per cause, `{"filter": {"several": 2, "receiver": 1}}`, no longer to one count (`{"filter": 3}`). The causes: `several`, `common`, `receiver`, `outside`. A tool that reads the file sums the values for the old count.

## 0.1.1

Outside a git repository, a query prints its one-line error alone: the "rebuilding" line no longer comes before it (T-0069).

## 0.1.0

The first release, on PyPI as `graphe-code`: the `graphe` command, the `graphe` skill as a Claude Code plugin, local extensions through `contribute(project)` declared in `graphe.toml`.
