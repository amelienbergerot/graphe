"""T-0004, T-0005, T-0006: the `graphe` command on a small sample host project.

The files read are those git tracks, plus untracked files that are not
ignored, each to the reader of its extension; `graphe.toml` excludes folders.
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

from conftest import GRID_ZERO, grid_zero

CALLER = "from outils import aider\n\n\ndef travailler():\n    return aider()\n"
CALLEE = "def aider():\n    return 1\n"


def _run(host: Path, *arguments: str, env: dict | None = None) -> subprocess.CompletedProcess:
    # The root is fixed at import: a separate process, on the sample host (not on Grid Zero, cf. conftest).
    env = {**(env or os.environ), "GRAPHE_ROOT": str(host)}
    # T-0046: `view` prints the address it would open, the tests open no browser.
    return subprocess.run([sys.executable, "-c", "import sys, webbrowser, graphe.cli; webbrowser.open = print; "
                                                 "sys.exit(graphe.cli.main(sys.argv[1:]))",
                           *arguments], cwd=host, env=env, capture_output=True, text=True, encoding="utf-8")


def _host(tmp_path: Path, files: dict[str, str], tracked: str = "outils.py") -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    subprocess.run(["git", "add", tracked], cwd=tmp_path, check=True)  # the rest is not tracked
    return tmp_path


def _files_read(host: Path) -> set[str]:
    data = json.loads((host / "graphe" / "graphe.json").read_bytes())
    return {n["source_file"] for n in data["nodes"]}


def test_a_host_without_configuration_builds_and_answers(tmp_path: Path):
    host = _host(tmp_path, {"outils.py": CALLEE, "travail.py": CALLER})
    r = _run(host, "build")
    assert r.returncode == 0, r.stderr
    assert _files_read(host) == {"outils.py", "travail.py"}
    r = _run(host, "explain", "aider")
    assert r.returncode == 0, r.stderr
    assert "travailler" in r.stdout


def test_graphe_toml_excludes_folders_and_files_without_a_reader_are_ignored(tmp_path: Path):
    host = _host(tmp_path, {
        "outils.py": CALLEE, "travail.py": CALLER,
        "graphe.toml": 'exclude = ["**/tests", "brouillon"]\n',
        "paquet/tests/test_outils.py": CALLER, "tests/test_travail.py": CALLER,
        "brouillon/essai.py": CALLER, "paquet/brouillon/garde.py": CALLEE,  # brouillon/ at the root only
        "donnees/mesures.xml": "<mesures/>\n",
        ".gitignore": "ignore.py\n", "ignore.py": CALLER,
    })
    r = _run(host, "build")
    assert r.returncode == 0, r.stderr
    assert _files_read(host) == {"outils.py", "travail.py", "paquet/brouillon/garde.py"}


def test_a_file_that_does_not_parse_is_skipped_and_named(tmp_path: Path):
    # T-0016: Django tracks a test file written to fail parsing; one such file must not stop the build.
    host = _host(tmp_path, {"outils.py": CALLEE, "travail.py": CALLER, "casse.py": "1syntax_error\n"})
    r = _run(host, "build")
    assert r.returncode == 0, r.stderr
    assert "casse.py" in r.stderr
    assert _files_read(host) == {"outils.py", "travail.py"}


# T-0005: an external program (Godot, for the GDScript reader) is looked for in graphe.toml, then the PATH.
SCRIPT_GD = "extends Node\n\n\nfunc _ready():\n\tadd_child(Node.new())\n"


def _without_godot() -> dict:
    """A PATH reduced to git: Godot is not in it, whatever the machine."""
    return {**os.environ, "PATH": str(Path(shutil.which("git")).parent)}


def _engine_calls(host: Path) -> int:
    data = json.loads((host / "graphe" / "graphe.json").read_bytes())
    return data["coverage"]["godot"].get("engine", 0)


def test_without_godot_the_gdscript_reader_goes_on_and_names_the_key(tmp_path: Path):
    host = _host(tmp_path, {"godot/main.gd": SCRIPT_GD}, tracked="godot/main.gd")
    r = _run(host, "build", env=_without_godot())
    assert r.returncode == 0, r.stderr
    assert "[godot]" in r.stderr and "executable" in r.stderr
    assert _engine_calls(host) == 0
    assert not (host / "graphe" / "extension_api.json").exists()  # nothing in cache: the key serves next time


def test_with_the_key_the_engine_calls_are_resolved(tmp_path: Path):
    # A fake Godot: a Python script that writes an API where Node has add_child, where it is run.
    api = '{"classes":[{"name":"Node","methods":[{"name":"add_child"}]}],' \
          '"builtin_classes":[],"utility_functions":[],"singletons":[]}'
    script = f"#!{sys.executable}\nopen('extension_api.json', 'w').write({api!r})\n"
    # The key names one program: the script itself where a shebang runs it, a .cmd launching it on Windows.
    launcher = {"outils/godot.cmd": f'@"{sys.executable}" "%~dp0godot.py"\n'} if os.name == "nt" else {}
    executable = "outils/godot.cmd" if launcher else "outils/godot.py"
    host = _host(tmp_path, {"godot/main.gd": SCRIPT_GD, "outils/godot.py": script, **launcher,
                            "graphe.toml": f'[godot]\nexecutable = "{executable}"\n'}, tracked="godot/main.gd")
    (host / "outils/godot.py").chmod(0o755)
    r = _run(host, "build", env=_without_godot())
    assert r.returncode == 0, r.stderr
    assert "not found" not in r.stderr
    assert _engine_calls(host) >= 1


# T-0006: the graph is stale if a file of the host or of the tool is newer than it.
TOOL = Path(__file__).resolve().parents[1] / "src" / "graphe"
REBUILDING = "rebuilding"


def test_a_graph_older_than_the_tool_is_rebuilt(tmp_path: Path):
    host = _host(tmp_path, {"outils.py": CALLEE, "travail.py": CALLER})
    assert _run(host, "build").returncode == 0
    # The tool newer than the graph, without touching its files: the host and the graph aged.
    for f in ("outils.py", "travail.py"):
        os.utime(host / f, (0, 0))
    json_ = host / "graphe" / "graphe.json"
    tool = max(p.stat().st_mtime for p in TOOL.glob("*.py"))
    os.utime(json_, (tool + 3600, tool + 3600))  # control: newer than everything, nothing to rebuild
    r = _run(host, "explain", "aider")
    assert r.returncode == 0 and REBUILDING not in r.stderr, r.stderr
    os.utime(json_, (tool - 1, tool - 1))
    r = _run(host, "explain", "aider")
    assert r.returncode == 0 and REBUILDING in r.stderr, r.stderr


def _graph(host: Path) -> dict:
    data = json.loads((host / "graphe" / "graphe.json").read_bytes())
    return {k: v for k, v in data.items() if k not in ("built", "built_s")}


def test_a_build_on_the_cache_gives_the_same_graph(tmp_path: Path):
    # T-0026: the second build reads each Python file's definitions from graphe/, not from its source.
    host = _host(tmp_path, {"outils.py": CALLEE, "travail.py": CALLER})
    assert _run(host, "build").returncode == 0
    first = _graph(host)
    assert any((host / "graphe").rglob("*.pickle"))
    assert _run(host, "build").returncode == 0
    assert _graph(host) == first


def _hooks(host: Path) -> dict[str, bytes]:
    folder = host / ".git" / "hooks"
    return {p.name: p.read_bytes() for p in folder.glob("post-*") if p.suffix != ".sample"}


def test_install_sets_the_hooks_and_ignores_the_output_only_once(tmp_path: Path):
    host = _host(tmp_path, {"outils.py": CALLEE, ".gitignore": ".venv/"})  # without a final newline
    (host / ".git" / "hooks" / "post-commit").write_bytes(b"#!/bin/sh\necho avant\n")
    before = _hooks(host)
    for _ in range(2):
        assert _run(host, "install").returncode == 0
    hooks = _hooks(host)
    assert set(hooks) == {"post-commit", "post-merge", "post-checkout", "post-rewrite"}
    for text in hooks.values():
        assert text.count(b"graphe build --quiet") == 1 and b"tools/graphe.py" not in text
    assert hooks["post-commit"].startswith(b"#!/bin/sh\necho avant\n")
    assert (host / ".gitignore").read_text(encoding="utf-8") == ".venv/\n/graphe/\n"
    assert _run(host, "install", "--remove").returncode == 0
    assert _hooks(host) == before


def test_help_or_an_unknown_flag_prints_the_help_and_runs_nothing(tmp_path: Path):
    # An agent that tries `graphe install --help` must not install the hooks.
    host = _host(tmp_path, {"outils.py": CALLEE})
    for flag, code in (("--help", 0), ("-h", 0), ("--uninstall", 2)):
        r = _run(host, "install", flag)
        assert r.returncode == code and "graphe install" in r.stdout, flag
    # `graphe --help` alone, the README's first command (T-0063's wheel job): the help, exit 0.
    for flag, code in (("--help", 0), ("-h", 0), ("--nothing", 2)):
        r = _run(host, flag)
        assert r.returncode == code and "graphe install" in r.stdout, flag
    assert _hooks(host) == {} and not (host / ".gitignore").exists()


def test_install_recognises_the_output_already_ignored(tmp_path: Path):
    host = _host(tmp_path, {"outils.py": CALLEE, ".gitignore": "# le graphe\ngraphe/*\n"})
    assert _run(host, "install").returncode == 0
    assert (host / ".gitignore").read_text(encoding="utf-8") == "# le graphe\ngraphe/*\n"
    # A hook turned to CRLF by an editor: its block is recognised, not doubled.
    hook = host / ".git" / "hooks" / "post-merge"
    hook.write_bytes(hook.read_bytes().replace(b"\n", b"\r\n"))
    assert _run(host, "install").returncode == 0
    assert hook.read_bytes().count(b"graphe build --quiet") == 1
    # The block of the tool in French (before T-0011): replaced whole, nothing of it stays.
    hook.write_bytes(b"#!/bin/sh\necho avant\n\n# >>> graphe du code (graphe installer)\n"
                     b"graphe construire --calme >/dev/null 2>&1 &\n# <<< graphe du code\necho apres\n")
    assert _run(host, "install").returncode == 0
    text = hook.read_bytes()
    assert text.startswith(b"#!/bin/sh\necho avant\necho apres\n") and b"construire" not in text
    assert b"du code" not in text and text.count(b"graphe build --quiet") == 1


# T-0007: a local extension, declared by graphe.toml, contributes like a reader.
EXTENSION = '''
def contribute(projet):
    noeuds = projet.graph["nodes"]
    if "outils_aider" not in noeuds:  # le graphe deja assemble, lecteurs et coeur compris
        return {"nodes": [], "links": []}
    noeuds["outils_aider"]["label"] = "abime"  # lecture seule : sans effet sur le graphe
    return {
        "nodes": [
            {"id": "regle_politesse", "label": "politesse", "kind": "regle", "source_file": "regles.txt",
             "source_location": "L1", "name": "politesse"},
            {"id": "outils_aider", "texts": [projet.configuration["salut"]]},  # fusionne dans le noeud du lecteur
        ],
        "links": [{"source": "regle_politesse", "target": "outils_aider", "relation": "exige",
                   "confidence": "EXTRACTED", "source_file": "regles.txt", "source_location": "L1", "context": ""}],
    }
'''
WITH_EXTENSION = '[[extensions]]\npath = "ext/regles_du_temoin.py"\nsalut = "Bonjour"\n'


def test_a_local_extension_adds_a_node_and_enriches_an_existing_node(tmp_path: Path):
    host = _host(tmp_path, {"outils.py": CALLEE, "travail.py": CALLER, "ext/regles_du_temoin.py": EXTENSION,
                            "graphe.toml": WITH_EXTENSION})
    r = _run(host, "build")
    assert r.returncode == 0, r.stderr
    r = _run(host, "explain", "aider")
    assert r.returncode == 0, r.stderr
    assert "aider()" in r.stdout and "abime" not in r.stdout
    assert "displays: Bonjour" in r.stdout
    assert "exige (1)" in r.stdout and "regles.txt: politesse:1" in r.stdout
    assert "travailler" in r.stdout  # what the reader had linked stays
    r = _run(host, "explain", "politesse")
    assert r.returncode == 0 and "[regle]" in r.stdout, r.stdout


def test_an_extension_not_found_stops_the_build_and_names_itself(tmp_path: Path):
    host = _host(tmp_path, {"outils.py": CALLEE, "graphe.toml": WITH_EXTENSION})
    r = _run(host, "build")
    assert r.returncode != 0
    assert "ext/regles_du_temoin.py" in r.stderr and "Traceback" not in r.stderr
    assert not (host / "graphe" / "graphe.json").exists()


def test_an_expected_error_on_a_query_prints_one_line(tmp_path: Path):
    # T-0065: outside a git repository, or an extension without contribute(project): one line, exit 1.
    (tmp_path / "dehors").mkdir()
    r = _run(tmp_path / "dehors", "explain", "aider")
    assert r.returncode == 1 and "Traceback" not in r.stderr
    [line] = r.stderr.strip().splitlines()  # T-0069: the error alone, no rebuilding line before it
    assert line.startswith("graphe: ") and "dehors" in line and "files git tracks" in line
    host = _host(tmp_path / "hote", {"outils.py": CALLEE, "graphe.toml": WITH_EXTENSION,
                                     "ext/regles_du_temoin.py": "SALUT = 1\n"})
    r = _run(host, "search", "aider")
    assert r.returncode == 1 and "Traceback" not in r.stderr
    assert r.stderr.strip().splitlines()[-1].startswith("graphe: ") and "contribute(project)" in r.stderr


def test_a_real_bug_keeps_its_traceback(tmp_path: Path):
    host = _host(tmp_path, {"outils.py": CALLEE, "graphe.toml": WITH_EXTENSION,
                            "ext/regles_du_temoin.py": "def contribute(projet):\n    return 1 / 0\n"})
    r = _run(host, "search", "aider")
    assert r.returncode == 1 and "Traceback" in r.stderr and "ZeroDivisionError" in r.stderr


def test_an_extension_imports_the_graphe_package_beside_the_host_s_graphe_folder(tmp_path: Path):
    # T-0061: Grid Zero's imports; the second build runs with the host's graphe/ output folder in the current directory.
    host = _host(tmp_path, {"outils.py": CALLEE, "graphe.toml": WITH_EXTENSION,
                            "ext/regles_du_temoin.py": "from graphe.core import BODIES, _comment\n"
                                                       "from graphe.godot import Script\n\n\n"
                                                       "def contribute(projet):\n    return {}\n"})
    for _ in range(2):
        r = _run(host, "build")
        assert r.returncode == 0, r.stderr
    assert (host / "graphe" / "graphe.json").exists()


def test_a_new_node_without_its_fields_stops_the_build(tmp_path: Path):
    host = _host(tmp_path, {"outils.py": CALLEE, "graphe.toml": WITH_EXTENSION,
                            "ext/regles_du_temoin.py": 'def contribute(projet):\n'
                                                '    return {"nodes": [{"id": "orphelin", "label": "x"}]}\n'})
    r = _run(host, "build")
    assert r.returncode != 0
    assert "ext/regles_du_temoin.py" in r.stderr and "orphelin" in r.stderr and "name" in r.stderr


def test_check_feeds_on_the_sites_of_an_extension(tmp_path: Path):
    sites = '[{"verdict": "lu", "file": "regles.txt", "line": 1, "name": "a", "text": "a"},' \
            ' {"file": "regles.txt", "line": 2, "name": "b", "text": "b", "alert": "regle orpheline"}]'
    host = _host(tmp_path, {"outils.py": CALLEE, "graphe.toml": WITH_EXTENSION,
                            "ext/regles_du_temoin.py": f"def contribute(projet):\n    return {{'sites': {sites}}}\n"})
    r = _run(host, "check")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "== ext/regles_du_temoin.py: 1 sites classified {'lu': 1}" in r.stdout
    assert "regles.txt:2 b (regle orpheline)" in r.stdout
    assert _run(host, "build").returncode == 0
    coverage = json.loads((host / "graphe" / "graphe.json").read_bytes())["coverage"]
    assert coverage["ext/regles_du_temoin.py"] == {"lu": 1} and "php" not in coverage


# T-0008: an extension that contributes with the readers, before the core, and takes over the links of lines.
DISPATCH = 'from outils import aider\n\n\ndef aiguiller(ordre):\n    if ordre == "aide":\n        return aider()\n    return 0\n'
BRANCH = '''
def contribute(projet):
    assert projet.graph["nodes"] == {}  # comme un lecteur : rien d'assemble encore
    return {
        "nodes": [{"id": "branche_aide", "label": "aide", "kind": "command", "source_file": "aiguillage.py",
                   "source_location": "L5", "name": "aide"}],
        "takeovers": [{"from": "aiguillage_aiguiller", "to": "branche_aide", "source_file": "aiguillage.py",
                       "lines": [6, 6]}],
    }
'''


def test_an_extension_with_the_readers_takes_over_the_links_of_its_lines(tmp_path: Path):
    host = _host(tmp_path, {"outils.py": CALLEE, "aiguillage.py": DISPATCH, "ext/branches.py": BRANCH,
                            "graphe.toml": '[[extensions]]\npath = "ext/branches.py"\nwith_readers = true\n'})
    r = _run(host, "build")
    assert r.returncode == 0, r.stderr
    data = json.loads((host / "graphe" / "graphe.json").read_bytes())
    links = {(e["source"], e["target"]) for e in data["links"]}
    assert ("branche_aide", "outils_aider") in links
    assert ("aiguillage_aiguiller", "outils_aider") not in links
    branch = next(n for n in data["nodes"] if n["id"] == "branche_aide")
    assert branch["end"] == 6  # a body for the core, which saw it


# T-0008: Grid Zero's server commands, through its local extension (tools/graphe_grid_zero.py).
CLIENT = 'extends Node\n\n\nfunc envoyer():\n\t_poster({"cmd": "pas"})\n\t_poster({"cmd": "invente"})\n' \
         '\t# _poster({"cmd": "en_commentaire"})\n\n\nfunc _poster(m):\n\tpass\n'
GRID_ZERO_EXTENSION = '[[extensions]]\npath = "tools/graphe_grid_zero.py"\nwith_readers = true\n'


@grid_zero
def test_the_grid_zero_extension_links_the_commands_and_reports_an_unknown_order(tmp_path: Path):
    from test_graphe import ENGINE_PY, FLEET_PY, SERVER_PY
    host = _host(tmp_path, {
        "simulation/moteur.py": ENGINE_PY, "simulation/flotte.py": FLEET_PY, "simulation/server.py": SERVER_PY,
        "godot/client.gd": CLIENT, "graphe.toml": GRID_ZERO_EXTENSION,
        "tools/graphe_grid_zero.py": (GRID_ZERO / "tools" / "graphe_grid_zero.py").read_text(encoding="utf-8"),
    }, tracked="simulation")
    r = _run(host, "build", env=_without_godot())
    assert r.returncode == 0, r.stderr
    data = json.loads((host / "graphe" / "graphe.json").read_bytes())
    links = {(e["source"], e["target"]): e["relations"] for e in data["links"]}
    s, m, cmd = "simulation_server_", "simulation_moteur_moteur_", "simulation_server_cmd_"
    assert links[(f"{s}handle_command", f"{cmd}pas")] == ["dispatches"]
    assert "calls" in links[(f"{cmd}pas", f"{m}pas")]  # the command bears the calls of its branch
    assert (f"{s}handle_command", f"{m}pas") not in links
    # a branch with two commands: the first bears it, the other leads to it
    assert "calls" in links[(f"{cmd}liste", f"{m}fabrique")]
    assert links[(f"{cmd}relister", f"{cmd}liste")] == ["dispatches"]
    # a command without a branch of its own still has its node
    assert f"{cmd}rien" in {n["id"] for n in data["nodes"]}
    assert links[("godot_client_envoyer", f"{cmd}pas")] == ["sends"]
    r = _run(host, "check", env=_without_godot())
    assert r.returncode == 1, r.stdout + r.stderr
    assert "godot/client.gd:6 invente (order unknown to the server)" in r.stdout
    assert "en_commentaire" not in r.stdout


# T-0009: the pattern of the call that displays a text comes from the host; `search` finds its texts.
DISPLAYER = 'def accueillir():\n    return dire("Bienvenue au port")\n'


def test_a_host_with_its_displayed_text_pattern_finds_its_texts(tmp_path: Path):
    host = _host(tmp_path, {"outils.py": DISPLAYER})
    r = _run(host, "search", "bienvenue")
    assert r.returncode == 1, r.stdout  # without a pattern, no displayed text
    (host / "graphe.toml").write_text(r"""displayed_text = '\bdire\("([^"]*)"'""", encoding="utf-8")
    r = _run(host, "search", "bienvenue")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "outils.py: accueillir:1" in r.stdout and 'displays "Bienvenue au port"' in r.stdout


def test_a_text_pattern_without_a_group_stops_the_build(tmp_path: Path):
    host = _host(tmp_path, {"outils.py": DISPLAYER, "graphe.toml": "displayed_text = 'dire'\n"})
    r = _run(host, "build")
    assert r.returncode == 1 and "displayed_text" in r.stderr and "Traceback" not in r.stderr, r.stderr


# T-0009: Grid Zero's state, actions, hints and journal, through its extension after the core.
STATE_PY = '''from dataclasses import dataclass


@dataclass
class EtatDeJeu:
    raison_du_jour: str = ""


def construire(x) -> EtatDeJeu:
    return EtatDeJeu(raison_du_jour=x)
'''
READING_GD = 'func texte(state: Dictionary) -> String:\n\tif state.get("raison_du_jour"):\n' \
             '\t\t_poster({"action": "liste"})\n\treturn I18n.t("le réglage tient, sans rien")\n\n\n' \
             'func _poster(m):\n\tpass\n'
PHP_ACTIONS = "<?php\nswitch ($action) {\n    case 'liste':\n        break;\n}\n"
GRID_ZERO_TOML = r'''displayed_text = '\bI18n\.tn?\(\s*"((?:[^"\\]|\\.)*)"'

[documents]
patterns = ["tickets/T-[0-9][0-9][0-9][0-9]*.md"]

[communities]
separate = { hint = "hints", iteration = "journal" }

[[extensions]]
path = "tools/graphe_grid_zero.py"
with_readers = true

[[extensions]]
path = "tools/graphe_grid_zero.py"
'''


@grid_zero
def test_the_grid_zero_extension_links_the_state_the_actions_the_hints_and_the_journal(tmp_path: Path):
    host = _host(tmp_path, {
        "simulation/game/etat_de_jeu.py": STATE_PY, "godot/lecture.gd": READING_GD, "web/api.php": PHP_ACTIONS,
        "scenarios/lecon/scenario.toml": "[[hints]]\ntick = 4\ntext = \"Quand la fréquence dit « le réglage "
                                         "tient … », attendez.\"\n",
        "tickets/T-0998-essai.md": "---\nid: T-0998\ntitle: Essai\n---\n",
        "tickets/T-0999-essai.md": "---\nid: T-0999\ntitle: Essai\n---\n",
        "docs/moonshot/journal.md": "# Journal\n\n## Itération 7 - un essai (T-0998 à T-0999, 2026-11-05)\n",
        "graphe.toml": GRID_ZERO_TOML,
        "tools/graphe_grid_zero.py": (GRID_ZERO / "tools" / "graphe_grid_zero.py").read_text(encoding="utf-8"),
    }, tracked="simulation")
    r = _run(host, "build", env=_without_godot())
    assert r.returncode == 0, r.stderr
    data = json.loads((host / "graphe" / "graphe.json").read_bytes())
    links = {(e["source"], e["target"]): e["relations"] for e in data["links"]}
    f, field = "simulation_game_etat_de_jeu_", "simulation_game_etat_de_jeu_etatdejeu_raison_du_jour"
    assert "writes" in links[(f"{f}construire", field)]  # by keyword, in the state's constructor
    assert "reads" in links[("godot_lecture_texte", field)]  # by its key
    assert links[("godot_lecture_texte", "web_api_php_action_liste")] == ["sends"]
    assert "cites" in links[("hint_lecon_0", "godot_lecture_texte")]
    assert {t for s, t in links if s == "iteration_7"} == {"ticket_t_0998", "ticket_t_0999"}
    names, community_of = data["communities"], {n["id"]: n["community"] for n in data["nodes"]}
    assert names[str(community_of["iteration_7"])] == "journal" and names[str(community_of["hint_lecon_0"])] == "hints"
    assert set(data["coverage"]) == {"python", "godot", "js", "php", "dangling"}  # no server: no sites


# T-0010: every Markdown file is a document; a document cites a node it names and another by its identifier.
def test_a_host_with_its_identifier_pattern_links_its_documents(tmp_path: Path):
    host = _host(tmp_path, {
        "outils.py": 'def aider():\n    """Voir ISSUE-12."""\n    return 1\n',
        "issues/ISSUE-12-aide.md": "# L'aide\n\nVoir ISSUE-7, et `aider`. ISSUE-12 se cite.\n",
        "issues/ISSUE-7-debut.md": "# Le debut\n",
        "README.md": "Lire ISSUE-7.\n",
        "brouillon/notes.md": "ISSUE-12\n",
        "graphe.toml": r"""[documents]
