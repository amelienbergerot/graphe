"""The code graph: what its readers link.

The readers play on a small repository written here; the tests marked
`grid_zero` on the real Grid Zero (conftest.py). Its coverage and its
reference test stay in Grid Zero (T-0003).
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest

from graphe import cli, python
from conftest import grid_zero

ENGINE_PY = '''
from dataclasses import dataclass
import re

from simulation.flotte import Flotte


@dataclass
class Reglage:
    flotte: Flotte

    def appliquer(self) -> None:
        self.flotte.pousser()


class Moteur:
    def __init__(self) -> None:
        self.flotte = Flotte()
        self.reglages: list[Reglage] = []

    @property
    def charge(self) -> float:
        return self.flotte.mesurer()

    def fabrique(self):
        return Flotte()

    def pas(self) -> None:
        for r in self.reglages:
            r.appliquer()
        self.fabrique().pousser()
        x = self.charge
        for m in re.finditer("a", "abc"):
            m.start()
        def interne():
            return self.flotte.mesurer()
        interne()
        from simulation.flotte import vider
        vider(self.flotte)
        rappel = sorted([1], key=cle)
        return x, rappel


def cle(v):
    return v
'''

FLEET_PY = '''
class Flotte:
    def pousser(self) -> None:
        pass

    def mesurer(self) -> float:
        return 0.0

    def start(self) -> None:
        pass


def vider(flotte: Flotte) -> None:
    flotte.pousser()
'''

SERVER_PY = '''
from simulation.moteur import Moteur

COMMANDES = frozenset({"pas", "rien", "liste", "relister"})


def handle_command(moteur: Moteur, message: dict) -> dict:
    cmd = message.get("cmd")
    if cmd == "pas":
        moteur.pas()
        return {"ok": True}
    if cmd in ("liste", "relister"):
        moteur.fabrique()
        return {"ok": True}
    return {"ok": False}
'''


@pytest.fixture
def reader(tmp_path: Path) -> python.Reader:
    (tmp_path / "simulation").mkdir()
    paths = []
    for name, text in (("__init__", ""), ("moteur", ENGINE_PY), ("flotte", FLEET_PY), ("server", SERVER_PY)):
        path = tmp_path / "simulation" / f"{name}.py"
        path.write_bytes(textwrap.dedent(text).encode("utf-8"))
        paths.append(path)
    return python.Reader(paths, root=tmp_path)


def _links(reader, relation: str = "calls") -> set[tuple[str, str]]:
    return {(e["source"], e["target"]) for e in reader.links if e["relation"] == relation
            and e["confidence"] == "EXTRACTED"}


M, F, S = "simulation_moteur_", "simulation_flotte_", "simulation_server_"


def test_a_call_follows_the_type_of_attributes(reader):
    calls = _links(reader)
    # self.flotte = Flotte() in __init__; an annotated dataclass field
    assert (f"{M}moteur_charge", f"{F}flotte_mesurer") in calls
    assert (f"{M}reglage_appliquer", f"{F}flotte_pousser") in calls
    # the element of an annotated list, the inferred return of a method
    assert (f"{M}moteur_pas", f"{M}reglage_appliquer") in calls
    assert (f"{M}moteur_pas", f"{F}flotte_pousser") in calls


def test_properties_nested_functions_local_imports_and_callbacks(reader):
    calls = _links(reader)
    assert (f"{M}moteur_pas", f"{M}moteur_charge") in calls  # reading a property calls it
    assert (f"{M}moteur_pas", f"{M}moteur_pas_interne") in calls
    assert (f"{M}moteur_pas_interne", f"{F}flotte_mesurer") in calls
    assert (f"{M}moteur_pas", f"{F}vider") in calls  # imported in the function
    assert (f"{M}moteur_pas", f"{M}cle") in _links(reader, "references")


def test_a_module_variable_computed_from_itself_ends(tmp_path: Path):
    """T-0015, 4cast's script: `for l in rows: l = l[1:]` at the top of a module looped the typing forever."""
    path = tmp_path / "script.py"
    path.write_text("rows = [[1]]\nfor l in rows:\n    l = l[1:]\n    l.count(1)\n", encoding="utf-8")
    python.Reader([path], root=tmp_path)


def test_the_cache_gives_the_same_reading_and_reads_an_edited_file_again(reader, tmp_path: Path):
    """T-0026: each file's parse and definitions come from the cache; the resolution is redone in full."""
    paths = sorted((tmp_path / "simulation").glob("*.py"))
    def read(cache):
        r = python.Reader(paths, root=tmp_path, cache=cache)
        return r.nodes, r.links, r.sites
    cache = tmp_path / "cache"
    assert read(cache) == read(None)
    assert any(cache.iterdir())
    assert read(cache) == read(None)  # warm
    fleet = tmp_path / "simulation" / "flotte.py"
    fleet.write_text(fleet.read_text(encoding="utf-8") + "\n\ndef remplir(flotte: Flotte) -> None:\n"
                     "    flotte.pousser()\n", encoding="utf-8")
    edited = read(cache)
    assert edited == read(None)
    assert f"{F}remplir" in {n["id"] for n in edited[0]}


