"""Le graphe du code : ce que ses lecteurs relient.

Les lecteurs se jouent sur un petit depot ecrit ici ; les tests marques
`grid_zero` sur le vrai Grid Zero (conftest.py). Sa couverture et son test de
reference restent dans Grid Zero (T-0003).
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest

import graphe
import graphe_python
from conftest import grid_zero

MOTEUR = '''
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

FLOTTE = '''
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

SERVEUR = '''
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
def lecture(tmp_path: Path) -> graphe_python.Lecture:
    (tmp_path / "simulation").mkdir()
    chemins = []
    for nom, texte in (("moteur", MOTEUR), ("flotte", FLOTTE), ("server", SERVEUR)):
        chemin = tmp_path / "simulation" / f"{nom}.py"
        chemin.write_bytes(textwrap.dedent(texte).encode("utf-8"))
        chemins.append(chemin)
    return graphe_python.Lecture(chemins, racine=tmp_path)


def _liens(lecture, relation: str = "calls") -> set[tuple[str, str]]:
    return {(e["source"], e["target"]) for e in lecture.liens if e["relation"] == relation
            and e["confidence"] == "EXTRACTED"}


M, F, S = "simulation_moteur_", "simulation_flotte_", "simulation_server_"


def test_un_appel_suit_le_type_des_attributs(lecture):
    appels = _liens(lecture)
    # self.flotte = Flotte() dans __init__ ; un champ de dataclass annote
    assert (f"{M}moteur_charge", f"{F}flotte_mesurer") in appels
    assert (f"{M}reglage_appliquer", f"{F}flotte_pousser") in appels
    # l'element d'une liste annotee, le retour deduit d'une methode
    assert (f"{M}moteur_pas", f"{M}reglage_appliquer") in appels
    assert (f"{M}moteur_pas", f"{F}flotte_pousser") in appels


def test_proprietes_imbriquees_imports_locaux_et_rappels(lecture):
    appels = _liens(lecture)
    assert (f"{M}moteur_pas", f"{M}moteur_charge") in appels  # lire une propriete l'appelle
    assert (f"{M}moteur_pas", f"{M}moteur_pas_interne") in appels
    assert (f"{M}moteur_pas_interne", f"{F}flotte_mesurer") in appels
    assert (f"{M}moteur_pas", f"{F}vider") in appels  # importe dans la fonction
    assert (f"{M}moteur_pas", f"{M}cle") in _liens(lecture, "references")


def test_un_objet_hors_du_depot_ne_prend_pas_nos_noms(lecture):
    """m.start() sur un re.Match : un nom que porte Flotte.start, sur un
    recepteur qui vient d'ailleurs - aucun lien, meme par le nom."""
    vers_start = [e for e in lecture.liens if e["target"] == f"{F}flotte_start" and e["relation"] != "method"]
    assert vers_start == []
    site = next(s for s in lecture.sites if s["expr"] == "m.start")
    assert site["verdict"] == "externe"


def test_trouver_un_noeud_par_son_nom(lecture):
    import networkx as nx
    g = nx.DiGraph()
    for n in lecture.noeuds:
        g.add_node(n["id"], **n)
    assert graphe.trouver(g, "Moteur.pas") == [f"{M}moteur_pas"]
    assert graphe.trouver(g, "moteur.py::pas") == [f"{M}moteur_pas"]
    assert set(graphe.trouver(g, "pousser")) == {f"{F}flotte_pousser"}
    assert graphe.trouver(g, "inexistant") == []


PHP = """<?php
// Le point d'entree.
function gz_lire($x) {
    return gz_valider($x);
}

function gz_valider($x) {
    return $x;
}

switch ($action) {
    case 'liste':
    case 'relister':
        gz_lire(1);
        break;
}
"""