patterns = ['issues', 'README.md']
identifier = '\bISSUE-\d+'
""",
    })
    r = _run(host, "build")
    assert r.returncode == 0, r.stderr
    data = json.loads((host / "graphe" / "graphe.json").read_bytes())
    links = {(e["source"], e["target"]): e["relations"] for e in data["links"]}
    a, b, readme = "ticket_issue_12", "ticket_issue_7", "document_readme_md"
    assert links[(a, b)] == ["cites"] and links[(readme, b)] == ["cites"]  # by the identifier
    assert (a, a) not in links  # not from itself to itself
    assert links[("outils_aider", a)] == ["cites"]  # the code that contains the identifier
    assert "names" in links[(a, "outils_aider")]  # between backticks
    assert not any(n["source_file"].startswith("brouillon/") for n in data["nodes"])  # outside the patterns
    r = _run(host, "explain", "aider")
    assert "ISSUE-12" in r.stdout


def test_without_configuration_every_markdown_file_is_a_document(tmp_path: Path):
    host = _host(tmp_path, {"outils.py": CALLEE, "travail.py": CALLER,
                            "README.md": "Le travail : `travailler`, voir T-0001.\n",
                            "tickets/T-0001-aide.md": "# L'aide\n"})
    r = _run(host, "search", "readme")
    assert r.returncode == 0 and "  README.md\n" in r.stdout, r.stdout + r.stderr
    r = _run(host, "path", "README.md", "aider")  # the document names `travailler`, which calls aider
    assert r.returncode == 0 and "names" in r.stdout and "calls" in r.stdout, r.stdout
    r = _run(host, "explain", "T-0001")
    assert "README.md" in r.stdout, r.stdout


def test_an_invalid_documents_section_stops_the_build(tmp_path: Path):
    for toml, key in (("[documents]\nidentifier = '('\n", "identifier"),
                      ("[documents]\npatterns = 'tickets'\n", "patterns"), ("documents = 1\n", "documents")):
        host = _host(tmp_path, {"outils.py": CALLEE, "graphe.toml": toml})
        r = _run(host, "build")
        assert r.returncode == 1 and key in r.stderr and "Traceback" not in r.stderr, r.stderr


def test_a_js_host_answers_explain_with_its_callers_and_tickets(tmp_path: Path):
    """T-0014: a .mjs function, its caller through an import, the ticket that names it."""
    host = _host(tmp_path, {
        "src/zones.mjs": "// T-0007: the climate zone\nexport function zoneFromCode(code) {\n  return code\n}\n",
        "src/compute.mjs": "import { zoneFromCode } from './zones.mjs'\n\nexport function compute(d) {\n"
                           "  return zoneFromCode(d)\n}\n",
        "tickets/T-0007-zones.md": "# Zones\n\n`zoneFromCode` reads the code.\n",
    }, tracked=".")
    r = _run(host, "explain", "zoneFromCode")
    assert r.returncode == 0, r.stderr
    assert "compute" in r.stdout and "T-0007" in r.stdout, r.stdout
    for arguments, expected in ((("callers", "zoneFromCode"), "compute"), (("path", "compute", "zoneFromCode"), "zoneFromCode"),
                                (("search", "zone"), "zoneFromCode")):
        r = _run(host, *arguments)
        assert r.returncode == 0 and expected in r.stdout, (arguments, r.stdout, r.stderr)


def test_a_svelte_host_answers_path_and_explain_with_its_issues(tmp_path: Path):
    """T-0015: from a Svelte component to the TS function it calls; issues named `NN-slug.md`, cited `ticket NN`."""
    host = _host(tmp_path, {
        "src/lib/eau.ts": "// La reserve du sol (ticket 34).\nexport function reserve(pluie: number): number {\n"
                          "  return pluie\n}\n",
        "src/Tuile.svelte": "<script lang=\"ts\">\n  import { reserve } from './lib/eau'\n\n"
                            "  function rafraichir(p: number) {\n    return reserve(p)\n  }\n</script>\n\n"
                            "<button onclick={() => rafraichir(1)}>ok</button>\n",
        "issues/34-reserve-du-sol.md": "# La reserve du sol\n",
        "issues/35-fiche.md": "# La fiche\n\nApres le ticket 34.\n",
        "graphe.toml": r"[documents]" "\n" r"identifier = '(?i)(?<=\bticket )\d{2}\b|^\d{2}(?=-)'" "\n",
    }, tracked=".")
    r = _run(host, "path", "rafraichir", "reserve")
    assert r.returncode == 0 and "calls" in r.stdout, r.stdout + r.stderr
    r = _run(host, "explain", "reserve")
    assert r.returncode == 0 and "rafraichir" in r.stdout and "La reserve du sol" in r.stdout, r.stdout
    r = _run(host, "explain", "34")
    assert "35" in r.stdout, r.stdout  # an issue cites another


def test_answers_name_each_neighbour_as_the_agent_designates_it_next(tmp_path: Path):
    """T-0016: neighbours by file, `Class.method:line`; tickets by their identifier; an ambiguous name by `file::name`."""
    host = _host(tmp_path, {
        "flotte.py": "class Flotte:\n    def avancer(self):\n        return 1\n\n\n"
                     "class Reparations:\n    def avancer(self):\n        return 2\n\n\n"
                     "def tout(f: Flotte, r: Reparations):\n    f.avancer()\n    r.avancer()\n",
        "tickets/T-0001-tout.md": "# Tout\n\n`tout` avance tout.\n",
        "paquet/moteur.py": "def vitesse():\n    return 3\n\n\nclass Moteur:\n    def vitesse(self):\n        return 4\n",
    }, tracked=".")
    r = _run(host, "explain", "paquet/moteur.py")  # a file as the answers print it
    assert r.returncode == 0 and "[file]" in r.stdout, r.stdout
    r = _run(host, "explain", "moteur.py::vitesse")  # the exact name, not Moteur.vitesse too
    assert r.returncode == 0 and "[function]" in r.stdout, r.stdout
    r = _run(host, "explain", "tout")
    assert r.returncode == 0, r.stderr
    assert "    flotte.py: Flotte.avancer:2, Reparations.avancer:7\n" in r.stdout, r.stdout
    assert "  names (1) [by name]\n    T-0001\n" in r.stdout and "tickets/T-0001-tout.md" not in r.stdout, r.stdout
    r = _run(host, "explain", "avancer")
    assert "  Flotte.avancer  flotte.py:2\n" in r.stdout, r.stdout
    r = _run(host, "callers", "flotte.py::Flotte.avancer")
    assert "  flotte.py: tout:11\n" in r.stdout, r.stdout
    r = _run(host, "search", "avancer")
    assert "  flotte.py: Flotte.avancer:2, Reparations.avancer:7\n" in r.stdout, r.stdout


# T-0017: the layout keeps the positions of the tool of 01a698e (T-0016 made it faster, not different).
LAYOUT_FIXTURE = Path(__file__).parent / "layout_01a698e.json"


def _many_communities(tmp_path: Path) -> Path:
    """40 files of 1 to 40 chained functions, none calling another file: tens of communities of varied sizes."""
    files = {f"m{k:02d}.py": "".join(f"def f{j}():\n    return f{j - 1}()\n\n\n" if j else "def f0():\n    return 0\n\n\n"
                                     for j in range(k)) for k in range(1, 41)}
    return _host(tmp_path, files, tracked=".")


def _page(host: Path) -> list[list]:
    """The nodes of `graphe.html`: [label, file, line, community, x, y, kind, id] each."""
    html = (host / "graphe" / "graphe.html").read_text(encoding="utf-8")
    return json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)[1])["n"]


def test_the_build_makes_no_page_and_view_makes_it_on_demand(tmp_path: Path):
    """T-0046: the layout and the page leave the build; `view` makes them, and opens the page on a node."""
    host = _host(tmp_path, {"outils.py": CALLEE, "travail.py": CALLER})
    r = _run(host, "build")
    assert r.returncode == 0, r.stderr
    assert not (host / "graphe" / "graphe.html").exists()
    assert not any("x" in n or "y" in n for n in json.loads((host / "graphe" / "graphe.json").read_bytes())["nodes"])
    r = _run(host, "view")
    assert r.returncode == 0, r.stderr
    page = (host / "graphe" / "graphe.html").resolve().as_uri()
    assert r.stdout.strip() == page
    assert {n[7] for n in _page(host)} == {"outils_aider", "travail_travailler", "outils", "travail"}
    r = _run(host, "view", "aider")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == page + "#outils_aider"
    r = _run(host, "view", "absent")
    assert r.returncode == 2 and "no node for 'absent'" in r.stdout, r.stdout


def test_the_layout_keeps_the_positions_of_the_tool_before_t_0016(tmp_path: Path):
    host = _many_communities(tmp_path)
    r = _run(host, "view")
    assert r.returncode == 0, r.stderr
    data = json.loads((host / "graphe" / "graphe.json").read_bytes())
    assert len(data["communities"]) > 30  # the spiral places many discs
    assert {n[7]: [n[4], n[5]] for n in _page(host)} == json.loads(LAYOUT_FIXTURE.read_bytes())


def test_a_community_above_1000_nodes_is_laid_out_in_its_disc(tmp_path: Path):
    host = _host(tmp_path, {"etoile.py": "def centre():\n    return 0\n\n\n" + "".join(
        f"def b{j}():\n    return centre()\n\n\n" for j in range(1100))}, tracked=".")
    r = _run(host, "view")
    assert r.returncode == 0, r.stderr
    nodes = _page(host)
    sizes = Counter(n[3] for n in nodes)
    big, size = sizes.most_common(1)[0]
    assert size > 1000  # the precondition: the sunflower's branch is taken
    points = [(n[4], n[5]) for n in nodes if n[3] == big]
    assert all(math.isfinite(x) and math.isfinite(y) for x, y in points)
    assert len(set(points)) == len(points)
    cx, cy = sum(x for x, _ in points) / len(points), sum(y for _, y in points) / len(points)
    radius = math.sqrt(size) * 1.6 + 1.0  # the disc of a community, as graphe.html draws it
    assert all(math.dist((x, y), (cx, cy)) <= radius for x, y in points)


def test_a_relation_with_a_sure_and_a_guessed_link_marks_the_guessed_one(tmp_path: Path):
    host = _host(tmp_path, {"outils.py": "class A:\n    def m(self):\n        return 1\n\n\ndef g():\n    return 2\n\n\n"
                                         "def f(x):\n    g()\n    x.m()\n"}, tracked=".")
    r = _run(host, "explain", "f")
    assert r.returncode == 0, r.stderr
    assert "  calls (2) [1 by name: ?]\n    outils.py: A.m:2?, g:6\n" in r.stdout, r.stdout
    r = _run(host, "callers", "A.m")  # T-0075: callers marks it too, once on the level when every caller is guessed
    assert "level 1 (1) [by name]:\n  outils.py: f:10\n" in r.stdout, r.stdout


def test_a_name_reexported_from_a_package_is_external(tmp_path: Path):
    """T-0018: dpe's `ui_helpers.mjs` re-exports `VirtualConsole` from `jsdom`."""
    host = _host(tmp_path, {
        "aides.mjs": "import { Console } from 'jsdom'\nexport { Console }\nexport { Fenetre } from 'jsdom'\n",
        "usage.mjs": "import { Console, Fenetre } from './aides.mjs'\n\nexport function f() {\n"
                     "  new Console()\n  return Fenetre()\n}\n",
    }, tracked=".")
    r = _run(host, "check")
    assert "== js: 2 sites classified {'external': 2}" in r.stdout, r.stdout + r.stderr


