"""`graphe hook` (T-0077): Claude Code's PreToolUse hook, which the plugin declares.

When Grep, or grep/rg through Bash or PowerShell, looks for a name a node bears, one line of added context names
`graphe explain` on it, or the nodes it designates when several (T-0085). Silent otherwise, and on any error; it never
blocks the tool, never rebuilds the graph (a stale one is read as it is).

It runs before every Bash call of the agent: this module imports the standard library alone, `graphe.root` only once
the pattern is a name, never networkx nor a reader (T-0084).
"""

from __future__ import annotations

import itertools
import json
import os
import re
import shlex
import sys
from collections import Counter
from pathlib import Path

# `def reset`, `func _ready`, `class Gabarit`: the name, without the language's keyword.
HEAD_WORDS = re.compile(r"^(?:async\s+def|def|static\s+func|func|class|function|const|var)\s+")
# The options of grep and rg whose separate value is not the pattern.
GREP_VALUED = {"-A", "-B", "-C", "-m", "-f", "-g", "-t", "-T", "-j", "--glob", "--type", "--type-not", "--max-count",
               "--file", "--include", "--exclude", "--exclude-dir", "--color", "--colors", "--max-depth", "--context",
               "--after-context", "--before-context", "--replace", "--threads"}
SHOWN = 5  # the designations named when a name designates several nodes


def _grep_pattern(command: str) -> str | None:
    """The pattern of the first grep or rg of a shell command that does not filter a pipe (T-0086): `-e`'s value,
    else its first operand."""
    # shortcut: the first such grep/rg only, a value glued to its option (`-eaider`) is missed, PowerShell is split by
    # POSIX rules; widen if agents' real commands go unhinted.
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    words = list(lexer)  # an unbalanced quote raises: the hook stays silent
    head = next((i for i, w in enumerate(words) if Path(w).name.removesuffix(".exe") in ("grep", "rg")
                 and not (i and words[i - 1] in ("|", "|&"))), None)  # `ls | grep x` searches no code
    if head is None:
        return None
    rest = iter(itertools.takewhile(lambda w: w.strip("();<>|&"), words[head + 1:]))  # up to `|`, `&&`, `;`
    for w in rest:
        if w in ("-e", "--regexp"):
            return next(rest, None)
        if w in GREP_VALUED:
            next(rest, None)
        elif not w.startswith("-"):
            return w
    return None


def _keys(node: dict) -> set[str]:
    """The names find() designates a node by (cli.py): its name, its bare label, its name's last segment."""
    keys = {node["name"], node["label"].removesuffix("()").lstrip(".")}
    if node["kind"] != "document":  # `BACKLOG.md`'s last segment `md` would designate every document
        keys.add(node["name"].rpartition(".")[2])
    return keys


def hint(name: str, nodes: list[dict]) -> str | None:
    """The line for `name`, or None when no node bears it."""
    designated = [n for n in nodes if name in _keys(n)]
    if not designated:
        return None
    what = "gives its definition, its callers and what it calls, without a grep"
    if len(designated) == 1:
        return f"graphe: `{name}` is in the code graph; `graphe explain {name}` {what}."
    names = Counter(n["name"] for n in nodes)
    # As cli._designation: `Class.method` when no other node bears that name, else `file::name`.
    designations = sorted(n["name"] if n["name"] != name and names[n["name"]] == 1
                          else f"{n['source_file']}::{n['name']}" for n in designated)
    more = f", and {len(designations) - SHOWN} more" if len(designations) > SHOWN else ""
    return (f"graphe: `{name}` designates {len(designated)} nodes of the code graph; `graphe explain` on one {what}:"
            f" {', '.join(designations[:SHOWN])}{more}.")


def hook() -> int:
    try:
        data = json.loads(sys.stdin.buffer.read())
        tool, tool_input = data["tool_name"], data["tool_input"]
        if tool == "Grep":
            pattern = tool_input["pattern"]
        elif tool in ("Bash", "PowerShell"):
            pattern = _grep_pattern(tool_input["command"]) or ""
        else:
            return 0
        name = re.sub(r"\\[b<>]|\\?\($", "", HEAD_WORDS.sub("", pattern.strip()))  # `def aider\b`, `aider\(`
        if not re.fullmatch(r"[\w.]+", name):  # before any git call: the hook runs on every Bash command
            return 0
        if "cwd" in data:
            os.chdir(data["cwd"])  # the session's directory, not the one the hook was started in
        from graphe import root as graphe_root  # noqa: PLC0415 - its import runs git: a name only
        # root() again: ROOT, fixed at import (graphe.cli's, before the chdir), may be the starting directory's.
        graph = graphe_root.root() / graphe_root.OUTPUT.name / "graphe.json"
        if not graph.is_file():
            return 0
        line = hint(name, json.loads(graph.read_bytes())["nodes"])
        if line:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": line}}))
    except Exception:  # noqa: BLE001 - fail-open: a hook's error must never stop the agent's tool
        pass
    return 0
