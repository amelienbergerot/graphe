"""T-0095, ADR 0006: a host's tickets taken from its GitHub issues, when graphe.toml says so.

`[tickets] github = true` takes the one github.com repository its remotes name (fetch and push); `github =
"owner/repo"` names it. Without the setting, nothing here runs: no git, no network.

The issues and their comments (no pull request) are kept in graphe/issues.json, fetched again (only what changed
since, `since`) when that fetch is older than REFRESH; GitHub unreachable, the cache serves, and a build never fails
for it. The REST API by urllib, a token only if one is there (GH_TOKEN, GITHUB_TOKEN, then `gh auth token`).
"""

from __future__ import annotations

import http.client
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

from graphe import root as graphe_root

API = "https://api.github.com"
REFRESH = 600  # seconds: the cache is fetched again past 10 minutes
TIMEOUT = 10  # seconds per request: a git hook's build is never held up long
# github.com/owner/repo in a remote's URL: https://, git@github.com:, ssh://git@github.com/.
REMOTE = re.compile(r"^(?:https?://|ssh://)?(?:[^@/\s]+@)?github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")


def _say(text: str) -> None:
    print(f"graphe: {text}", file=sys.stderr)


def setting(root: Path) -> bool | str:
    """`[tickets] github` of graphe.toml: False without it, True, or "owner/repo"."""
    table = graphe_root.configuration(root).get("tickets", {})
    value = table.get("github", False) if isinstance(table, dict) else None
    if not (isinstance(value, bool) or isinstance(value, str) and re.fullmatch(r"[\w.-]+/[\w.-]+", value)):
        raise RuntimeError(f'[tickets] github ({graphe_root.CONFIGURATION}): true, or "owner/repo"')
    return value