def test_a_svelte_prop_called_is_local(tmp_path: Path):
    """T-0019: 4cast's `let { onouvrir } = $props()`, then `onouvrir()`."""
    host = _host(tmp_path, {
        "src/Fiche.svelte": "<script lang=\"ts\">\n  let { onouvrir } = $props()\n\n"
                            "  function ouvrir() {\n    onouvrir()\n  }\n</script>\n\n<button>ok</button>\n",
    }, tracked=".")
    r = _run(host, "check")
    assert "== js: 2 sites classified" in r.stdout and "'local': 1" in r.stdout, r.stdout + r.stderr
    assert "unknown" not in r.stdout, r.stdout


def test_the_methods_of_an_object_literal_and_of_a_typed_variable_are_sure(tmp_path: Path):
    """T-0020: dpe's page object (`const p = await ouvrir()`, then `p.saisir()`), 4cast's harness
    (`const faux = new FauxAmont()`, then `faux.de()`), a module's object (`outils.m()`)."""
    host = _host(tmp_path, {
        "page.mjs": "export function ouvrir() {\n  return {\n    saisir(v) {\n      return v\n    },\n"
                    "    clic: () => 1,\n  }\n}\n",
        "autre.mjs": "export function autre() {\n  return { saisir() {}, clic() {} }\n}\n",  # the same names
        "faux.mjs": "export class Faux {\n  de() {}\n}\nexport class Vrai {\n  de() {}\n}\n",
        "outils.mjs": "export const outils = {\n  mesurer() {},\n}\n",
        "essai.mjs": "import { ouvrir } from './page.mjs'\nimport { Faux } from './faux.mjs'\n"
                     "import { outils } from './outils.mjs'\n\nconst faux = new Faux()\n\n"
                     "export async function essai() {\n  const p = await ouvrir()\n  p.saisir(1)\n  p.clic()\n"
                     "  faux.de()\n  outils.mesurer()\n}\n",
    }, tracked=".")
    r = _run(host, "explain", "essai")
    assert r.returncode == 0, r.stderr
    for expected in ("page.mjs: ouvrir:1, ouvrir.saisir:3, ouvrir.clic:6", "faux.mjs: Faux.de:2", "outils.mjs: outils.mesurer:2"):
        assert expected in r.stdout, r.stdout
    assert "by name" not in r.stdout, r.stdout