def test_a_module_resolves_by_its_import_name_and_a_shared_one_by_neither(tmp_path: Path):
    """T-0096: in a src/ layout `src/pkg/a.py` is imported as `pkg.a`; two files of one import name, neither."""
    sources = {"src/pkg/__init__.py": "", "src/pkg/a.py": "def f():\n    pass\n",
               "src/pkg/b.py": "from pkg import a\nfrom pkg.a import f\nfrom pkg.sub.d import e\n\n\n"
                               "def g():\n    a.f()\n    f()\n    e()\n",
               "src/pkg/sub/d.py": "def e():\n    pass\n",  # a folder without __init__.py inside a package
               "one/apps.py": "def h():\n    pass\n", "two/apps.py": "def h():\n    pass\n",
               "c.py": "import apps\nfrom apps import h\n\n\ndef k():\n    apps.h()\n    h()\n"}
    for rel, text in sources.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    read = python.Reader([tmp_path / rel for rel in sources], root=tmp_path)
    calls = [(e["source"], e["target"], e["confidence"]) for e in read.links if e["relation"] == "calls"]
    assert calls.count(("src_pkg_b_g", "src_pkg_a_f", "EXTRACTED")) == 2
    assert ("src_pkg_b_g", "src_pkg_sub_d_e", "EXTRACTED") in calls
    assert not [c for c in calls if c[0] == "c_k"]
    assert not [e for e in read.links if e["source"] == "c" and e["relation"] == "imports"]
    assert {n["name"] for n in read.nodes if n["kind"] == "file"} \
        == {"src.pkg", "src.pkg.a", "src.pkg.b", "src.pkg.sub.d", "one.apps", "two.apps", "c"}  # their path name


def test_an_import_through_a_leading_folder_without_init_resolves_by_the_path(tmp_path: Path):
    """T-0100: `import top.pkg.mod`, `top/` without `__init__.py`: the module's import name is `pkg.mod`, its path
    `top.pkg.mod` a second key. A path two files bear (`x/a.py`, `x/a/__init__.py`) resolves to neither."""
    sources = {"top/pkg/__init__.py": "", "top/pkg/mod.py": "def f():\n    pass\n",
               "x/a.py": "def g():\n    pass\n", "x/a/__init__.py": "def g():\n    pass\n",
               "c.py": "import top.pkg.mod\nimport x.a\nfrom top.pkg.mod import f\nfrom x.a import g\n\n\n"
                       "def k():\n    f()\n    g()\n"}
    for rel, text in sources.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    read = python.Reader([tmp_path / rel for rel in sources], root=tmp_path)
    assert ("c", "top_pkg_mod") in _links(read, "imports")
    assert ("c_k", "top_pkg_mod_f") in _links(read)
    assert not [e for e in read.links if e["source"] in ("c", "c_k") and e["target"].startswith("x_a")]


def test_import_a_dotted_module_then_call_through_it(tmp_path: Path):
    """T-0096: `import pkg.a` binds `pkg`; `pkg.a.f()` goes through the package to its submodule, at the top of a
    file and in a function, and the file imports `pkg.a` as well as `pkg`. A name the package binds itself, by a
    def or an import, is its own, though a submodule bears it."""
    sources = {"pkg/__init__.py": "from .x import g as h\nfrom .y import y\n\n\ndef b():\n    pass\n",
               "pkg/a.py": "def f():\n    pass\n", "pkg/b.py": "", "pkg/h.py": "", "pkg/x.py": "def g():\n    pass\n",
               "pkg/y.py": "def y():\n    pass\n", "pkg/sub/__init__.py": "", "pkg/sub/deep.py": "def z():\n    pass\n",
               "c.py": "import pkg.a\nimport pkg.sub.deep\n\n\n"
                       "def k():\n    pkg.a.f()\n    pkg.b()\n    pkg.h()\n    pkg.y()\n    pkg.sub.deep.z()\n\n\n"
                       "def m():\n    import pkg.a\n    pkg.a.f()\n"}
    for rel, text in sources.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    read = python.Reader([tmp_path / rel for rel in sources], root=tmp_path)
    assert {("c_k", "pkg_a_f"), ("c_k", "pkg___init___b"), ("c_k", "pkg_x_g"), ("c_k", "pkg_y_y"),
            ("c_k", "pkg_sub_deep_z"), ("c_m", "pkg_a_f")} <= _links(read)
    assert {("c", "pkg___init__"), ("c", "pkg_a"), ("c", "pkg_sub___init__"), ("c", "pkg_sub_deep"),
            ("c_m", "pkg_a")} <= _links(read, "imports")