def remotes(root: Path) -> list[str]:
    """The distinct github.com repositories among the remotes' URLs, fetch and push, as the first remote spells them."""
    try:
        r = subprocess.run(["git", "remote", "-v"], cwd=root, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return []
    found: dict[str, str] = {}
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and (m := REMOTE.search(parts[1])):
            found.setdefault(f"{m[1]}/{m[2]}".lower(), f"{m[1]}/{m[2]}")
    return list(found.values())


def repository(root: Path) -> str | None:
    """The repository whose issues are the host's tickets; None, said in one line when the setting is on."""
    value = setting(root)
    if value is not True:
        return value or None
    found = remotes(root)
    if len(found) == 1:
        return found[0]
    if not found:
        _say("[tickets] github = true, but no remote is on github.com: built without the issues")
    else:
        _say(f"[tickets] github = true, but the remotes name {', '.join(sorted(found))}: set github = \"owner/repo\" "
             f"in {graphe_root.CONFIGURATION} (graphe install asks which); built without the issues")
    return None


def choose(root: Path) -> None:
    """`graphe install`: with `github = true` and several GitHub repositories among the remotes, the one asked for,
    written in its place in graphe.toml (the rest of the file as it was)."""
    if setting(root) is not True or len(found := sorted(remotes(root))) < 2:
        return
    print("  [tickets] github = true, and the remotes name several GitHub repositories:")
    for i, repo in enumerate(found, 1):
        print(f"    {i}. {repo}")
    try:
        answer = input("  Which one holds the tickets (its number)? ").strip()
    except EOFError:
        answer = ""
    path = root / graphe_root.CONFIGURATION
    text = path.read_bytes().decode("utf-8")
    m = re.search(r"(?ms)^\[tickets\][^\[]*?^[ \t]*github[ \t]*=[ \t]*(true)\b", text)
    if not (answer.isdigit() and 1 <= int(answer) <= len(found) and m):
        print(f"  [tickets] github: none chosen, {graphe_root.CONFIGURATION} unchanged")
        return
    path.write_bytes((text[:m.start(1)] + f'"{found[int(answer) - 1]}"' + text[m.end(1):]).encode("utf-8"))
    print(f'  [tickets] github = "{found[int(answer) - 1]}" ({graphe_root.CONFIGURATION})')


def tickets(root: Path) -> list[dict]:
    """The host's issues, sorted by number: number, title, url, body, comments (url, body) in their order; [] without
    the setting, or without a cache and GitHub unreachable."""
    repo = repository(root)
    if repo is None:
        return []
    path = root / graphe_root.OUTPUT.name / "issues.json"
    cache = _read(path, repo)
    now = time.time()  # before the requests: what changes during them is fetched again next time
    # shortcut: a failed fetch is tried again at the next build, so a network that drops the packets costs each build
    # TIMEOUT; to keep the failed attempt's time and wait REFRESH if a host's builds wait for it.
    if cache is None or now - cache["fetched"] > REFRESH:
        try:
            cache = _fetch(repo, cache, now)
            _write(path, cache)
        except (OSError, ValueError, KeyError, TypeError, http.client.HTTPException) as e:  # URLError is an OSError
            if cache is None:
                _say(f"the issues of {repo} not fetched ({e}), and no cache: built without them")
                return []
            _say(f"the issues of {repo} not fetched ({e}): those of {time.strftime('%Y-%m-%d %H:%M', time.localtime(cache['fetched']))}")
    by_issue: dict[int, list[dict]] = defaultdict(list)
    for _, c in sorted(cache["comments"].items(), key=lambda p: int(p[0])):
        by_issue[c["issue"]].append({"url": c["url"], "body": c["body"]})
    # A comment on a pull request is in no issue's.
    return [{"number": int(n), **i, "comments": by_issue.get(int(n), [])}
            for n, i in sorted(cache["issues"].items(), key=lambda p: int(p[0]))]


def _read(path: Path, repo: str) -> dict | None:
    """The cache of `repo`; None when absent, broken or another repository's."""
    try:
        cache = json.loads(path.read_bytes())
        valid = cache["repository"] == repo and isinstance(cache["fetched"], (int, float))             and isinstance(cache["issues"], dict) and isinstance(cache["comments"], dict)
        return cache if valid else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _write(path: Path, cache: dict) -> None:
    """Alongside, then replaced: two builds in the background never leave half a cache."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False, suffix=".tmp") as f:
        f.write(json.dumps(cache, ensure_ascii=False).encode("utf-8"))
    os.replace(f.name, path)


def _fetch(repo: str, cache: dict | None, now: float) -> dict:
    """The cache with what changed since its fetch merged in (everything without one), fetched at `now`.
    shortcut: an issue or a comment deleted on GitHub stays in the cache (`since` does not list it); to fetch
    everything again now and then if a deleted one misleads."""
    # A minute back: GitHub's clock against this one.
    since = f"&since={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(cache['fetched'] - 60))}" if cache else ""
    cache = cache or {"repository": repo, "issues": {}, "comments": {}}
    # shortcut: the first fetch is all or nothing, so a repository past ~5000 issues and comments without a token (60
    # requests an hour) never fills its cache; to keep the pages fetched and go on from them if a host has so many.
    token = _token()
    for item in _pages(f"{API}/repos/{repo}/issues?state=all&per_page=100{since}", token):
        if "pull_request" not in item:
            cache["issues"][str(item["number"])] = {"title": item["title"], "url": item["html_url"],
                                                    "body": item["body"] or ""}
    for item in _pages(f"{API}/repos/{repo}/issues/comments?per_page=100{since}", token):
        cache["comments"][str(item["id"])] = {"issue": int(item["issue_url"].rsplit("/", 1)[1]),
                                              "url": item["html_url"], "body": item["body"] or ""}
    cache["fetched"] = now
    return cache


def _pages(url: str | None, token: str | None):
    while url:
        items, url = _get(url, token)
        yield from items


def _get(url: str, token: str | None) -> tuple[list, str | None]:
    """One page of the API, and the next page's URL (its Link header). The only call to the network."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "graphe"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=TIMEOUT) as response:
        following = re.search(r'<([^>]+)>;\s*rel="next"', response.headers.get("Link", ""))
        return json.loads(response.read()), following and following[1]


def _token() -> str | None:
    """GH_TOKEN, GITHUB_TOKEN, then `gh auth token` when gh is installed; None: unauthenticated (a public repository,
    60 requests an hour)."""
    if token := os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"):
        return token
    if gh := shutil.which("gh"):
        try:
            r = subprocess.run([gh, "auth", "token"], capture_output=True, text=True, timeout=10)
            return (r.stdout.strip() or None) if r.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            pass
    return None