def test_a_test_callback_is_a_node_named_by_its_title(tmp_path: Path):
    """T-0021: dpe's `test('...', () => { compute(...) })`: the caller is the test, not its file."""
    host = _host(tmp_path, {
        "src/f.mjs": "export function f() {\n  return 1\n}\n",
        "test/f.test.mjs": "import { test, describe, it } from 'node:test'\nimport { f } from '../src/f.mjs'\n\n"
                           "test('f doubles', () => {\n  f()\n})\n\ndescribe('group', () => {\n"
                           "  it('f again', async () => f())\n})\n",
    }, tracked=".")
    r = _run(host, "explain", "f")
    assert r.returncode == 0, r.stderr
    assert "  calls (2)\n    test/f.test.mjs: f doubles:4, f again:9\n" in r.stdout, r.stdout


def test_the_calls_in_a_svelte_markup_belong_to_the_component(tmp_path: Path):
    """T-0022: 4cast's `onclick={() => rafraichir(1)}`, `{jourCourt(j.date)}`, `{#if ...}`, `{#each ... as j}`."""
    host = _host(tmp_path, {
        "src/Carte.svelte": "<script lang=\"ts\">\n  function rafraichir(n: number) {\n    return n\n  }\n"
                            "  function jourCourt(d: string) {\n    return d\n  }\n  function pret() {\n    return true\n  }\n"
                            "  function liste() {\n    return []\n  }\n  function fermer() {}\n</script>\n\n"
                            "<button onclick={fermer}>x</button>\n"
                            "{#if pret()}\n  {#each liste() as j (j.id)}\n    {@const c = jourCourt(j.date)}\n    <p>{c}</p>\n  {/each}\n"
                            "{:else}\n  <button onclick={() => rafraichir(1)} style=\"a\">ok</button>\n{/if}\n\n"
                            "<style>\n  p { color: red; }\n</style>\n",
    }, tracked=".")
    for name in ("rafraichir", "jourCourt", "pret", "liste"):
        r = _run(host, "explain", name)
        assert r.returncode == 0 and "  calls (1)\n    src/Carte.svelte\n" in r.stdout, (name, r.stdout, r.stderr)
    r = _run(host, "explain", "fermer")  # a handler passed by its name
    assert "  references (1)\n    src/Carte.svelte\n" in r.stdout, r.stdout


