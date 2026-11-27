"""T-0095: a host's tickets taken from its GitHub issues, `[tickets] github` of graphe.toml; never the network."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from graphe import issues
from test_host import _host, _run


def _repository(tmp_path: Path, toml: str, remotes: dict[str, str]) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for name, url in remotes.items():
        subprocess.run(["git", "remote", "add", name, url], cwd=tmp_path, check=True)
    (tmp_path / "graphe.toml").write_bytes(toml.encode())
    return tmp_path


def test_the_repository_is_the_one_github_repository_of_the_remotes(tmp_path: Path, capsys):
    host = _repository(tmp_path, "[tickets]\ngithub = true\n",
                       {"origin": "https://github.com/a/b.git", "mirror": "git@github.com:A/b", "lab": "https://gitlab.com/c/d",
                        "ci": "https://x-access-token:abc@github.com/a/b", "other": "https://mygithub.com/e/f"})
    subprocess.run(["git", "remote", "set-url", "--push", "lab", "ssh://git@github.com/a/b/"], cwd=host, check=True)
    assert issues.remotes(host) == ["a/b"]
    assert issues.repository(host) == "a/b"
    assert capsys.readouterr().err == ""


def test_no_github_remote_or_several_build_without_the_issues_in_one_line(tmp_path: Path, capsys):
    none = _repository(tmp_path / "none", "[tickets]\ngithub = true\n", {"lab": "https://gitlab.com/c/d"})
    assert issues.repository(none) is None
    assert len(capsys.readouterr().err.strip().splitlines()) == 1
    several = _repository(tmp_path / "several", "[tickets]\ngithub = true\n",
                          {"origin": "https://github.com/a/b", "fork": "https://github.com/me/b"})
    assert issues.repository(several) is None
    err = capsys.readouterr().err
    assert len(err.strip().splitlines()) == 1 and "a/b, me/b" in err and 'github = "owner/repo"' in err


def test_the_setting_names_the_repository_or_is_absent(tmp_path: Path):
    host = _repository(tmp_path, '[tickets]\ngithub = "o/r"\n', {"origin": "https://github.com/a/b"})
    assert issues.repository(host) == "o/r"
    (host / "graphe.toml").write_text("", encoding="utf-8")
    assert issues.repository(host) is None
    assert issues.tickets(host) == []


API = "https://api.github.com/repos/o/r"


def _issue(number: int, title: str, body: str | None = "", pull: bool = False) -> dict:
    issue = {"number": number, "title": title, "html_url": f"https://github.com/o/r/issues/{number}", "body": body}
    return {**issue, "pull_request": {}} if pull else issue


def _comment(id_: int, number: int, body: str) -> dict:
    return {"id": id_, "issue_url": f"{API}/issues/{number}", "body": body,
            "html_url": f"https://github.com/o/r/issues/{number}#issuecomment-{id_}"}


def _github(monkeypatch, answers: dict[str, tuple[list, str | None]]) -> list[str]:
    """`issues._get` answered from `answers` (an URL without its query -> items, next page); the URLs asked."""
    asked = []

    def get(url: str, token: str | None) -> tuple[list, str | None]:
        asked.append(url)
        if isinstance(answers, Exception):
            raise answers
        return answers[url.split("?")[0]] if url.split("?")[0] in answers else answers[url]

    monkeypatch.setattr(issues, "_get", get)
    return asked


def test_the_issues_and_their_comments_are_fetched_without_the_pull_requests(tmp_path: Path, monkeypatch):
    host = _repository(tmp_path, '[tickets]\ngithub = "o/r"\n', {})
    asked = _github(monkeypatch, {
        f"{API}/issues": ([_issue(2, "T-0002: Two", None), _issue(3, "A pull request", pull=True)], "page2"),
        "page2": ([_issue(1, "T-0001: One", "See T-0002.")], None),
        f"{API}/issues/comments": ([_comment(9, 1, "And `aider`."), _comment(8, 3, "On the pull request")], None)})
    assert issues.tickets(host) == [
        {"number": 1, "title": "T-0001: One", "url": "https://github.com/o/r/issues/1", "body": "See T-0002.",
         "comments": [{"url": "https://github.com/o/r/issues/1#issuecomment-9", "body": "And `aider`."}]},
        {"number": 2, "title": "T-0002: Two", "url": "https://github.com/o/r/issues/2", "body": "", "comments": []}]
    assert len(asked) == 3 and "state=all" in asked[0] and "since" not in asked[0]


def test_the_cache_is_fetched_again_only_past_10_minutes_and_only_what_changed(tmp_path: Path, monkeypatch):
    host = _repository(tmp_path, '[tickets]\ngithub = "o/r"\n', {})
    _github(monkeypatch, {f"{API}/issues": ([_issue(1, "T-0001: One")], None), f"{API}/issues/comments": ([], None)})
    issues.tickets(host)
    asked = _github(monkeypatch, {})
    assert [t["title"] for t in issues.tickets(host)] == ["T-0001: One"] and asked == []  # fresh: no request
    monkeypatch.setattr(issues.time, "time", lambda: 2e9)  # far past 10 minutes
    asked = _github(monkeypatch, {f"{API}/issues": ([_issue(1, "T-0001: Renamed")], None),
                                  f"{API}/issues/comments": ([_comment(5, 1, "New")], None)})
    found = issues.tickets(host)
    assert [t["title"] for t in found] == ["T-0001: Renamed"] and found[0]["comments"][0]["body"] == "New"
    assert len(asked) == 2 and all("since=" in url for url in asked)


def test_no_network_uses_the_cache_or_builds_without_the_issues_in_one_line(tmp_path: Path, monkeypatch, capsys):
    host = _repository(tmp_path, '[tickets]\ngithub = "o/r"\n', {})
    _github(monkeypatch, OSError("unreachable"))
    assert issues.tickets(host) == []
    assert len(capsys.readouterr().err.strip().splitlines()) == 1
    _github(monkeypatch, {f"{API}/issues": ([_issue(1, "T-0001: One")], None), f"{API}/issues/comments": ([], None)})
    issues.tickets(host)
    monkeypatch.setattr(issues.time, "time", lambda: 2e9)
    _github(monkeypatch, OSError("unreachable"))
    assert [t["title"] for t in issues.tickets(host)] == ["T-0001: One"]
    assert len(capsys.readouterr().err.strip().splitlines()) == 1
    for broken in ("{not json", '{"repository": "o/r", "fetched": 0}'):  # a broken cache: as none
        (host / "graphe" / "issues.json").write_text(broken, encoding="utf-8")
        assert issues.tickets(host) == []


def test_an_issue_is_the_ticket_the_code_and_the_issues_cite(tmp_path: Path, monkeypatch):
    """The issue beats the file of its identifier; a citation from a body is located at its issue, from a comment at
    the comment; `explain` names the ticket with its URL."""
    host = _host(tmp_path, {"outils.py": "# For T-0001.\ndef aider():\n    return 1\n", "tickets/T-0001-aide.md": "# Aide\n",
                            "graphe.toml": '[tickets]\ngithub = "o/r"\n'})
    url = "https://github.com/o/r/issues/"
    _github(monkeypatch, {f"{API}/issues": ([_issue(1, "T-0001: The help", "After T-0002, `aider`."),
                                             _issue(2, "T-0002: Before"), _issue(4, "Without an identifier")], None),
                          f"{API}/issues/comments": ([_comment(7, 2, "Then T-0001.")], None)})
    issues.tickets(host)  # the cache, fresh: the build does not fetch
    r = _run(host, "build")
    assert r.returncode == 0, r.stderr
    data = json.loads((host / "graphe" / "graphe.json").read_bytes())
    nodes = {n["id"]: n for n in data["nodes"]}
    links = {(e["source"], e["target"]): e for e in data["links"]}
    aider = next(n for n, d in nodes.items() if d["name"] == "aider")
    one = nodes["ticket_t_0001"]
    assert (one["kind"], one["source_file"], one["source_location"], one["notes"]) == \
        ("ticket", f"{url}1", "", "The help")
    assert nodes["document_tickets_t_0001_aide_md"]["kind"] == "document"
    assert not any(d["source_file"] == f"{url}4" for d in nodes.values())
    assert links[(aider, "ticket_t_0001")]["relations"] == ["cites"]
    assert links[(aider, "ticket_t_0001")]["locations"] == ["outils.py:2"]
    assert links[("ticket_t_0001", "ticket_t_0002")]["locations"] == [f"{url}1"]
    assert links[("ticket_t_0002", "ticket_t_0001")]["locations"] == [f"{url}2#issuecomment-7"]
    assert links[("ticket_t_0001", aider)]["relations"] == ["names"]
    r = _run(host, "explain", "aider")
    assert f"T-0001 ({url}1)" in r.stdout, r.stdout
    r = _run(host, "explain", "T-0001")
    assert r.stdout.startswith(f"T-0001  [ticket]  {url}1\n"), r.stdout


def test_install_asks_which_repository_when_the_remotes_name_several(tmp_path: Path):
    toml = 'exclude = ["x"]\r\n\r\n[tickets]\r\ngithub = true  # the issues\r\n\r\n[keys]\r\ngithub = true\r\n'
    host = _repository(tmp_path, toml, {"origin": "https://github.com/a/b", "fork": "https://github.com/me/b"})
    r = _run(host, "install", input="")  # no answer: nothing written
    assert r.returncode == 0, r.stderr
    assert (host / "graphe.toml").read_bytes() == toml.encode() and "a/b" in r.stdout
    r = _run(host, "install", input="2\n")
    assert r.returncode == 0, r.stderr
    assert (host / "graphe.toml").read_bytes() == toml.replace("github = true  #", 'github = "me/b"  #').encode()
    r = _run(host, "install", input="2\n")  # set: not asked again
    assert "a/b" not in r.stdout
