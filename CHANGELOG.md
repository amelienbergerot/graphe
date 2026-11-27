# Changelog

One entry per release, newest first. graphe follows [SemVer](https://semver.org) and stays `0.x` while the extension contract may still move.

A release that changes `contribute(project)`, `Project`, the shape of the nodes and links, or another field of `graphe/graphe.json` carries a **Contract** section: what breaks, and how to adapt an extension or a tool that reads the file. Such a release is at least a minor bump in `0.x` (never a patch), a major from `1.0`.

## Unreleased

`graphe affected [REV] [--depth N]`: what the working tree changes since it left REV (HEAD by default), the nodes touched, the definitions removed, then the callers of each node; `callers` marks a caller linked by name alone, `[by name]` on the level when every one is, `?` after it otherwise (T-0075).

`explain` and `callers` say why they could not attribute the calls of a name: a count per cause (several definitions, with the candidates when five at most; a common name; a receiver of unknown type; a definition outside the host) under the line "+ N calls named `f` the graph could not attribute:" (T-0074).

### Contract

`graphe.json`'s `unattributed` maps each name to its counts per cause, `{"filter": {"several": 2, "receiver": 1}}`, no longer to one count (`{"filter": 3}`). The causes: `several`, `common`, `receiver`, `outside`. A tool that reads the file sums the values for the old count.

## 0.1.1

Outside a git repository, a query prints its one-line error alone: the "rebuilding" line no longer comes before it (T-0069).

## 0.1.0

The first release, on PyPI as `graphe-code`: the `graphe` command, the `graphe` skill as a Claude Code plugin, local extensions through `contribute(project)` declared in `graphe.toml`.