def test_a_package_s_import_of_its_submodule_wins_over_its_fallback_its_variable_does_not(tmp_path: Path):
    """T-0096: `from . import a` with `a = None` beside it in an except is the submodule; a variable `b` of the
    package is no submodule `b`; `import pkg.sub.deep as d` imports `pkg.sub` too."""
    sources = {"pkg/__init__.py": "try:\n    from . import a\nexcept ImportError:\n    a = None\nb = 1\n",
               "pkg/a.py": "def f():\n    pass\n", "pkg/b.py": "def g():\n    pass\n",
               "pkg/sub/__init__.py": "", "pkg/sub/deep.py": "",
               "q/__init__.py": "try:\n    import q.a\nexcept ImportError:\n    a = None\n", "q/a.py": "def f():\n    pass\n",
               "c.py": "import pkg\nimport pkg.sub.deep as d\nfrom pkg import a\nimport q\n\n\n"
                       "def k():\n    pkg.a.f()\n    a.f()\n    pkg.b.g()\n    q.a.f()\n"}
    for rel, text in sources.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    read = python.Reader([tmp_path / rel for rel in sources], root=tmp_path)
    calls = [(e["source"], e["target"], e["confidence"]) for e in read.links if e["relation"] == "calls"]
    assert calls.count(("c_k", "pkg_a_f", "EXTRACTED")) == 2
    assert ("c_k", "q_a_f", "EXTRACTED") in calls  # `import q.a` in q, the plain form
    assert not [c for c in calls if c[1] == "pkg_b_g"]
    assert {("pkg___init__", "pkg_a"), ("c", "pkg_a"), ("c", "pkg_sub___init__"), ("c", "pkg_sub_deep")} \
        <= _links(read, "imports")


def test_an_object_outside_the_repository_does_not_take_our_names(reader):
    """m.start() on a re.Match: a name that Flotte.start bears, on a
    receiver that comes from elsewhere - no link, not even by the name."""
    to_start = [e for e in reader.links if e["target"] == f"{F}flotte_start" and e["relation"] != "method"]
    assert to_start == []
    site = next(s for s in reader.sites if s["expr"] == "m.start")
    assert site["verdict"] == "external"


def test_find_a_node_by_its_name(reader):
    import networkx as nx
    g = nx.DiGraph()
    for n in reader.nodes:
        g.add_node(n["id"], **n)
    assert cli.find(g, "Moteur.pas") == [f"{M}moteur_pas"]
    assert cli.find(g, "moteur.py::pas") == [f"{M}moteur_pas"]
    assert set(cli.find(g, "pousser")) == {f"{F}flotte_pousser"}
    assert cli.find(g, "inexistant") == []


PHP = """<?php
// Le point d'entree.
function gz_lire($x) {
    return gz_valider($x);
}

function gz_valider($x) {
    return $x;
}

function gz_noter($x): int
{
    return gz_valider($x);
}

switch ($action) {
    case 'liste':
    case 'relister':
        gz_lire(1);
        break;
}
"""


def test_extent_and_notes_of_a_body():
    from graphe import core as gc
    lines = textwrap.dedent('''\
        # Le pas du moteur,
        # en deux lignes.
        @decorateur
        def pas(a,
                b):
            x = 1

            # un commentaire dedans
            return x
        AUTRE = 2
    ''').splitlines()
    assert gc.extent(lines, 4) == 9
    assert gc.notes(lines, 4) == "Le pas du moteur, en deux lignes."
    assert gc.extent(PHP.splitlines(), 3) == 5  # the closing brace belongs to the block
    assert gc.extent(PHP.splitlines(), 11) == 14  # the opening one too, on its own line after the signature
    assert gc.extent(["def f():", "    return 1", "{", "  'a': 1", "}"], 1) == 2  # not after a body


def test_an_extent_reads_strings_as_strings():
    """T-0083: the parentheses of a string do not open a signature; a string over several lines is the block's."""
    from graphe import core as gc
    assert gc.extent(['MOTIF = r"\\((a)"', "", "def f():", "    return 1"], 1) == 1
    toml = ["CONFIG = r'''cle = '\\(x'", "", "[section]", "a = 1", "'''", "", "", "def f():", "    return 1"]
    assert gc.extent(toml, 1) == 5
    assert gc.extent(['def f():', '    """Doc,', "", "sans retrait.", '    """', "    return 1", "", "X = 2"], 1) == 6
    assert gc.extent(["def f(a,", "b):", "    return 1"], 1) == 1  # a line back at the indentation ends a signature
    assert gc.extent(["def f(", "    a,", "):", "    return a"], 1) == 4


def _enrich(g, root: Path) -> None:
    """The core, on sources written in `root`: a git repository, from which it draws the documents (T-0010)."""
    from graphe import core
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    core.enrich(g, root)


def test_enrich_links_variables_and_finds_by_the_text(tmp_path: Path):
    import networkx as nx

    (tmp_path / "simulation").mkdir()
    path = tmp_path / "simulation" / "jeu.py"
    path.write_bytes(textwrap.dedent('''\
        LIMITE = 3
        compte = 0


        # La clarte du jour.
        def avancer():
            global compte
            compte += LIMITE
            return tr("Réseau stable")
    ''').encode("utf-8"))
    # T-0009: the pattern of the call that displays a text comes from the host.
    (tmp_path / "graphe.toml").write_text("displayed_text = '\\btr\\(\"([^\"]*)\"'\n", encoding="utf-8")
    read = python.Reader([path], root=tmp_path)
    g = nx.DiGraph()
    for n in read.nodes:
        g.add_node(n["id"], **n)
    _enrich(g, tmp_path)
    f = "simulation_jeu_"
    assert "reads" in g[f"{f}avancer"][f"{f}limite"]["relations"]
    assert "writes" in g[f"{f}avancer"][f"{f}compte"]["relations"]
    assert g.nodes[f"{f}avancer"]["texts"] == ["Réseau stable"]
    assert [n for n, _ in cli.search_nodes(g, "réseau stable")] == [f"{f}avancer"]
    assert [n for n, _ in cli.search_nodes(g, "clarte")] == [f"{f}avancer"]
    assert [n for n, _ in cli.search_nodes(g, "def avancer")] == [f"{f}avancer"]