def test_a_php_file_calls_from_its_top_level(tmp_path: Path):
    """T-0023: 4cast's `api/index.php` routes at the top of the file (`route_zones($db, ...)`)."""
    host = _host(tmp_path, {
        "api/index.php": "<?php\n$db = ouvrir();\nroute_zones($db);\n\nfunction route_zones($db)\n{\n"
                         "    return aide();\n}\n\nfunction aide()\n{\n    return 1;\n}\n\nfunction ouvrir()\n{\n    return 2;\n}\n",
    }, tracked=".")
    r = _run(host, "explain", "route_zones")
    assert r.returncode == 0 and "  calls (1)\n    api/index.php\n" in r.stdout, r.stdout + r.stderr
    r = _run(host, "explain", "aide")  # a body's call stays its own
    assert "  calls (1) [by name]\n    api/index.php: route_zones:5\n" in r.stdout, r.stdout


def test_a_document_names_a_function_written_with_its_arguments(tmp_path: Path):
    """T-0024: 4cast's issue 48 writes `ndviRecent(geometrie, aujourdhui)`."""
    host = _host(tmp_path, {"outils.py": CALLEE, "tickets/T-0001-aide.md": "# Aide\n\n`aider(1, 2)` aide.\n"},
                 tracked=".")
    r = _run(host, "explain", "aider")
    assert r.returncode == 0 and "  names (1) [by name]\n    T-0001\n" in r.stdout, r.stdout + r.stderr


