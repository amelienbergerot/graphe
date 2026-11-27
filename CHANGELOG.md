# Changelog

One entry per release, newest first. graphe follows [SemVer](https://semver.org) and stays `0.x` while the extension contract may still move.

A release that changes `contribute(project)`, `Project`, the shape of the nodes and links, or another field of `graphe/graphe.json` carries a **Contract** section: what breaks, and how to adapt an extension or a tool that reads the file. Such a release is at least a minor bump in `0.x` (never a patch), a major from `1.0`.

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