def test_a_value_written_on_both_sides(tmp_path: Path):
    """T-0354: a value written in Python and in GDScript becomes a node, in its community."""
    import networkx as nx

    for d in ("serveur", "godot"):
        (tmp_path / d).mkdir(parents=True)
    (tmp_path / "serveur" / "etat.py").write_bytes(textwrap.dedent('''\
        def construire(x):
            if x:
                return {"raison": "coupee"}
            raison = "voisin"
            return raison
    ''').encode("utf-8"))
    (tmp_path / "godot" / "lecture.gd").write_bytes(textwrap.dedent('''\
        func texte(raison: String) -> String:
        \tif raison == "coupee":
        \t\treturn "ok"
        \treturn ""
    ''').encode("utf-8"))
    read = python.Reader(sorted((tmp_path / "serveur").rglob("*.py")), root=tmp_path)
    g = nx.DiGraph()
    for n in read.nodes:
        g.add_node(n["id"], **n)
    g.add_node("godot_lecture_texte", id="godot_lecture_texte", label="texte()", kind="function",
               source_file="godot/lecture.gd", source_location="L1", name="texte")
    _enrich(g, tmp_path)
    assert {s for s, _ in g.in_edges("value_coupee")} == {"serveur_etat_construire", "godot_lecture_texte"}
    assert "value_voisin" not in g  # written on one side only
    assert [n for n, _ in cli.search_nodes(g, "coupee")] == ["value_coupee"]
    community_of, names = cli.communities(g)
    assert names[community_of["value_coupee"]] == "values"


def test_a_keyed_link_from_the_body_that_names_a_key_to_the_code_that_answers_it(tmp_path: Path):
    """T-0047: 4cast's front names its routes, its PHP answers them; `sends`, by the key alone."""
    from graphe import core
    import networkx as nx

    (tmp_path / "front.ts").write_text(textwrap.dedent('''\
        export const lister = () => api<Zone[]>("zones");
        export const lire = (id: number) => api<Zone>(`zones/${id}?champ=${x}`);
        export const meteo = (q: string) =>
          api(`meteo?q=${q}`);
        // api("session") in a comment names nothing
        export const tout = (c: string) => api(`${c}`);
        export const perdu = () => api("inconnue");
        export const session = () => api("session");
    '''), encoding="utf-8")
    (tmp_path / "index.php").write_text(textwrap.dedent('''\
        <?php
        if ($chemin === '/api/session') {
            connecter();
        }
        match (true) {
            $chemin === '/api/meteo' => route_meteo(),
        };
        function route_zones($chemin) {
            if ($chemin === '/api/zones') {
                return 1;
            }
            if (preg_match('#^/api/zones/(\\d+)$#', $chemin, $m)) {
                return 2;
            }
        }
        function route_meteo() {
        }
    '''), encoding="utf-8")
    (tmp_path / "graphe.toml").write_text(textwrap.dedent('''\
        [keys]
        names = \'\'\'\\bapi(?:<.*?>)?\\(\\s*[`"']([^`"'?]+)\'\'\'
        answers = \'\'\'(?:\\$chemin\\s*===\\s*'|preg_match\\('#\\^)/api/([^'#$]+)\'\'\'
        parameters = '\\$\\{[^}]*\\}|\\([^)]*\\)'
    '''), encoding="utf-8")
    g = nx.DiGraph()
    nodes = [("f", "front.ts", "file", 1), ("lister", "front.ts", "function", 1), ("lire", "front.ts", "function", 2),
             ("meteo", "front.ts", "function", 3), ("tout", "front.ts", "function", 6),
             ("perdu", "front.ts", "function", 7), ("session", "front.ts", "function", 8),
             ("index", "index.php", "file", 1), ("route_zones", "index.php", "function", 8),
             ("route_meteo", "index.php", "function", 16), ("connecter", "session.php", "function", 1)]
    for n, rel, kind, line in nodes:
        g.add_node(n, id=n, label=n, kind=kind, source_file=rel, source_location=f"L{line}", name=n)
    for t, line in (("connecter", 3), ("route_meteo", 6)):
        g.add_edge("index", t, relations={"calls"}, confidence="INFERRED", locations=[f"index.php:{line}"],
                   contexts=[])
    _enrich(g, tmp_path)
    sends = {(s, t, tuple(d["contexts"]), d["locations"][0]) for s, t, d in g.edges(data=True)
             if "sends" in d["relations"]}
    assert sends == {
        ("lister", "route_zones", ("zones",), "front.ts:1"),       # a one-line arrow names on its head
        ("lire", "route_zones", ("zones/*",), "front.ts:2"),       # `${id}` and `(\d+)`, the query string out
        ("meteo", "route_meteo", ("meteo",), "front.ts:4"),        # the second line; the line's call answers
    }  # `tout` (`*` alone), `perdu` (no answer) and `session` (a top-level `if` without a call: not its file) link
    # nothing, nor the comment
    assert all(g[s][t]["confidence"] == "INFERRED" for s, t, *_ in sends)
    for keys, message in (("names = 'api'\nanswers = '(x)'", "keys.names"), ("names = '(x)'", "answers")):
        (tmp_path / "graphe.toml").write_text(f"[keys]\n{keys}\n", encoding="utf-8")
        with pytest.raises(RuntimeError, match=message):
            core.enrich(nx.DiGraph(), tmp_path)