def test_explain_says_why_it_could_not_attribute_the_calls_of_its_name(tmp_path: Path):
    """T-0025, T-0074: Django's `Model.objects.filter()`: two methods bear the name; a bare call the reader cannot
    attribute; a module of ours that lacks the name."""
    host = _host(tmp_path, {"requete.py": "import outils\n\n\nclass Requete:\n    def filtrer(self):\n        return 1\n\n\n"
                                          "class Autre:\n    def filtrer(self):\n        return 2\n\n\n"
                                          "def f(x, y):\n    x.filtrer()\n    outils.filtrer()\n    filtrer()\n"
                                          "    return y.filtrer()\n",
                            "outils.py": "def aide():\n    return 1\n"}, tracked=".")
    lines = ("  + 4 calls named `filtrer` the graph could not attribute:\n"
             "    2 between 2 definitions: Requete.filtrer, Autre.filtrer\n"
             "    1 on a receiver of unknown type\n"
             "    1 to a definition outside the host\n")
    for arguments in (("explain", "Requete.filtrer"), ("callers", "Requete.filtrer")):
        r = _run(host, *arguments)
        assert r.returncode == 0 and lines in r.stdout, (arguments, r.stdout, r.stderr)
    r = _run(host, "explain", "f")
    assert "could not attribute" not in r.stdout, r.stdout  # nothing missed for a name nobody calls
    stored = host / "graphe" / "graphe.json"  # a graph built by 0.1.1, one count per name, newer than the tool
    data = json.loads(stored.read_bytes())
    stored.write_text(json.dumps({**data, "unattributed": {"filtrer": 4}}), encoding="utf-8")
    r = _run(host, "explain", "Requete.filtrer")
    assert r.returncode == 0 and lines in r.stdout, r.stdout + r.stderr


