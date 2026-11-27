# Changelog

One entry per release, newest first. graphe follows [SemVer](https://semver.org) and stays `0.x` while the extension contract may still move.

A release that changes `contribute(project)`, `Project`, the shape of the nodes and links, or another field of `graphe/graphe.json` carries a **Contract** section: what breaks, and how to adapt an extension or a tool that reads the file. Such a release is at least a minor bump in `0.x` (never a patch), a major from `1.0`.

## Unreleased

The generic reader makes a node of a method without a body, Java's abstract or an interface's (not a `native` one), and of a Swift protocol's `func` requirement; a method overrides the one of its class or of a class its base list names directly (Swift's `extension C: P` too). A call whose candidates all override one declaration is linked to it, by name: protobuf's `input.pushLimit(n)` goes to `CodedInputStream.pushLimit`, libsignal's `nativeHandle.const()` to `SignalMutPointer.const`. A single concrete definition is linked as before. On protobuf, 3802 Java call sites linked more, on libsignal 1161 Swift and 4 Java ones; none lost or moved (T-0081).

The generic reader links a send qualified by a class of the host, Rust's `T::f()`, Java's and Kotlin's `C.f()`, to that class's method `f`, by name, a common name too (`DeviceId::new`), when the classes so named define one; several leave it unattributed, none leave it to the name alone, as before. A type the host only implements a trait for (Rust's `impl From<X> for HashMap`) is not its class. On libsignal, 2629 links more, on protobuf 3112 (T-0080).

`graphe check` and REPORT.md list the generated files read, as git's `linguist-generated` says, or, for the generic reader's languages, a known header (protobuf's compiler, Go's `// Code generated ... DO NOT EDIT.`, before the first code), each with the count of ambiguous calls on the names it defines, and the `exclude` line to paste that drops those whose names are ambiguous, the host's own entries kept. The links are unchanged (T-0079).

The skill reaches Codex, GitHub Copilot CLI and Cursor through a `plugin.json` at the root (the Agent Plugins format) and Codex's marketplace (`.agents/plugins/marketplace.json`), Gemini CLI through `gemini-extension.json`; each untested, the README says how to install it (T-0078).

### Contract

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