def test_fields_import_aliases_and_tickets(tmp_path: Path):
    """BACKLOG.md: the fields of a class, the Python import alias, the
    ticket cited by the code and the one that names a function."""
    import networkx as nx

    (tmp_path / "simulation").mkdir()
    (tmp_path / "tickets").mkdir()
    (tmp_path / "simulation" / "__init__.py").write_bytes(b"")
    (tmp_path / "simulation" / "aides.py").write_bytes(b"PREVISIONNISTE = 'p'\n")
    (tmp_path / "simulation" / "jeu.py").write_bytes(textwrap.dedent('''\
        from dataclasses import dataclass

        from simulation import aides as aides_de_camp


        @dataclass
        class Etat:
            # La demande, en MW.
            demande_mw: float = 0.0


        def remplir(etat: Etat) -> None:
            """T-0999 : la demande."""
            etat.demande_mw = 3.0


        def lire(etat: Etat) -> float:
            return etat.demande_mw if aides_de_camp.PREVISIONNISTE else 0.0
    ''').encode("utf-8"))
    (tmp_path / "tickets" / "T-0999-essai.md").write_bytes(
        b"---\nid: T-0999\ntitle: Un essai\n---\n\n`lire` lit la demande.\n")
    read = python.Reader(sorted((tmp_path / "simulation").glob("*.py")), root=tmp_path)
    g = nx.DiGraph()
    for n in read.nodes:
        g.add_node(n["id"], **n)
    for e in read.links:
        g.add_edge(e["source"], e["target"], relations={e["relation"]}, confidence=e["confidence"],
                   locations=[e["source_file"]], contexts=[])
    _enrich(g, tmp_path)
    f, field = "simulation_jeu_", "simulation_jeu_etat_demande_mw"
    assert g.nodes[field]["kind"] == "field" and g.nodes[field]["notes"] == "La demande, en MW."
    assert g.nodes[f"{f}etat"]["end"] == 9
    assert "writes" in g[f"{f}remplir"][field]["relations"]
    assert "reads" in g[f"{f}lire"][field]["relations"]
    constant = "simulation_aides_previsionniste"
    assert g[f"{f}lire"][constant]["confidence"] == "EXTRACTED"
    assert "cites" in g[f"{f}remplir"]["ticket_t_0999"]["relations"]
    assert g.nodes["ticket_t_0999"]["notes"] == "Un essai"
    assert "names" in g["ticket_t_0999"][f"{f}lire"]["relations"]


def test_an_import_alias_finds_its_module_by_its_import_name(tmp_path: Path):
    """T-0096: `from pkg import reglages as r`, then `r.SEUIL`, in a src/ layout: the core reads the constant."""
    import networkx as nx

    sources = {"src/pkg/__init__.py": "", "src/pkg/reglages.py": "SEUIL = 1\n",
               "src/pkg/jeu.py": "from pkg import reglages as r  # a comment\n\n\ndef lire():\n    return r.SEUIL\n",
               "autre/reglages.py": "SEUIL = 2\n"}  # the same constant elsewhere: only the alias tells which
    for rel, text in sources.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    read = python.Reader([tmp_path / rel for rel in sources], root=tmp_path)
    g = nx.DiGraph()
    for n in read.nodes:
        g.add_node(n["id"], **n)
    _enrich(g, tmp_path)
    assert g["src_pkg_jeu_lire"]["src_pkg_reglages_seuil"]["confidence"] == "EXTRACTED"
    assert "autre_reglages_seuil" not in g["src_pkg_jeu_lire"]


def test_a_name_defined_once_is_read_from_another_file_after_a_chain(tmp_path: Path):
    """`x.NAME`, NAME a module variable defined once in the host, reads it (INFERRED), after `a.b.` too; T-0091 tries
    `elsewhere` only on the lines where a word after `x.` is such a name."""
    import networkx as nx

    (tmp_path / "simulation").mkdir()
    (tmp_path / "simulation" / "reglages.py").write_bytes(b"SEUIL_GLOBAL = 1\n")
    (tmp_path / "simulation" / "jeu.py").write_bytes(textwrap.dedent('''\
        def proche(x):
            return x.SEUIL_GLOBAL


        def loin(a):
            return a.b.SEUIL_GLOBAL


        def ailleurs(a):
            return a.SEUIL_LOCAL
    ''').encode("utf-8"))
    read = python.Reader(sorted((tmp_path / "simulation").glob("*.py")), root=tmp_path)
    g = nx.DiGraph()
    for n in read.nodes:
        g.add_node(n["id"], **n)
    _enrich(g, tmp_path)
    seuil = "simulation_reglages_seuil_global"
    assert {s for s in g.predecessors(seuil) if "reads" in g[s][seuil]["relations"]} \
        == {"simulation_jeu_proche", "simulation_jeu_loin"}
    assert g["simulation_jeu_loin"][seuil]["confidence"] == "INFERRED"