def test_above_five_definitions_of_the_name_only_their_count(tmp_path: Path):
    """T-0074: protobuf's 407 `pushLimit` calls; a list of candidates longer than five tells no more than a grep."""
    classes = "".join(f"class C{i}:\n    def m(self):\n        return {i}\n\n\n" for i in range(6))
    host = _host(tmp_path, {"c.py": classes + "def f(x):\n    return x.m()\n"}, tracked=".")
    r = _run(host, "explain", "C0.m")
    assert r.returncode == 0 and "\n    1 between 6 definitions\n" in r.stdout, r.stdout + r.stderr


def test_a_common_name_is_its_own_cause(tmp_path: Path):
    """T-0074: Ruby's `each`, a common name: a grep would return every loop."""
    host = _host(tmp_path, {"liste.rb": "class Liste\n  def each\n    1\n  end\nend\n\n"
                                        "def parcourir(x)\n  x.each\nend\n"}, tracked=".")
    r = _run(host, "explain", "Liste.each")
    assert r.returncode == 0 and "\n    1 on a common name\n" in r.stdout, r.stdout + r.stderr


def test_a_method_call_on_a_receiver_of_unknown_type_is_its_own_cause(tmp_path: Path):
    """T-0074: `x.filtrer()` in JavaScript, where no method bears the name: what `x` is, the reader cannot tell."""
    host = _host(tmp_path, {"x.js": "function filtrer() {\n  return 1\n}\n\nfunction g(x) {\n  return x.filtrer()\n}\n"},
                 tracked=".")
    r = _run(host, "explain", "filtrer")
    assert r.returncode == 0 and "\n    1 on a receiver of unknown type\n" in r.stdout, r.stdout + r.stderr


def test_the_svelte_markup_reader_holds_on_awaits_line_breaks_and_unknown_tags(tmp_path: Path):
    """T-0022, after the review: `{#await p then v}`, a keyword before a line break, `{@attach}`, and an
    expression left open do not break the component's script."""
    host = _host(tmp_path, {
        "src/Fiche.svelte": "<script lang=\"ts\">\n  function charger() {\n    return 1\n  }\n"
                            "  function voir(x: number) {\n    return x\n  }\n  function infobulle() {}\n</script>\n\n"
                            "{#await charger() then v}\n  <p>{voir(v)}</p>\n{/await}\n{#if\n  voir(2)}\n  <i {@attach infobulle()}></i>\n{/if}\n"
                            "<p>{voir(3)</p>\n<style>\n  p { color: red; }\n</style>\n",
        "test/t.mjs": "export function f(it) {\n  return new it('x', () => 1)\n}\n",
    }, tracked=".")
    r = _run(host, "check")
    assert r.returncode == 0, r.stdout + r.stderr
    r = _run(host, "explain", "voir")
    assert "  calls (1)\n    src/Fiche.svelte\n" in r.stdout, r.stdout
    r = _run(host, "explain", "charger")
    assert "  calls (1)\n    src/Fiche.svelte\n" in r.stdout, r.stdout


def test_a_required_name_is_not_hidden_and_a_function_is_not_its_returned_object(tmp_path: Path):
    """After the review of T-0019 and T-0020: `const { aider } = require('./x.js')` stays a name of ours, and
    `ouvrir.click()` (a property of the function) is not the method of the object it returns."""
    host = _host(tmp_path, {
        "x.js": "function aider() {\n  return 1\n}\nmodule.exports = { aider }\n",
        "y.js": "const { aider } = require('./x.js')\n\nfunction y() {\n  return aider()\n}\n",
        "page.mjs": "export function ouvrir() {\n  return { click() {} }\n}\n\nexport function f() {\n  ouvrir.click()\n}\n",
    }, tracked=".")
    r = _run(host, "explain", "aider")
    assert "y.js: y:3" in r.stdout, r.stdout + r.stderr
    r = _run(host, "explain", "ouvrir.click")
    assert "what calls it:\n  contains (1)" in r.stdout and "calls (" not in r.stdout.split("what calls it:")[1], r.stdout


