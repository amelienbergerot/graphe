# Changelog

One entry per release, newest first. graphe follows [SemVer](https://semver.org) and stays `0.x` while the extension contract may still move.

A release that changes `contribute(project)`, `Project` or the shape of the nodes and links carries a **Contract** section: what breaks, and how to adapt an extension. Such a release is at least a minor bump in `0.x` (never a patch), a major from `1.0`.

## 0.1.1

Outside a git repository, a query prints its one-line error alone: the "rebuilding" line no longer comes before it (T-0069).

## 0.1.0

The first release, on PyPI as `graphe-code`: the `graphe` command, the `graphe` skill as a Claude Code plugin, local extensions through `contribute(project)` declared in `graphe.toml`.
