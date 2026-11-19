# graphe

The code graph of a host project: what calls what, what cites what. `graphe --help` lists the commands.

## Install

Once for the account, both in editable mode, so that a fix in this repository serves every host at once:

```powershell
# The command (Python 3.14: scipy does not exist yet for 3.15).
uv tool install -e E:/dev/graphe --python 3.14

# The Claude Code skill that teaches it to the agent in every project: a junction, not a copy.
New-Item -ItemType Junction -Path "$HOME\.claude\skills\graphe" -Target "E:\dev\graphe\skills\graphe"
```

Without an allow rule, each `graphe` query asks for approval (and a headless `claude -p` falls back to grep): add `Bash(graphe:*)` and `PowerShell(graphe *)` to `permissions.allow` in `~/.claude/settings.json`.

Then, in each host repository, `graphe install` sets the git hooks that rebuild the graph.

The gaps the graph leaves go in `BACKLOG.md`, naming the host.

## Readers

The languages the graph reads, and how each is read: `docs/readers.md`.

## Tested on

Public sample hosts, pinned in `docs/sample-hosts.md`. Measures only: the build on this machine (Windows, median of three, warm), one query against grep's lines for the same name.

| Host | Languages | Files | Build | One query, compared with grep |
|---|---|---|---|---|
| Django | Python, JavaScript | 7104 (2943 `.py`) | 54.8 s | `explain django/shortcuts.py::get_object_or_404`: 5 callers, 839 bytes; grep `get_object_or_404(`: 21 lines, 2130 bytes |
| gitea | Go, TypeScript | 6431 (3199 `.go`) | 31.4 s | `explain GetRepositoryByID`: 72 callers by name, 1770 bytes; grep `GetRepositoryByID(`: 80 lines in 63 files, 7813 bytes |
| libsignal | Rust, Java, TypeScript | 1852 (612 `.rs`, 344 `.java`) | 24.6 s | `explain Timestamp.from_epoch_millis`: 57 callers by name, 1577 bytes; grep `from_epoch_millis(`: 81 lines in 30 files, 8260 bytes |
| protobuf | Java, Python, Rust, PHP, Go | 3795 (293 `.java`) | 35.1 s | `callers ByteString.copyFromUtf8`: 124 callers by name, 9253 bytes; grep `copyFromUtf8(`: 172 lines in 42 files, 25208 bytes |