def _commit(host: Path) -> str:
    """Commits the whole tree (no identity needed on CI); its sha."""
    subprocess.run(["git", "add", "-A"], cwd=host, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"], cwd=host, check=True)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=host, capture_output=True, text=True).stdout.strip()


def _write(host: Path, rel: str, text: str) -> None:
    (host / rel).write_bytes(text.encode("utf-8"))  # bytes: no CRLF on Windows, the diff stays the lines changed


def test_affected_lists_a_changed_function_and_its_callers(tmp_path: Path):
    """T-0075."""
    host = _host(tmp_path, {}, tracked=".")
    _write(host, "outils.py", CALLEE)
    _write(host, "travail.py", CALLER)
    _commit(host)
    _write(host, "outils.py", "def aider():\n    return 2\n")
    _write(host, "neuf.py", "def neuf():\n    return 0\n\n\nneuf()\n")  # untracked: new as a whole
    r = _run(host, "affected")
    assert r.returncode == 0, r.stderr
    assert "touched (3):\n  neuf.py: (file), neuf:1\n  outils.py: aider:1\n" in r.stdout, r.stdout
    assert "aider (outils.py:1):\nlevel 1 (1):\n  travail.py: travailler:4\n" in r.stdout, r.stdout


def test_affected_against_a_revision_with_the_callers_callers(tmp_path: Path):
    """T-0075: a branch's changes against its base; --depth 2."""
    host = _host(tmp_path, {}, tracked=".")
    _write(host, "outils.py", CALLEE)
    _write(host, "travail.py", CALLER + "\n\ndef journee():\n    return travailler()\n")
    base = _commit(host)
    _write(host, "outils.py", "def aider():\n    return 2\n")
    _commit(host)
    assert "nothing touched against HEAD" in _run(host, "affected").stdout  # the tree is HEAD's
    r = _run(host, "affected", base)
    assert r.returncode == 0 and "travail.py: travailler:4" in r.stdout and "journee" not in r.stdout, r.stdout
    r = _run(host, "affected", base, "--depth", "2")
    assert "level 2 (1):\n  travail.py: journee:8\n" in r.stdout, r.stdout


def test_affected_lists_a_top_level_change_by_its_file_and_a_removed_function_apart(tmp_path: Path):
    """T-0075."""
    host = _host(tmp_path, {}, tracked=".")
    _write(host, "outils.py", CALLEE + "\n\ndef ancien():\n    return 0\n")
    _write(host, "travail.py", CALLER)
    _commit(host)
    _write(host, "outils.py", "import os\n" + CALLEE)  # a line added at the top, `ancien` removed after `aider`
    r = _run(host, "affected")
    assert r.returncode == 0, r.stderr
    assert "touched (1):\n  outils.py\n" in r.stdout, r.stdout
    assert "removed (no longer in the graph):\n  outils.py: ancien\n" in r.stdout, r.stdout


def test_affected_with_no_change_says_nothing_is_touched(tmp_path: Path):
    host = _host(tmp_path, {}, tracked=".")
    _write(host, "outils.py", CALLEE)
    _commit(host)
    r = _run(host, "affected")
    assert r.returncode == 0 and r.stdout == "nothing touched against HEAD (in what the graph reads)\n", r.stdout
    r = _run(host, "affected", "nonexistent-rev")
    assert r.returncode == 1 and r.stderr.startswith("graphe: git merge-base: "), r.stderr


def test_affected_against_a_branch_that_moved_on_lists_only_the_changes_since_the_base(tmp_path: Path):
    """T-0075, after the review: what `amont` did after the branch left it is not the branch's change."""
    host = _host(tmp_path, {}, tracked=".")
    _write(host, "outils.py", CALLEE)
    _write(host, "travail.py", CALLER)
    _commit(host)
    subprocess.run(["git", "branch", "amont"], cwd=host, check=True)
    _write(host, "outils.py", "def aider():\n    return 2\n")
    _commit(host)
    subprocess.run(["git", "checkout", "-q", "amont"], cwd=host, check=True)
    _write(host, "travail.py", CALLER + "\n\ndef nouveau():\n    return 0\n")
    _commit(host)
    subprocess.run(["git", "checkout", "-q", "-"], cwd=host, check=True)
    r = _run(host, "affected", "amont")
    assert r.returncode == 0 and "touched (1):\n  outils.py: aider:1\n" in r.stdout, r.stdout
    assert "nouveau" not in r.stdout and "removed" not in r.stdout, r.stdout


def test_affected_lists_the_definitions_of_a_deleted_file_and_a_method_removed_from_its_class(tmp_path: Path):
    """T-0075, after the review: a deleted file, a method at the end of its class, a path with a space, Ruby's
    `def self.f`; a function moved to another file is not removed."""
    host = _host(tmp_path, {}, tracked=".")
    _write(host, "a b.py", "class K:\n    def m(self):\n        return 1\n\n    def n(self):\n        return 2\n")
    _write(host, "vieux.py", "def ancien():\n    return 0\n")
    _write(host, "outils.py", CALLEE + "\n\ndef bouge():\n    return 3\n")
    _write(host, "travail.py", CALLER)
    _write(host, "r.rb", "class R\n  def self.cree\n    1\n  end\n\n  def garde\n    2\n  end\nend\n")
    _commit(host)
    (host / "vieux.py").unlink()
    _write(host, "a b.py", "class K:\n    def m(self):\n        return 1\n")
    _write(host, "outils.py", CALLEE)
    _write(host, "travail.py", CALLER + "\n\ndef bouge():\n    return 3\n")
    _write(host, "r.rb", "class R\n  def garde\n    2\n  end\nend\n")
    r = _run(host, "affected")
    assert r.returncode == 0, r.stderr
    assert "\n  a b.py: K:1\n" in r.stdout and "\n  travail.py: bouge:8\n" in r.stdout, r.stdout
    assert "removed (no longer in the graph):\n  a b.py: n\n  r.rb: cree\n  vieux.py: ancien\n" in r.stdout, r.stdout


def test_affected_reads_a_diff_with_a_form_feed_and_a_removed_top_level_line(tmp_path: Path):
    """T-0075, after the review: a page break (`^L`) is a line of its own; a top-level line removed after a function
    is the file's, not the function's."""
    host = _host(tmp_path, {}, tracked=".")
    _write(host, "o.py", "def a():\n    return 1\n\x0c\ndef b():\n    return 2\n")
    _write(host, "p.py", "def c():\n    return 1\n\n\nc()\n")
    _commit(host)
    _write(host, "o.py", "def a():\n    return 1\n")
    _write(host, "p.py", "def c():\n    return 1\n")
    r = _run(host, "affected")
    assert r.returncode == 0, r.stderr
    assert "touched (2):\n  o.py\n  p.py\n" in r.stdout and "removed (no longer in the graph):\n  o.py: b\n" in r.stdout, \
        r.stdout