@grid_zero
def test_godot_resolves_its_preloads():
    """On the real repository: `Charte.ACCENT` read through the preload,
    `Progress.record` found through it, a send from the client leads to its action."""
    g, *_ = cli.assemble()
    accent = next(n for n, d in g.nodes(data=True) if d["source_file"] == "godot/menu/charte.gd" and d["name"] == "ACCENT")
    assert sum("reads" in g[s][accent]["relations"] and g[s][accent]["confidence"] == "EXTRACTED"
               for s in g.predecessors(accent)) >= 10
    assert [g.nodes[n]["source_file"] for n in cli.find(g, "Progress.record")] == ["godot/settings/progress.gd"]
    assert any("sends" in g[s]["web_api_scenarios_php_action_defi_envoyer"]["relations"]
               for s in g.predecessors("web_api_scenarios_php_action_defi_envoyer"))
    # The keys of the state: the client reads `demand_rising_beyond` by its key.
    field = "simulation_game_etat_de_jeu_etatdejeu_demand_rising_beyond"
    assert "godot/map/lectures.gd" in {g.nodes[s]["source_file"] for s in g.predecessors(field)
                                       if "reads" in g[s][field]["relations"]}
    # The field of a base (EngineState) is read by its key too.
    tick = next(n for n, d in g.nodes(data=True) if d["kind"] == "field" and d["name"] == "EngineState.tick")
    assert any(g.nodes[s]["source_file"].endswith(".gd") for s in g.predecessors(tick))


@grid_zero
def test_the_graph_does_not_change_from_one_build_to_the_next():
    g1, *_ = cli.assemble()
    g2, *_ = cli.assemble()
    assert sorted(g1.edges) == sorted(g2.edges)
    assert cli.communities(g1) == cli.communities(g2)


def test_a_leaf_stays_in_its_neighbours_community():
    """T-0090: the nodes of one neighbour are folded into it before Louvain; a chain hanging off a triangle, a pair
    apart, each with its neighbour; a ticket still in its own community."""
    import networkx as nx
    g = nx.DiGraph()
    for n in ("a", "b", "c", "d", "e", "x", "y", "p", "q", "r", "t"):
        g.add_node(n, kind="ticket" if n == "t" else "function", source_file=f"{n}.py")
    for s, t in ("ab", "bc", "ca", "cd", "de", "xy", "pq", "qr", "rp", "ap", "et"):
        g.add_edge(s, t, locations=[f"{s}.py:1"])
    community_of, names = cli.communities(g)
    assert community_of["c"] == community_of["d"] == community_of["e"]
    assert community_of["x"] == community_of["y"] != community_of["a"]
    assert names[community_of["t"]] == "tickets"
    assert cli.communities(g) == (community_of, names)


def test_undirected_the_path_prefers_the_code(capsys):
    """T-0354: a value links everything that writes it; undirected, the
    path goes through it only for want of a path through the code."""
    import networkx as nx
    g = nx.DiGraph()
    for n, kind in (("a", "function"), ("b", "function"), ("c", "function"), ("d", "function"),
                    ("value_x", "value")):
        g.add_node(n, id=n, label=n, name=n, kind=kind, source_file="f.py", source_location="L1")
    for s, t, rel in (("a", "b", "calls"), ("b", "c", "calls"), ("c", "d", "calls"),
                      ("a", "value_x", "value"), ("d", "value_x", "value")):
        g.add_edge(s, t, relations={rel}, confidence="EXTRACTED", locations=["f.py:1"], contexts=[])
    assert cli.path(g, "a", "d", undirected=True) == 0
    assert "value_x" not in capsys.readouterr().out
    g.remove_edge("b", "c")
    assert cli.path(g, "a", "d", undirected=True) == 0
    assert "value_x" in capsys.readouterr().out


# T-0014: the JS reader, on a small sample project.
JS = {
    "src/zones.mjs": "export function zoneFromCode(code) {\n  return code\n}\n",
    "src/compute.mjs": textwrap.dedent("""\
        import { zoneFromCode as zone } from './zones.mjs'
        import Builder from './builder.mjs'

        export function compute(dpe) {
          const b = new Builder()
          b.build(zone(dpe.code))
          return total(b)
        }

        const total = (b) => b.sum
        """),
    "src/builder.mjs": textwrap.dedent("""\
        export default class Builder {
          build(zone) {
            return this.check(zone)
          }

          check(zone) {
            return zone
          }
        }
        """),
}


def _js(tmp_path: Path, files: dict[str, str]):
    from graphe import js
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    return js.Reader([tmp_path / rel for rel in sorted(files)], root=tmp_path)


