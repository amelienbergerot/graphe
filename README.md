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
