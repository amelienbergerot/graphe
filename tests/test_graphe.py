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

import graphe
import graphe_python
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
def reader(tmp_path: Path) -> graphe_python.Reader:
    (tmp_path / "simulation").mkdir()
    paths = []
    for name, text in (("moteur", ENGINE_PY), ("flotte", FLEET_PY), ("server", SERVER_PY)):
        path = tmp_path / "simulation" / f"{name}.py"
        path.write_bytes(textwrap.dedent(text).encode("utf-8"))
        paths.append(path)
    return graphe_python.Reader(paths, root=tmp_path)


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
    graphe_python.Reader([path], root=tmp_path)


def test_the_cache_gives_the_same_reading_and_reads_an_edited_file_again(reader, tmp_path: Path):
    """T-0026: each file's parse and definitions come from the cache; the resolution is redone in full."""
    paths = sorted((tmp_path / "simulation").glob("*.py"))
    def read(cache):
        r = graphe_python.Reader(paths, root=tmp_path, cache=cache)
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
    assert graphe.find(g, "Moteur.pas") == [f"{M}moteur_pas"]
    assert graphe.find(g, "moteur.py::pas") == [f"{M}moteur_pas"]
    assert set(graphe.find(g, "pousser")) == {f"{F}flotte_pousser"}
    assert graphe.find(g, "inexistant") == []


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


def test_the_php_reader_reads_functions_actions_and_calls(tmp_path: Path):
    import graphe_php
    (tmp_path / "web").mkdir()
    path = tmp_path / "web" / "api.php"
    path.write_bytes(PHP.encode("utf-8"))
    read = graphe_php.Reader([path], root=tmp_path)
    links = {(e["source"], e["target"], e["relation"]) for e in read.links}
    f = "web_api"
    assert (f"{f}_gz_lire", f"{f}_gz_valider", "calls") in links
    assert (f"{f}_gz_noter", f"{f}_gz_valider", "calls") in links  # T-0015: the brace on its own line (4cast)
    # two cases in a row: the first leads to the second, which bears the body
    assert (graphe_php.action_id(f, "liste"), graphe_php.action_id(f, "relister"), "dispatches") in links
    assert (graphe_php.action_id(f, "relister"), f"{f}_gz_lire", "calls") in links
    assert (graphe_php.action_id(f, "liste"), f"{f}_gz_lire", "calls") not in links


def test_extent_and_notes_of_a_body():
    import graphe_core as gc
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


def _enrich(g, root: Path) -> None:
    """The core, on sources written in `root`: a git repository, from which it draws the documents (T-0010)."""
    import graphe_core
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    graphe_core.enrich(g, root)


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
    read = graphe_python.Reader([path], root=tmp_path)
    g = nx.DiGraph()
    for n in read.nodes:
        g.add_node(n["id"], **n)
    _enrich(g, tmp_path)
    f = "simulation_jeu_"
    assert "reads" in g[f"{f}avancer"][f"{f}limite"]["relations"]
    assert "writes" in g[f"{f}avancer"][f"{f}compte"]["relations"]
    assert g.nodes[f"{f}avancer"]["texts"] == ["Réseau stable"]
    assert [n for n, _ in graphe.search_nodes(g, "réseau stable")] == [f"{f}avancer"]
    assert [n for n, _ in graphe.search_nodes(g, "clarte")] == [f"{f}avancer"]
    assert [n for n, _ in graphe.search_nodes(g, "def avancer")] == [f"{f}avancer"]


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
    read = graphe_python.Reader(sorted((tmp_path / "serveur").rglob("*.py")), root=tmp_path)
    g = nx.DiGraph()
    for n in read.nodes:
        g.add_node(n["id"], **n)
    g.add_node("godot_lecture_texte", id="godot_lecture_texte", label="texte()", kind="function",
               source_file="godot/lecture.gd", source_location="L1", name="texte")
    _enrich(g, tmp_path)
    assert {s for s, _ in g.in_edges("value_coupee")} == {"serveur_etat_construire", "godot_lecture_texte"}
    assert "value_voisin" not in g  # written on one side only
    assert [n for n, _ in graphe.search_nodes(g, "coupee")] == ["value_coupee"]
    community_of, names = graphe.communities(g)
    assert names[community_of["value_coupee"]] == "values"


def test_fields_import_aliases_and_tickets(tmp_path: Path):
    """BACKLOG.md: the fields of a class, the Python import alias, the
    ticket cited by the code and the one that names a function."""
    import networkx as nx

    (tmp_path / "simulation").mkdir()
    (tmp_path / "tickets").mkdir()
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
    read = graphe_python.Reader(sorted((tmp_path / "simulation").glob("*.py")), root=tmp_path)
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


@grid_zero
def test_godot_resolves_its_preloads():
    """On the real repository: `Charte.ACCENT` read through the preload,
    `Progress.record` found through it, a send from the client leads to its action."""
    g, *_ = graphe.assemble()
    accent = next(n for n, d in g.nodes(data=True) if d["source_file"] == "godot/menu/charte.gd" and d["name"] == "ACCENT")
    assert sum("reads" in g[s][accent]["relations"] and g[s][accent]["confidence"] == "EXTRACTED"
               for s in g.predecessors(accent)) >= 10
    assert [g.nodes[n]["source_file"] for n in graphe.find(g, "Progress.record")] == ["godot/settings/progress.gd"]
    assert any("sends" in g[s]["web_api_scenarios_action_defi_envoyer"]["relations"]
               for s in g.predecessors("web_api_scenarios_action_defi_envoyer"))
    # The keys of the state: the client reads `demand_rising_beyond` by its key.
    field = "simulation_game_etat_de_jeu_etatdejeu_demand_rising_beyond"
    assert "godot/map/lectures.gd" in {g.nodes[s]["source_file"] for s in g.predecessors(field)
                                       if "reads" in g[s][field]["relations"]}
    # The field of a base (EngineState) is read by its key too.
    tick = next(n for n, d in g.nodes(data=True) if d["kind"] == "field" and d["name"] == "EngineState.tick")
    assert any(g.nodes[s]["source_file"].endswith(".gd") for s in g.predecessors(tick))


@grid_zero
def test_the_graph_does_not_change_from_one_build_to_the_next():
    g1, *_ = graphe.assemble()
    g2, *_ = graphe.assemble()
    assert sorted(g1.edges) == sorted(g2.edges)
    assert graphe.communities(g1) == graphe.communities(g2)


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
    assert graphe.path(g, "a", "d", undirected=True) == 0
    assert "value_x" not in capsys.readouterr().out
    g.remove_edge("b", "c")
    assert graphe.path(g, "a", "d", undirected=True) == 0
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
    import graphe_js
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    return graphe_js.Reader([tmp_path / rel for rel in sorted(files)], root=tmp_path)


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