def test_the_js_reader_follows_named_and_default_imports_and_method_calls(tmp_path: Path):
    read = _js(tmp_path, JS)
    links = {(e["source"], e["target"], e["relation"], e["confidence"]) for e in read.links}
    names = {n["id"]: n["name"] for n in read.nodes}
    assert names["src_builder_mjs_builder_build"] == "Builder.build"
    assert ("src_compute_mjs", "src_zones_mjs", "imports", "EXTRACTED") in links
    assert ("src_compute_mjs_compute", "src_zones_mjs_zonefromcode", "calls", "EXTRACTED") in links  # named, aliased
    assert ("src_compute_mjs_compute", "src_builder_mjs_builder", "calls", "EXTRACTED") in links  # new on a default import
    assert ("src_compute_mjs_compute", "src_compute_mjs_total", "calls", "EXTRACTED") in links  # a local arrow function
    assert ("src_builder_mjs_builder_build", "src_builder_mjs_builder_check", "calls", "EXTRACTED") in links  # this.check()
    # b.build(): b = new Builder(), its type known (T-0020)
    assert ("src_compute_mjs_compute", "src_builder_mjs_builder_build", "calls", "EXTRACTED") in links


def test_the_js_reader_follows_re_exports_and_classifies_its_calls(tmp_path: Path):
    read = _js(tmp_path, {
        **JS,
        "src/index.mjs": "export { zoneFromCode } from './zones.mjs'\nexport * from './compute.mjs'\n",
        "app.js": textwrap.dedent("""\
            import * as engine from './src/index.mjs'
            import { zoneFromCode } from './src/index.mjs'
            import { calcul_3cl } from '@open3cl/engine'

            function main() {
              engine.compute({})
              zoneFromCode(1)
              calcul_3cl({})
              Math.max(1, 2)
              const xs = [1].map(String)
            }
            """),
    })
    links = {(e["source"], e["target"], e["confidence"]) for e in read.links if e["relation"] == "calls"}
    assert ("app_js_main", "src_compute_mjs_compute", "EXTRACTED") in links  # export * from, then a namespace
    assert ("app_js_main", "src_zones_mjs_zonefromcode", "EXTRACTED") in links  # export { } from
    verdicts = {s["text"]: s["verdict"] for s in read.sites if s["file"] == "app.js"}
    assert verdicts == {"engine.compute": "ours", "zoneFromCode": "ours", "calcul_3cl": "external",
                        "Math.max": "global", "[1].map": "member"}


def test_the_js_reader_skips_a_comment_among_the_imported_names(tmp_path: Path):
    """libsignal's `node/ts/NativeNice.ts` (T-0032): a comment is a named child of `{ }`, not a specifier."""
    read = _js(tmp_path, {
        "src/zones.mjs": "export function zoneFromCode() {}\n",
        "app.mjs": textwrap.dedent("""\
            import {
              /* eslint-disable no-unused-vars */
              zoneFromCode,
            } from './src/zones.mjs'
            export { /* again */ zoneFromCode as z }

            function main() { zoneFromCode() }
            """),
    })
    assert ("app_mjs_main", "src_zones_mjs_zonefromcode", "calls", "EXTRACTED") in \
        {(e["source"], e["target"], e["relation"], e["confidence"]) for e in read.links}


def test_the_js_reader_keeps_ids_apart_and_links_only_what_it_knows(tmp_path: Path):
    read = _js(tmp_path, {
        "lib.mjs": textwrap.dedent("""\
            export function f() {}
            export function g() {}
            export const util = { f: () => 1 }
            """),
        "index.mjs": "export * as lib from './lib.mjs'\n",
        "shapes.js": textwrap.dedent("""\
            export class Base {
              area() { return 0 }
            }

            export class Box extends Base {
              get size() { return 1 }
              set size(v) {}
              static make() { return new Box() }
              make() { return this.area() }
              #h() {}
              h() { this.#h() }
            }

            function Foo() {}
            function foo() {}
            """),
        "shapes.mjs": "export function area() {}\n",
        "use.mjs": textwrap.dedent("""\
            import { f, util } from './lib.mjs'
            import { lib } from './index.mjs'

            export function run(f) {
              f()
              util.g()
              lib.g()
              const g = () => 1
              g()
            }
            """),
    })
    ids = [n["id"] for n in read.nodes]
    assert len(ids) == len(set(ids)), sorted(i for i in ids if ids.count(i) > 1)
    assert {"lib_mjs", "shapes_js", "shapes_mjs"} <= set(ids)  # the extension too: x.py is the Python reader's
    calls = {(e["source"], e["target"]): e["confidence"] for e in read.links if e["relation"] == "calls"}
    run = "use_mjs_run"
    assert ("use_mjs_run", "lib_mjs_f") not in calls  # f is the parameter, not the import
    assert ("use_mjs_run", "lib_mjs_g") in calls  # lib.g(): export * as lib, then a named import
    assert calls[(run, "lib_mjs_g")] == "EXTRACTED"
    sure = {t for (s, t), c in calls.items() if s == run and c == "EXTRACTED"}
    assert sure == {"lib_mjs_g"}, sure  # util.g(): util is an object, not the module; g() is the local arrow
    make = next(n["id"] for n in read.nodes if n["name"] == "Box.make" and n["source_location"] == "L9")
    assert calls[(make, "shapes_js_base_area")] == "EXTRACTED"  # this.area(), inherited