def test_le_lecteur_php_lit_fonctions_actions_et_appels(tmp_path: Path):
    import graphe_php
    (tmp_path / "web").mkdir()
    chemin = tmp_path / "web" / "api.php"
    chemin.write_bytes(PHP.encode("utf-8"))
    lu = graphe_php.Lecture([chemin], racine=tmp_path)
    liens = {(e["source"], e["target"], e["relation"]) for e in lu.liens}
    f = "web_api"
    assert (f"{f}_gz_lire", f"{f}_gz_valider", "calls") in liens
    # deux case a la suite : le premier mene au second, qui porte le corps
    assert (graphe_php.id_d_action(f, "liste"), graphe_php.id_d_action(f, "relister"), "dispatches") in liens
    assert (graphe_php.id_d_action(f, "relister"), f"{f}_gz_lire", "calls") in liens
    assert (graphe_php.id_d_action(f, "liste"), f"{f}_gz_lire", "calls") not in liens


def test_etendue_et_notes_d_un_corps():
    import graphe_enrichir as ge
    lignes = textwrap.dedent('''\
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
    assert ge.etendue(lignes, 4) == 9
    assert ge.notes(lignes, 4) == "Le pas du moteur, en deux lignes."
    assert ge.etendue(PHP.splitlines(), 3) == 5  # l'accolade fermante est du bloc


def _enrichir(g, racine: Path) -> None:
    """Le coeur, sur des sources ecrites dans `racine` : un depot git, d'ou il tire les documents (T-0010)."""
    import graphe_enrichir
    subprocess.run(["git", "init", "-q", str(racine)], check=True)
    graphe_enrichir.enrichir(g, racine)


def test_enrichir_relie_les_variables_et_trouve_par_le_texte(tmp_path: Path):
    import networkx as nx

    (tmp_path / "simulation").mkdir()
    chemin = tmp_path / "simulation" / "jeu.py"
    chemin.write_bytes(textwrap.dedent('''\
        LIMITE = 3
        compte = 0


        # La clarte du jour.
        def avancer():
            global compte
            compte += LIMITE
            return tr("Réseau stable")
    ''').encode("utf-8"))
    # T-0009 : le motif de l'appel qui affiche un texte vient de l'hote.
    (tmp_path / "graphe.toml").write_text("texte_affiche = '\\btr\\(\"([^\"]*)\"'\n", encoding="utf-8")
    lu = graphe_python.Lecture([chemin], racine=tmp_path)
    g = nx.DiGraph()
    for n in lu.noeuds:
        g.add_node(n["id"], **n)
    _enrichir(g, tmp_path)
    f = "simulation_jeu_"
    assert "lit" in g[f"{f}avancer"][f"{f}limite"]["relations"]
    assert "ecrit" in g[f"{f}avancer"][f"{f}compte"]["relations"]
    assert g.nodes[f"{f}avancer"]["textes"] == ["Réseau stable"]
    assert [n for n, _ in graphe.recherche(g, "réseau stable")] == [f"{f}avancer"]
    assert [n for n, _ in graphe.recherche(g, "clarte")] == [f"{f}avancer"]
    assert [n for n, _ in graphe.recherche(g, "def avancer")] == [f"{f}avancer"]


def test_une_valeur_ecrite_des_deux_cotes(tmp_path: Path):
    """T-0354 : une valeur ecrite en Python et en GDScript devient un noeud, dans sa communaute."""
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
    lu = graphe_python.Lecture(sorted((tmp_path / "serveur").rglob("*.py")), racine=tmp_path)
    g = nx.DiGraph()
    for n in lu.noeuds:
        g.add_node(n["id"], **n)
    g.add_node("godot_lecture_texte", id="godot_lecture_texte", label="texte()", sorte="fonction",
               source_file="godot/lecture.gd", source_location="L1", nom="texte")
    _enrichir(g, tmp_path)
    assert {s for s, _ in g.in_edges("valeur_coupee")} == {"serveur_etat_construire", "godot_lecture_texte"}
    assert "valeur_voisin" not in g  # ecrite d'un seul cote
    assert [n for n, _ in graphe.recherche(g, "coupee")] == ["valeur_coupee"]
    de, noms = graphe.communautes(g)
    assert noms[de["valeur_coupee"]] == "valeurs"


def test_champs_alias_d_import_et_tickets(tmp_path: Path):
    """graphe_manques.md : les champs d'une classe, l'alias d'import Python,
    le ticket cite par le code et celui qui nomme une fonction."""
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
    lu = graphe_python.Lecture(sorted((tmp_path / "simulation").glob("*.py")), racine=tmp_path)
    g = nx.DiGraph()
    for n in lu.noeuds:
        g.add_node(n["id"], **n)
    for e in lu.liens:
        g.add_edge(e["source"], e["target"], relations={e["relation"]}, confiance=e["confidence"],
                   lieux=[e["source_file"]], contextes=[])
    _enrichir(g, tmp_path)
    f, champ = "simulation_jeu_", "simulation_jeu_etat_demande_mw"
    assert g.nodes[champ]["sorte"] == "champ" and g.nodes[champ]["notes"] == "La demande, en MW."
    assert g.nodes[f"{f}etat"]["fin"] == 9
    assert "ecrit" in g[f"{f}remplir"][champ]["relations"]
    assert "lit" in g[f"{f}lire"][champ]["relations"]
    constante = "simulation_aides_previsionniste"
    assert g[f"{f}lire"][constante]["confiance"] == "EXTRACTED"
    assert "cite" in g[f"{f}remplir"]["ticket_t_0999"]["relations"]
    assert g.nodes["ticket_t_0999"]["notes"] == "Un essai"
    assert "nomme" in g["ticket_t_0999"][f"{f}lire"]["relations"]


@grid_zero
def test_le_godot_resout_ses_prechargements():
    """Sur le vrai depot : `Charte.ACCENT` lu par le prechargement,
    `Progress.record` trouve par lui, un envoi du client mene a son action."""
    g, *_ = graphe.assembler()
    accent = next(n for n, d in g.nodes(data=True) if d["source_file"] == "godot/menu/charte.gd" and d["nom"] == "ACCENT")
    assert sum("lit" in g[s][accent]["relations"] and g[s][accent]["confiance"] == "EXTRACTED"
               for s in g.predecessors(accent)) >= 10
    assert [g.nodes[n]["source_file"] for n in graphe.trouver(g, "Progress.record")] == ["godot/settings/progress.gd"]
    assert any("sends" in g[s]["web_api_scenarios_action_defi_envoyer"]["relations"]
               for s in g.predecessors("web_api_scenarios_action_defi_envoyer"))
    # Les cles de l'etat : le client lit `demand_rising_beyond` par sa cle.
    champ = "simulation_game_etat_de_jeu_etatdejeu_demand_rising_beyond"
    assert "godot/map/lectures.gd" in {g.nodes[s]["source_file"] for s in g.predecessors(champ)
                                       if "lit" in g[s][champ]["relations"]}
    # Le champ d'une base (EngineState) se lit aussi par sa cle.
    tick = next(n for n, d in g.nodes(data=True) if d["sorte"] == "champ" and d["nom"] == "EngineState.tick")
    assert any(g.nodes[s]["source_file"].endswith(".gd") for s in g.predecessors(tick))


@grid_zero
def test_le_graphe_ne_change_pas_d_une_construction_a_l_autre():
    g1, *_ = graphe.assembler()
    g2, *_ = graphe.assembler()
    assert sorted(g1.edges) == sorted(g2.edges)
    assert graphe.communautes(g1) == graphe.communautes(g2)


def test_sans_le_sens_le_chemin_prefere_le_code(capsys):
    """T-0354 : une valeur relie tout ce qui l'ecrit ; sans le sens, le
    chemin ne passe par elle que faute de chemin par le code."""
    import networkx as nx
    g = nx.DiGraph()
    for n, sorte in (("a", "fonction"), ("b", "fonction"), ("c", "fonction"), ("d", "fonction"),
                     ("valeur_x", "valeur")):
        g.add_node(n, id=n, label=n, nom=n, sorte=sorte, source_file="f.py", source_location="L1")
    for s, c, rel in (("a", "b", "calls"), ("b", "c", "calls"), ("c", "d", "calls"),
                      ("a", "valeur_x", "valeur"), ("d", "valeur_x", "valeur")):
        g.add_edge(s, c, relations={rel}, confiance="EXTRACTED", lieux=["f.py:1"], contextes=[])
    assert graphe.chemin(g, "a", "d", sans_sens=True) == 0
    assert "valeur_x" not in capsys.readouterr().out
    g.remove_edge("b", "c")
    assert graphe.chemin(g, "a", "d", sans_sens=True) == 0
    assert "valeur_x" in capsys.readouterr().out