TS = {
    "src/lib/eau.ts": textwrap.dedent("""\
        import { Base } from './base'
        export type Etat = 'sec' | 'confort'

        export function reserve(pluie: number, { ru }: { ru: number } = { ru: 50 }): Etat {
          return pluie > ru ? 'confort' : 'sec'
        }

        export class Bilan extends Base implements Etat {
          jour(p?: number): Etat {
            return this.mesure(p!)
          }
        }
        """),
    "src/lib/base.ts": "export abstract class Base {\n  mesure(p: number): Etat {\n    return reserve(p)\n  }\n}\n",
    "src/Tuile.svelte": textwrap.dedent("""\
        <script lang="ts">
          import { reserve, type Etat } from './lib/eau'
          let { pluie }: { pluie: number } = $props()
          let etat = $derived(reserve(pluie))

          function rafraichir(reserve: (p: number) => Etat): Etat {
            return reserve(1)
          }

          function calcul(p: number): Etat {
            return reserve(p)
          }
        </script>

        <p onclick={() => rafraichir(1)}>{etat}</p>
        """),
}


def test_the_js_reader_reads_typescript_and_the_script_of_a_svelte_component(tmp_path: Path):
    """T-0015: a Svelte component's function calls a TS function through an import."""
    read = _js(tmp_path, TS)
    links = {(e["source"], e["target"], e["relation"], e["confidence"]) for e in read.links}
    lines = {n["id"]: n["source_location"] for n in read.nodes}
    assert ("src_tuile_svelte", "src_lib_eau_ts", "imports", "EXTRACTED") in links  # './lib/eau': the .ts
    assert ("src_tuile_svelte_calcul", "src_lib_eau_ts_reserve", "calls", "EXTRACTED") in links
    assert ("src_tuile_svelte", "src_lib_eau_ts_reserve", "calls", "EXTRACTED") in links  # $derived(...) at the top
    assert ("src_lib_eau_ts_bilan_jour", "src_lib_base_ts_base_mesure", "calls", "EXTRACTED") in links  # this, inherited
    assert lines["src_tuile_svelte_calcul"] == "L10"  # the markup does not move the lines
    calls = {(e["source"], e["target"]) for e in read.links if e["relation"] == "calls"}
    assert ("src_tuile_svelte_rafraichir", "src_lib_eau_ts_reserve") not in calls  # its parameter hides the import
    verdicts = {(s["file"], s["text"]): s["verdict"] for s in read.sites}
    assert verdicts[("src/Tuile.svelte", "$props")] == "global"  # a rune: Svelte's
    assert verdicts[("src/Tuile.svelte", "$derived")] == "global"


VUE = {
    "src/lib/eau.ts": "export function reserve(p: number): number {\n  return p\n}\n",
    "src/Carte.vue": textwrap.dedent("""\
        <template>
          <div :class="ton(niveau)" @click.prevent="garder">
            {{ reserve(niveau) }}
            <p v-if="pret()">{{ a + }}{{ a // b }}{{ garder() }}</p>
            <li v-for="(x, i) in liste()" :key="i">{{ etiquette(x) }}</li>
          </div>
        </template>

        <script setup lang="ts">
        import { reserve } from './lib/eau'
        const props = defineProps<{ niveau: number }>()
        function ton(n: number): string { return reserve(n) > 1 ? 'haut' : 'bas' }
        function garder() {}
        function pret() { return true }
        function liste(): number[] { return [] }
        function etiquette(x: number) { return `${x}` }
        </script>
        """),
}


def test_the_js_reader_reads_the_script_and_template_of_a_vue_component(tmp_path: Path):
    """T-0082: a `<script setup lang="ts">` read as TypeScript; the template's calls the component's, a broken
    expression costing only itself."""
    read = _js(tmp_path, VUE)
    links = {(e["source"], e["target"], e["relation"], e["confidence"]) for e in read.links}
    vue = "src_carte_vue"
    assert (vue, "src_lib_eau_ts", "imports", "EXTRACTED") in links
    assert (f"{vue}_ton", "src_lib_eau_ts_reserve", "calls", "EXTRACTED") in links  # typed: the TS grammar
    for called in ("src_lib_eau_ts_reserve", f"{vue}_ton", f"{vue}_pret", f"{vue}_liste", f"{vue}_etiquette"):
        assert (vue, called, "calls", "EXTRACTED") in links, called  # after `{{ a + }}` too
    assert (vue, f"{vue}_garder", "calls", "EXTRACTED") in links  # `{{ a // b }}` swallows no neighbour
    assert (vue, f"{vue}_garder", "references", "EXTRACTED") in links  # @click="garder"
    lines = {n["id"]: n["source_location"] for n in read.nodes}
    assert lines[f"{vue}_ton"] == "L12"
    verdicts = {(s["file"], s["text"]): s["verdict"] for s in read.sites}
    assert verdicts[("src/Carte.vue", "defineProps")] == "global"  # a compiler macro: Vue's
