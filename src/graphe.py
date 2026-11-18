"""graphe: the code graph of a host project - what calls what, what cites what.

    graphe build [--quiet]           graphe/: graphe.json, REPORT.md, graphe.html
    graphe check                     the coverage of each contribution
    graphe path A B [--undirected]   the shortest path from A to B
    graphe explain X [--all] [--source]   what X calls, what calls X (and its code)
    graphe callers X [--depth N]
    graphe search PATTERN            by name, then by displayed texts and comments
    graphe install [--remove]        the git hooks that rebuild it

A node is designated by its id, its name (`help`, `Class.method`),
`file::name` (`tools.py::help`) or, in GDScript, by the constant that
preloads its script (`Script.function`).

The readers: graphe_python.py (the ast, calls resolved by types),
graphe_godot.py (GDScript, by patterns) and graphe_php.py (its functions and
the actions of a `switch ($action)`). The core, graphe_enrichir.py, then
reads the text: the end of each function and class, the texts it displays
(the `displayed_text` pattern of graphe.toml), its comment, module variables
and who reads them, and the documents (the host's Markdown, `[documents]` of
graphe.toml) - who cites them, what they name. The fields of a class are
nodes (the Python reader).

Communities (`[communities]` of graphe.toml): `separate` gives kinds outside
the code their own community (kind -> name), after tickets, values and
documents; `strip_prefixes` removes prefixes from community names.

The contract (docs/contribution.md): readers and local extensions return a
contribution through `contribute(project)`. Assembly runs the readers, then
the core (graphe_enrichir), then the extensions declared by `[[extensions]]`
in graphe.toml, in their order. A `with_readers` extension comes in with the
readers, before the core, and may take over their links.

Files read (graphe_racine.py): those git tracks, plus untracked files that
are not ignored, each to the reader of its extension; `exclude`, in an
optional graphe.toml at the host root, removes folders.

Updates: `install` sets git hooks (post-commit, post-merge, post-checkout,
post-rewrite) that rebuild the graph in the background with the global
`graphe` command, and adds the output to the host's .gitignore; a query on a
graph older than the host's code or than the tool rebuilds it first.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from functools import cached_property
from pathlib import Path

import networkx as nx

import graphe_enrichir
import graphe_godot
import graphe_php
import graphe_python
import graphe_racine
from graphe_racine import CONFIGURATION, RACINE, SORTIE

JSON = SORTIE / "graphe.json"
CROCHETS = ("post-commit", "post-merge", "post-checkout", "post-rewrite")
# (debut, fin) du bloc pose dans un crochet ; le second, celui d'avant T-0011 (le relais de l'hote puis l'outil en
# francais), est retire aussi.
BLOCS = (("# >>> graphe code graph", "# <<< graphe code graph"), ("# >>> graphe du code", "# <<< graphe du code"))
# Ce qui fait passer de l'appelant a l'appele.
APPELS = {"calls", "uses", "references", "indirect_call", "sends", "dispatches", "reads", "writes", "value"}
# T-0354 : des noeuds qui ne sont pas du code, chacun leur communaute - un
# ticket, une valeur ou un document relie des fichiers que rien d'autre ne relie, et
# fondrait des communautes sans rapport. L'hote en ajoute (`[communities] separate`).
A_PART = {"ticket": "tickets", "value": "values", "document": "documents"}
POIDS_HORS_CODE = 4


def _communautes() -> tuple[dict[str, str], list[str]]:
    """`[communities]` de graphe.toml : les sortes a part (sorte -> nom), et les prefixes retires des noms."""
    table = graphe_racine.configuration().get("communities", {})
    return {**A_PART, **table.get("separate", {})}, table.get("strip_prefixes", [])


# ---------- construire

def _sources() -> list[Path]:
    """T-0009 : tous les fichiers de l'hote, pas seulement ceux des lecteurs (une extension lit ce qu'elle veut)."""
    return [p for p in graphe_racine.fichiers("") + [RACINE / CONFIGURATION]
            + [RACINE / e.get("path", "") for e in _extensions_declarees()] if p.is_file()]


def _outil() -> list[Path]:
    """Les fichiers de l'outil (T-0006) : un lecteur corrige perime le graphe de chaque hote."""
    return sorted(Path(__file__).parent.glob("graphe*.py"))


def _commit() -> str | None:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RACINE, capture_output=True, text=True,
                           timeout=10)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


# Chaque lecteur sous le nom de sa section de graphe.toml : la cle de sa configuration et de sa couverture.
LECTEURS = {"python": graphe_python.contribute, "godot": graphe_godot.contribute, "php": graphe_php.contribute}
CHAMPS_DU_NOEUD = ("id", "label", "kind", "source_file", "source_location", "name")
CHAMPS_DU_LIEN = ("source", "target", "relation", "confidence", "source_file", "source_location", "context")


class Projet:
    """Ce que recoit `contribute(project)` : la racine, les fichiers de l'hote, la section de configuration de
    celui qui contribue et le graphe deja assemble, copie a la lecture (docs/contribution.md)."""

    def __init__(self, configuration: dict, graphe: nx.DiGraph, verifier: bool) -> None:
        self.root = RACINE
        self.configuration = configuration
        self.checking = verifier
        self._graphe = graphe

    def files(self, suffixe: str) -> list[Path]:
        return graphe_racine.fichiers(suffixe, self.root)

    @cached_property
    def graph(self) -> dict:
        return {"nodes": {n: copy.deepcopy(d) for n, d in self._graphe.nodes(data=True)},
                "links": [{"source": s, "target": c, **copy.deepcopy({**d, "relations": sorted(d["relations"])})}
                          for s, c, d in self._graphe.edges(data=True)]}


def _extensions_declarees() -> list[dict]:
    return graphe_racine.configuration().get("extensions", [])


def _extension(declaration: dict):
    """La fonction `contribute` d'une extension locale ; une extension introuvable arrete la construction."""
    chemin = declaration.get("path", "")
    fichier = RACINE / chemin
    if not chemin or not fichier.is_file():
        raise RuntimeError(f"local extension {chemin!r} not found ([[extensions]] path, {CONFIGURATION})")
    spec = importlib.util.spec_from_file_location(f"graphe_extension_{fichier.stem}", fichier)
    if spec is None:
        raise RuntimeError(f"local extension {chemin}: not a Python module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # une dataclass de l'extension cherche son module ici
    spec.loader.exec_module(module)
    if not callable(getattr(module, "contribute", None)):
        raise RuntimeError(f"local extension {chemin}: no function contribute(project)")
    return module.contribute


def _inserer(graphe: nx.DiGraph, apports: list[tuple[str, dict]], pendants: list[dict]) -> None:
    """Les contributions dans le graphe : les noeuds tries par l'id (un id deja la fusionne ses attributs), puis
    les liens ; un lien par paire de noeuds, qui garde ses relations et ses lieux."""
    noeuds = sorted(((qui, n) for qui, c in apports for n in c.get("nodes", [])), key=lambda p: str(p[1].get("id")))
    for qui, n in noeuds:
        requis = ("id",) if n.get("id") in graphe else CHAMPS_DU_NOEUD
        if manque := [k for k in requis if k not in n]:
            raise RuntimeError(f"{qui}: node {n.get('id')!r} lacks {', '.join(manque)}")
        graphe.add_node(n["id"], **n)
    for qui, c in apports:
        for e in c.get("links", []):
            if manque := [k for k in CHAMPS_DU_LIEN if k not in e]:
                raise RuntimeError(f"{qui}: link {e.get('source')!r} -> {e.get('target')!r} lacks "
                                   f"{', '.join(manque)}")
            s, cible = e["source"], e["target"]
            if s not in graphe or cible not in graphe:
                pendants.append(e)
                continue
            lieu = f"{e['source_file']}:{e['source_location'].lstrip('L')}"
            if graphe.has_edge(s, cible):
                d = graphe[s][cible]
                d["relations"].add(e["relation"])
                if lieu not in d["locations"]:
                    d["locations"].append(lieu)
                if e["confidence"] == "EXTRACTED":
                    d["confidence"] = "EXTRACTED"
                if e["context"] and e["context"] not in d["contexts"]:
                    d["contexts"].append(e["context"])
            else:
                graphe.add_edge(s, cible, relations={e["relation"]}, confidence=e["confidence"], locations=[lieu],
                                contexts=[e["context"]] if e["context"] else [])


def _reprendre(apports: list[tuple[str, dict]]) -> None:
    """Les reprises (`takeovers`), dans leur ordre : les liens qui partent de `from` depuis les lignes `lines`
    (bornes comprises) de `source_file` partent de `to`. Une reprise suivante voit les precedentes (une branche dans une branche).
    Seuls les liens des lecteurs sont repris : une extension rend les siens deja a leur place."""
    liens = [e for qui, c in apports if qui in LECTEURS for e in c.get("links", [])]
    for qui, c in apports:
        for r in c.get("takeovers", []):
            if manque := [k for k in ("from", "to", "source_file", "lines") if k not in r]:
                raise RuntimeError(f"{qui}: a takeover lacks {', '.join(manque)}")
            debut, fin = r["lines"]
            for e in liens:
                ligne = int(str(e.get("source_location", "")).lstrip("L") or 0)
                if e.get("source") == r["from"] and e.get("source_file") == r["source_file"] and debut <= ligne <= fin:
                    e["source"] = r["to"]


def assembler(verifier: bool = False) -> tuple[nx.DiGraph, dict, list[dict], dict[str, list[dict]]]:
    """Les lecteurs (et les extensions `avec_les_lecteurs`), puis le coeur, puis les autres extensions locales
    dans l'ordre de graphe.toml : le graphe oriente,
    la couverture, les liens pendants et les sites de chaque contribution."""
    configuration = graphe_racine.configuration()
    graphe = nx.DiGraph()
    pendants: list[dict] = []
    # Les lecteurs ensemble : leurs noeuds entrent tries tous a la fois, comme avant le contrat (T-0007).
    lecteurs = [(nom, contribuer(Projet(configuration.get(nom, {}), graphe, verifier)))
                for nom, contribuer in LECTEURS.items()]
    # T-0008 : une extension `with_readers` entre avec eux, avant le coeur, et peut reprendre leurs liens.
    avec, apres = [], []
    for declaration in _extensions_declarees():
        (avec if declaration.get("with_readers") else apres).append(declaration)
    lecteurs += [(d.get("path", ""), _extension(d)(Projet(d, graphe, verifier))) for d in avec]
    _reprendre(lecteurs)
    _inserer(graphe, lecteurs, pendants)
    graphe_enrichir.enrichir(graphe, RACINE)
    apports = list(lecteurs)
    for declaration in apres:
        apport = (declaration.get("path", ""), _extension(declaration)(Projet(declaration, graphe, verifier)))
        if "takeovers" in apport[1]:
            raise RuntimeError(f"{apport[0]}: takeovers without with_readers = true ({CONFIGURATION})")
        _inserer(graphe, [apport], pendants)
        apports.append(apport)
    # shortcut: un fichier declare deux fois qui rend des sites deux fois ne garde que les derniers ; a fusionner
    # si une extension en a besoin des deux cotes.
    sites = {qui: c["sites"] for qui, c in apports if "sites" in c}
    couverture = {qui: dict(Counter(s["verdict"] for s in liste if "verdict" in s).most_common())
                  for qui, liste in sites.items()}
    couverture["dangling"] = len(pendants)
    return _trie(graphe), couverture, pendants, sites


def _cle_lieu(lieu: str) -> tuple[str, int]:
    fichier, _, ligne = lieu.rpartition(":")
    chiffres = re.match(r"\d*", ligne).group()
    return fichier, int(chiffres or 0)


def _trie(graphe: nx.DiGraph) -> nx.DiGraph:
    """T-0381 : noeuds, liens et lieux dans l'ordre de leur contenu - celui des lecteurs (et du hachage) bougeait graphe.html."""
    trie = nx.DiGraph()
    trie.add_nodes_from(sorted(graphe.nodes(data=True), key=lambda n: n[0]))
    for s, c, d in sorted(graphe.edges(data=True), key=lambda e: (e[0], e[1])):
        trie.add_edge(s, c, **{**d, "locations": sorted(d["locations"], key=_cle_lieu), "contexts": sorted(d["contexts"])})
    return trie


def communautes(graphe: nx.DiGraph) -> tuple[dict[str, int], dict[int, str]]:
    a_part, prefixes = _communautes()
    non_oriente = nx.Graph()
    non_oriente.add_nodes_from(n for n in graphe.nodes if graphe.nodes[n]["kind"] not in a_part)
    for s, c, d in graphe.edges(data=True):
        if s != c and s in non_oriente and c in non_oriente:
            poids = non_oriente[s][c]["poids"] if non_oriente.has_edge(s, c) else 0
            non_oriente.add_edge(s, c, poids=poids + len(d["locations"]))
    groupes = nx.community.louvain_communities(non_oriente, weight="poids", seed=0)
    groupes = sorted(groupes, key=lambda g: (-len(g), min(g)))
    de, noms, vus = {}, {}, Counter()
    for i, groupe in enumerate(groupes):
        for n in groupe:
            de[n] = i
        fichiers = Counter(graphe.nodes[n]["source_file"] for n in sorted(groupe))  # egalites : par l'id
        (premier, nombre), *suite = fichiers.most_common(2)
        nom = _court(premier, prefixes)
        if suite and suite[0][1] * 3 >= nombre:
            nom += " + " + _court(suite[0][0], prefixes)
        vus[nom] += 1
        noms[i] = nom if vus[nom] == 1 else f"{nom} ({vus[nom]})"
    for sorte, nom in a_part.items():
        membres = [n for n, d in graphe.nodes(data=True) if d["kind"] == sorte]
        if membres:
            i = len(noms)
            noms[i] = nom
            de.update(dict.fromkeys(membres, i))
    return de, noms


def _court(fichier: str, prefixes: list[str]) -> str:
    for prefixe in prefixes:
        fichier = fichier.removeprefix(prefixe)
    return fichier.rsplit(".", 1)[0]


def disposer(graphe: nx.DiGraph, de: dict[str, int]) -> dict[str, tuple[float, float]]:
    """Chaque communaute disposee seule dans un disque, les disques poses en
    spirale du plus grand au plus petit : bien plus vite qu'une disposition
    d'ensemble (15 s pour 2400 noeuds), et sans chevauchement."""
    membres = defaultdict(list)
    for n, i in de.items():
        membres[i].append(n)
    places: list[tuple[float, float, float]] = []
    positions = {}
    for i in sorted(membres, key=lambda i: (-len(membres[i]), i)):
        rayon = math.sqrt(len(membres[i])) * 1.6 + 1.0
        if not places:
            centre = (0.0, 0.0)
        else:
            pas = 0
            while True:
                angle, distance = pas * 0.5, 2.0 * math.sqrt(pas + 1) * 3.0
                centre = (distance * math.cos(angle), distance * math.sin(angle))
                if all(math.dist(centre, (x, y)) >= r + rayon + 1.0 for x, y, r in places):
                    break
                pas += 1
        places.append((*centre, rayon))
        # T-0381 : pas graphe.subgraph(), qui parcourt ses noeuds dans l'ordre d'un ensemble (le hasard du hachage)
        groupe = sorted(membres[i])
        dedans = set(groupe)
        sous = nx.Graph()
        sous.add_nodes_from(groupe)
        sous.add_edges_from((s, c) for s, c in graphe.edges(groupe) if c in dedans)
        local = nx.spring_layout(sous, seed=0, iterations=60) if len(membres[i]) > 1 else {membres[i][0]: (0, 0)}
        for n, (x, y) in local.items():
            positions[n] = (round(centre[0] + x * rayon * 0.92, 2), round(centre[1] + y * rayon * 0.92, 2))
    return positions


def _ecrire(chemin: Path, texte: str) -> None:
    """Ecrit a cote puis remplace : deux constructions de suite ne laissent
    jamais un fichier a moitie ecrit."""
    with tempfile.NamedTemporaryFile("wb", dir=chemin.parent, delete=False, suffix=".tmp") as f:
        f.write(texte.encode("utf-8"))
    os.replace(f.name, chemin)


def construire(calme: bool = False) -> int:
    debut = time.monotonic()
    SORTIE.mkdir(exist_ok=True)
    graphe, couverture, pendants, _ = assembler()
    de, noms = communautes(graphe)
    positions = disposer(graphe, de)
    donnees = {
        "built": time.strftime("%Y-%m-%d %H:%M:%S"), "built_s": time.time(), "commit": _commit(),
        "coverage": couverture, "communities": {str(i): nom for i, nom in noms.items()},
        "nodes": [{**graphe.nodes[n], "community": de[n], "x": positions[n][0], "y": positions[n][1]}
                  for n in graphe.nodes],
        "links": [{"source": s, "target": c, "relations": sorted(d["relations"]), "confidence": d["confidence"],
                   "locations": d["locations"], "contexts": d["contexts"]} for s, c, d in graphe.edges(data=True)],
    }
    _ecrire(JSON, json.dumps(donnees, ensure_ascii=False))
    _ecrire(SORTIE / "REPORT.md", rapport(graphe, donnees, de, noms))
    _ecrire(SORTIE / "graphe.html", page(donnees))
    if not calme:
        print(f"{graphe.number_of_nodes()} nodes, {graphe.number_of_edges()} links, {len(noms)} communities, "
              f"{len(pendants)} dangling link(s) - {time.monotonic() - debut:.1f} s -> {SORTIE.relative_to(RACINE)}/")
        for e in pendants[:10]:
            print("  dangling", e["source"], "->", e["target"], e["relation"], e["source_file"], e["source_location"])
    return 0


# ---------- le rapport

def _lieu(graphe: nx.DiGraph, n: str) -> str:
    d = graphe.nodes[n]
    return f"{d['source_file']}:{d['source_location'].lstrip('L')}"


def rapport(graphe: nx.DiGraph, donnees: dict, de: dict, noms: dict) -> str:
    c = donnees["coverage"]
    sortes = Counter(d["kind"] for _, d in graphe.nodes(data=True))
    lignes = [
        "# The code graph", "",
        f"Built on {donnees['built']} (commit {donnees['commit']}, working tree included) "
        "by `graphe build`.", "",
        f"- {graphe.number_of_nodes()} nodes: " + ", ".join(f"{n} {s}" for s, n in sortes.most_common()),
        f"- {graphe.number_of_edges()} links, {len(noms)} communities, {c['dangling']} dangling link(s)",
        f"- Python calls classified: {c['python']}",
        f"- GDScript calls classified: {c['godot']}",
        "", "`ours`: linked for sure; `ours?`: linked by name alone (INFERRED); `ambiguous`: a name that "
        "several of our functions bear, on an untyped receiver - not linked; `external`, `engine`: "
        "outside the repository. Details: `graphe check`.", "",
        "## Most connected", "",
    ]
    def reels(liens) -> int:  # sans la contenance (fichier, classe -> fonction)
        return sum(1 for *_, d in liens if d["relations"] - {"contains", "method"})
    entrants = {n: reels(graphe.in_edges(n, data=True)) for n in graphe.nodes}
    sortants = {n: reels(graphe.out_edges(n, data=True)) for n in graphe.nodes}
    centraux = sorted((n for n in graphe.nodes if graphe.nodes[n]["kind"] != "file"),
                      key=lambda n: (-entrants[n] - sortants[n], n))[:20]
    for n in centraux:
        lignes.append(f"- `{graphe.nodes[n]['label']}` - {entrants[n]} incoming, "
                      f"{sortants[n]} outgoing ({_lieu(graphe, n)})")
    commandes = sorted(n for n in graphe.nodes if graphe.nodes[n]["kind"] == "command")
    if commandes:
        lignes += ["", "## Commands", "", "Each command: who sends it, what it calls.", ""]
    for n in commandes:
        envoyeurs = sorted({graphe.nodes[s]["label"] for s in graphe.predecessors(n)
                            if "sends" in graphe[s][n]["relations"]})
        appeles = sorted({graphe.nodes[x]["label"] for x in graphe.successors(n)})
        lignes.append(f"- `{graphe.nodes[n]['label']}`: sent by "
                      f"{', '.join(envoyeurs) or 'nobody'}; calls "
                      f"{', '.join(appeles[:8]) or '-'}{' …' if len(appeles) > 8 else ''}")
    imports = nx.DiGraph()
    for s, cible, d in graphe.edges(data=True):
        ss, cc = graphe.nodes[s]["source_file"], graphe.nodes[cible]["source_file"]
        if "imports" in d["relations"] and graphe.nodes[s]["kind"] == "file" and ss != cc:
            imports.add_edge(ss, cc)
    cycles = sorted((cy for cy in nx.simple_cycles(imports, length_bound=4)), key=lambda cy: (len(cy), cy))[:20]
    lignes += ["", "## Import cycles (module level)", ""]
    lignes += [f"- {' → '.join(cy + cy[:1])}" for cy in cycles] or ["None."]
    lignes += ["", "## Communities", ""]
    membres = defaultdict(list)
    for n, i in de.items():
        membres[i].append(n)
    minces = 0
    for i in sorted(membres):
        if len(membres[i]) < 4:
            minces += 1
            continue
        tete = sorted(membres[i], key=lambda n: (-graphe.degree(n), n))[:8]
        lignes += [f"### {i} - {noms[i]} ({len(membres[i])} nodes)", "",
                   ", ".join(f"`{graphe.nodes[n]['label']}`" for n in tete), ""]
    lignes += [f"{minces} small communities (fewer than 4 nodes) not detailed.", "",
               "## What the graph does not see", "",
               "- dynamic calls: `getattr`, a callback stored in a variable, a receiver that nothing "
               "types (the `ambiguous` ones);",
               "- files that no reader takes, and those that `exclude` removes (graphe.toml).", ""]
    return "\n".join(lignes)


# ---------- la page

def page(donnees: dict) -> str:
    noeuds = donnees["nodes"]
    index = {n["id"]: i for i, n in enumerate(noeuds)}
    compact = {
        "n": [[n["label"], n["source_file"], n["source_location"].lstrip("L"), n["community"], n["x"], n["y"],
               n["kind"], n["id"]] for n in noeuds],
        "l": [[index[e["source"]], index[e["target"]], ",".join(e["relations"]), e["confidence"] == "EXTRACTED"]
              for e in donnees["links"]],
        "c": donnees["communities"], "t": donnees["built"], "k": donnees["commit"],
    }
    texte = json.dumps(compact, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return PAGE.replace("__DONNEES__", texte)


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Code graph</title>
<style>
:root{--fond:#f7f7f5;--texte:#1d1d1b;--doux:#6b6b66;--panneau:#ffffff;--bord:#deded8;--lien:rgba(60,60,60,.10);--choix:#d4572a}
@media (prefers-color-scheme:dark){:root{--fond:#161615;--texte:#e8e8e3;--doux:#9a9a93;--panneau:#1f1f1d;--bord:#34342f;--lien:rgba(220,220,210,.09);--choix:#f08a5d}}
*{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--fond);color:var(--texte);font:14px/1.4 system-ui,sans-serif}
#carte{position:fixed;top:0;left:0;width:calc(100% - 340px);height:100%;cursor:grab;touch-action:none}#carte.tire{cursor:grabbing}
#cote{position:fixed;top:0;right:0;bottom:0;width:340px;background:var(--panneau);border-left:1px solid var(--bord);display:flex;flex-direction:column;overflow-x:hidden}
#cote header{padding:12px 14px;border-bottom:1px solid var(--bord)}#cote h1{font-size:15px;margin:0 0 6px}
#cote input[type=search]{width:100%;padding:7px 9px;border:1px solid var(--bord);border-radius:6px;background:var(--fond);color:var(--texte);font:inherit}
#cote label{display:block;margin-top:8px;color:var(--doux);font-size:12px}
#fiche{padding:12px 14px;overflow:auto;flex:1}#fiche h2{font-size:15px;margin:0 0 2px;word-break:break-all}
#fiche .ou{color:var(--doux);font-size:12px;margin-bottom:10px;word-break:break-all}#fiche h3{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--doux);margin:14px 0 4px}
#fiche a{color:var(--texte);text-decoration:none;display:block;padding:2px 0;border-bottom:1px dotted transparent;cursor:pointer;word-break:break-all}
#fiche a:hover{color:var(--choix)}#fiche .rel{color:var(--doux);font-size:11px}
@media (max-width:760px){#carte{width:100%;height:55vh}#cote{top:auto;height:45vh;width:100%;border-left:0;border-top:1px solid var(--bord)}}
</style></head><body>
<canvas id="carte"></canvas>
<aside id="cote"><header><h1>Code graph</h1><input id="cherche" type="search" list="noms" placeholder="Search a function, a file…" autocomplete="off"><datalist id="noms"></datalist>
<label><input id="contient" type="checkbox"> containment links (file → function)</label></header>
<div id="fiche"></div></aside>
<script id="donnees" type="application/json">__DONNEES__</script>
<script>
const D=JSON.parse(document.getElementById('donnees').textContent);
const N=D.n.map((n,i)=>({i,label:n[0],fichier:n[1],ligne:n[2],c:n[3],x:n[4],y:n[5],sorte:n[6],id:n[7],sort:[],entr:[]}));
const L=D.l.map(l=>({s:l[0],t:l[1],rel:l[2],sur:l[3]}));
for(const l of L){N[l.s].sort.push(l);N[l.t].entr.push(l)}
for(const n of N){n.deg=n.sort.length+n.entr.length;n.r=1.2+Math.sqrt(n.deg)*0.45}
const teinte=c=>`hsl(${(c*137.508)%360},55%,52%)`;
const cv=document.getElementById('carte'),cx=cv.getContext('2d');
let fit=1,vue={x:0,y:0,z:1},choisi=null,voisins=new Set(),contient=false;
function taille(){const r=cv.getBoundingClientRect(),d=devicePixelRatio||1;cv.width=r.width*d;cv.height=r.height*d;cx.setTransform(d,0,0,d,0,0);dessiner()}
function cadrer(){let a=1e9,b=1e9,c=-1e9,e=-1e9;for(const n of N){a=Math.min(a,n.x);b=Math.min(b,n.y);c=Math.max(c,n.x);e=Math.max(e,n.y)}
const r=cv.getBoundingClientRect();vue.z=fit=Math.min(r.width/(c-a+10),r.height/(e-b+10));vue.x=r.width/2-(a+c)/2*vue.z;vue.y=r.height/2-(b+e)/2*vue.z}
const ecran=n=>[n.x*vue.z+vue.x,n.y*vue.z+vue.y];
function couleur(v){return getComputedStyle(document.documentElement).getPropertyValue(v)}
function dessiner(){const r=cv.getBoundingClientRect();cx.clearRect(0,0,r.width,r.height);
cx.lineWidth=1;cx.strokeStyle=couleur('--lien');cx.beginPath();
for(const l of L){if(!contient&&(l.rel==='contains'||l.rel==='method'))continue;const[a,b]=ecran(N[l.s]),[c,d]=ecran(N[l.t]);cx.moveTo(a,b);cx.lineTo(c,d)}cx.stroke();
if(choisi){cx.strokeStyle=couleur('--choix');cx.lineWidth=1.5;cx.beginPath();for(const l of choisi.sort.concat(choisi.entr)){const[a,b]=ecran(N[l.s]),[c,d]=ecran(N[l.t]);cx.moveTo(a,b);cx.lineTo(c,d)}cx.stroke()}
for(const n of N){const[x,y]=ecran(n);if(x<-20||y<-20||x>r.width+20||y>r.height+20)continue;const rr=Math.max(1.5,n.r*Math.sqrt(vue.z));
cx.globalAlpha=choisi&&!voisins.has(n.i)&&n!==choisi?0.25:1;cx.fillStyle=n===choisi?couleur('--choix'):teinte(n.c);cx.beginPath();cx.arc(x,y,rr,0,7);cx.fill()}
cx.globalAlpha=1;cx.fillStyle=couleur('--texte');
// Des etiquettes qui ne se chevauchent pas : les plus reliees d'abord.
const poses=[],libre=(x,y,w)=>{for(const p of poses)if(x<p[2]&&x+w>p[0]&&y-11<p[3]&&y+3>p[1])return false;poses.push([x,y-11,x+w,y+3]);return true};
if(vue.z>fit*2.5){cx.font='12px system-ui';const vus=N.filter(n=>{const[x,y]=ecran(n);return x>0&&y>0&&x<r.width&&y<r.height&&(!choisi||voisins.has(n.i)||n===choisi)});
vus.sort((a,b)=>(b===choisi)-(a===choisi)||b.deg-a.deg);for(const n of vus.slice(0,600)){const[x,y]=ecran(n),w=cx.measureText(n.label).width;if(libre(x+4,y-3,w))cx.fillText(n.label,x+4,y-3)}}
else{const centres={};for(const n of N){const c=centres[n.c]||(centres[n.c]={x:0,y:0,k:0});c.x+=n.x;c.y+=n.y;c.k++}
cx.font='600 12px system-ui';for(const c of Object.keys(centres).sort((a,b)=>centres[b].k-centres[a].k)){const v=centres[c];const w=cx.measureText(D.c[c]).width,x=(v.x/v.k)*vue.z+vue.x-w/2,y=(v.y/v.k)*vue.z+vue.y;if(libre(x,y,w))cx.fillText(D.c[c],x,y)}}}
function lien(n){return `<a data-i="${n.i}">${esc(n.label)} <span class="rel">${esc(n.fichier)}:${n.ligne}</span></a>`}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function groupe(liste,bout){const g={};for(const l of liste){for(const r of l.rel.split(','))(g[r]=g[r]||[]).push(N[l[bout]])}
return Object.keys(g).sort().map(r=>`<h3>${esc(r)} (${g[r].length})</h3>`+g[r].sort((a,b)=>a.label.localeCompare(b.label)).map(lien).join('')).join('')}
function choisir(n,centrer){choisi=n;voisins=new Set();if(n){for(const l of n.sort)voisins.add(l.t);for(const l of n.entr)voisins.add(l.s)}
const f=document.getElementById('fiche');
if(!n){f.innerHTML=`<p class="ou">${N.length} nodes, ${L.length} links. Built on ${esc(D.t)} (commit ${esc(D.k)}).</p><p class="ou">Wheel: zoom. Drag: move. Click: a node and its links.</p>`}
else{f.innerHTML=`<h2>${esc(n.label)}</h2><div class="ou">${esc(n.sorte)} · ${esc(n.fichier)}:${n.ligne} · ${esc(D.c[n.c])}<br>${esc(n.id)}</div><h3 style="color:var(--texte)">What it calls</h3>${groupe(n.sort.filter(l=>l.rel!=='contains'&&l.rel!=='method'),'t')||'<p class=ou>nothing</p>'}<h3 style="color:var(--texte)">What calls it</h3>${groupe(n.entr.filter(l=>l.rel!=='contains'&&l.rel!=='method'),'s')||'<p class=ou>nothing</p>'}`}
if(n&&centrer){const r=cv.getBoundingClientRect();vue.z=Math.max(vue.z,fit*6);vue.x=r.width/2-n.x*vue.z;vue.y=r.height/2-n.y*vue.z}dessiner()}
document.getElementById('fiche').addEventListener('click',e=>{const a=e.target.closest('a[data-i]');if(a)choisir(N[+a.dataset.i],true)});
const dl=document.getElementById('noms');dl.innerHTML=N.map(n=>`<option value="${esc(n.label)} — ${esc(n.fichier)}">`).join('');
document.getElementById('cherche').addEventListener('change',e=>{const v=e.target.value.split(' — ');const n=N.find(n=>n.label===v[0]&&(!v[1]||n.fichier===v[1]))||N.find(n=>n.label.toLowerCase().includes(v[0].toLowerCase()));if(n)choisir(n,true)});
document.getElementById('contient').addEventListener('change',e=>{contient=e.target.checked;dessiner()});
let tir=null,bouge=false;
cv.addEventListener('pointerdown',e=>{tir={x:e.clientX,y:e.clientY,vx:vue.x,vy:vue.y};bouge=false;cv.classList.add('tire');cv.setPointerCapture(e.pointerId)});
cv.addEventListener('pointermove',e=>{if(!tir)return;const dx=e.clientX-tir.x,dy=e.clientY-tir.y;if(Math.abs(dx)+Math.abs(dy)>3)bouge=true;vue.x=tir.vx+dx;vue.y=tir.vy+dy;dessiner()});
cv.addEventListener('pointerup',e=>{cv.classList.remove('tire');if(!bouge){const r=cv.getBoundingClientRect(),px=e.clientX-r.left,py=e.clientY-r.top;let m=null,dm=144;
for(const n of N){const[x,y]=ecran(n),d=(x-px)**2+(y-py)**2;if(d<dm){dm=d;m=n}}choisir(m,false)}tir=null});
cv.addEventListener('wheel',e=>{e.preventDefault();const r=cv.getBoundingClientRect(),px=e.clientX-r.left,py=e.clientY-r.top,f=Math.exp(-e.deltaY*0.0015);
vue.x=px-(px-vue.x)*f;vue.y=py-(py-vue.y)*f;vue.z*=f;dessiner()},{passive:false});
addEventListener('resize',taille);taille();cadrer();choisir(null);
// graphe.html#<id> ouvre ce noeud.
const ancre=()=>{const n=N.find(n=>n.id===decodeURIComponent(location.hash.slice(1)));if(n)choisir(n,true)};addEventListener('hashchange',ancre);ancre();
</script></body></html>
"""


# ---------- les requetes

def charger(tel_quel: bool = False) -> nx.DiGraph:
    """Le graphe ; reconstruit d'abord s'il est plus ancien que le code de l'hote ou que l'outil."""
    if not JSON.exists() or (not tel_quel and max((p.stat().st_mtime for p in _sources() + _outil()), default=0)
                             > JSON.stat().st_mtime):
        print("(the graph is older than the code or the tool: rebuilding)", file=sys.stderr)
        construire(calme=True)
    donnees = json.loads(JSON.read_bytes())
    graphe = nx.DiGraph(communities=donnees["communities"])
    for n in donnees["nodes"]:
        graphe.add_node(n["id"], **n)
    for e in donnees["links"]:
        graphe.add_edge(e["source"], e["target"], **{k: v for k, v in e.items() if k not in ("source", "target")})
    return graphe


def _nu(label: str) -> str:
    return label.removesuffix("()").lstrip(".")


def _prechargements(racine: Path = RACINE) -> dict[str, set[str]]:
    """Les constantes qui prechargent un script GDScript, et ce script :
    `const Outils = preload("res://menu/outils.gd")` -> godot/menu/outils.gd (graphe_godot.GODOT)."""
    motif = re.compile(r'^const\s+(\w+)\s*=\s*preload\("res://([^"]+\.gd)"\)', re.M)
    alias: dict[str, set[str]] = defaultdict(set)
    for chemin in graphe_godot.scripts():
        for nom, cible in motif.findall(chemin.read_bytes().decode("utf-8", "replace")):
            alias[nom].add(graphe_godot.res(cible))
    return alias


def trouver(graphe: nx.DiGraph, texte: str) -> list[str]:
    if texte in graphe:
        return [texte]
    fichier, _, nom = texte.rpartition("::")
    trouves = []
    for n, d in graphe.nodes(data=True):
        if fichier and not (d["source_file"].endswith(fichier) or fichier in d["source_file"]):
            continue
        if nom in (d["name"], _nu(d["label"]), d["label"]) or d["name"].endswith("." + nom):
            trouves.append(n)
    if not trouves and not fichier and "." in nom:
        # `Outils.aider` : Outils precharge godot/menu/outils.gd.
        tete, _, membre = nom.partition(".")
        scripts = _prechargements().get(tete, set())
        trouves = [n for n, d in graphe.nodes(data=True)
                   if d["source_file"] in scripts and membre in (d["name"], _nu(d["label"]))]
    return sorted(trouves)


def _un(graphe: nx.DiGraph, texte: str) -> str | None:
    trouves = trouver(graphe, texte)
    if len(trouves) == 1:
        return trouves[0]
    if not trouves:
        print(f"no node for {texte!r} - try: graphe search {texte}")
    else:
        print(f"{texte!r} designates {len(trouves)} nodes; narrow it by id or by file::name:")
        for n in trouves:
            print(f"  {n}  ({_lieu(graphe, n)})")
    return None


def _etiquette(graphe: nx.DiGraph, n: str) -> str:
    return f"{graphe.nodes[n]['label']} ({_lieu(graphe, n)})"


def chemin(graphe: nx.DiGraph, a: str, b: str, sans_sens: bool) -> int:
    source, cible = _un(graphe, a), _un(graphe, b)
    if source is None or cible is None:
        return 2
    vu = graphe.to_undirected(as_view=True) if sans_sens else graphe
    a_part, _ = _communautes()

    def poids(x: str, y: str, _d: dict) -> int:
        # T-0354 : sans le sens, une valeur ou un ticket relie tout ce qui
        # l'ecrit ; il ne sert que faute de chemin par le code.
        hors_code = graphe.nodes[x]["kind"] in a_part or graphe.nodes[y]["kind"] in a_part
        return POIDS_HORS_CODE if sans_sens and hors_code else 1

    try:
        etapes = nx.shortest_path(vu, source, cible, weight=poids)
    except nx.NetworkXNoPath:
        print("no path" + ("" if sans_sens else " in the direction of the links (try --undirected)"))
        return 1
    print(f"{len(etapes) - 1} step(s):")
    print(f"  {_etiquette(graphe, etapes[0])}")
    for x, y in zip(etapes, etapes[1:], strict=False):
        sens, d = ("-->", graphe[x][y]) if graphe.has_edge(x, y) else ("<--", graphe[y][x])
        sur = "" if d["confidence"] == "EXTRACTED" else " [by name]"
        print(f"    {sens} {','.join(d['relations'])}{sur}  {d['locations'][0]}")
        print(f"  {_etiquette(graphe, y)}")
    return 0


def source(graphe: nx.DiGraph, n: str) -> str:
    """Les lignes du noeud, numerotees ; "" sans etendue connue."""
    d = graphe.nodes[n]
    debut, fin = int(d["source_location"].lstrip("L") or 0), int(d.get("end", 0))
    if not fin or not (RACINE / d["source_file"]).is_file():
        return ""
    lignes = (RACINE / d["source_file"]).read_bytes().decode("utf-8", "replace").splitlines()
    return "\n".join(f"{i:5d}  {lignes[i - 1]}" for i in range(debut, min(fin, len(lignes)) + 1))


def expliquer(graphe: nx.DiGraph, x: str, tout: bool, code: bool = False) -> int:
    n = _un(graphe, x)
    if n is None:
        return 2
    d = graphe.nodes[n]
    fin = f"-{d['end']}" if d.get("end") and d["end"] != int(d["source_location"].lstrip("L") or 0) else ""
    print(f"{d['label']}  [{d['kind']}]  {_lieu(graphe, n)}{fin}")
    print(f"  id: {n}")
    print(f"  community: {graphe.graph['communities'][str(d['community'])]}")
    if d.get("notes"):
        print(f"  note: {d['notes'][:300]}")
    for texte in d.get("texts", [])[:10]:
        print(f"  displays: {texte}")
    if code:
        print("\n" + (source(graphe, n) or "  (no known extent)"))
    limite = None if tout else 25
    for titre, paires in (("what it calls", [(c, graphe[n][c]) for c in graphe.successors(n)]),
                          ("what calls it", [(s, graphe[s][n]) for s in graphe.predecessors(n)])):
        par = defaultdict(list)
        for autre, lien in paires:
            for r in lien["relations"]:
                par[r].append((autre, lien))
        print(f"\n{titre}:" + ("" if par else " nothing"))
        for r in sorted(par):
            print(f"  {r} ({len(par[r])})")
            for autre, lien in sorted(par[r], key=lambda p: _etiquette(graphe, p[0]))[:limite]:
                sur = "" if lien["confidence"] == "EXTRACTED" else " [by name]"
                print(f"    {_etiquette(graphe, autre)}{sur}")
            if limite and len(par[r]) > limite:
                print(f"    ... and {len(par[r]) - limite} more (--all)")
    return 0


def appelants(graphe: nx.DiGraph, x: str, profondeur: int) -> int:
    n = _un(graphe, x)
    if n is None:
        return 2
    vus, front = {n}, [n]
    for niveau in range(1, profondeur + 1):
        suivant = []
        for y in front:
            for s in graphe.predecessors(y):
                if s not in vus and APPELS & set(graphe[s][y]["relations"]):
                    vus.add(s)
                    suivant.append(s)
        if not suivant:
            break
        print(f"level {niveau} ({len(suivant)}):")
        for s in sorted(suivant, key=lambda s: _etiquette(graphe, s)):
            print(f"  {_etiquette(graphe, s)}")
        front = suivant
    if len(vus) == 1:
        print("nothing calls it (in what the graph sees)")
    return 0


# `def reset`, `func _ready`, `class Gabarit` : le nom, sans le mot du langage.
MOTS_DE_TETE = re.compile(r"^(?:async\s+def|def|static\s+func|func|class|function|const|var)\s+")


def recherche(graphe: nx.DiGraph, motif: str) -> list[tuple[str, str]]:
    """(noeud, ou) : par le nom d'abord ; puis, si un texte affiche ou un
    commentaire le contient, avec ce qui l'a trouve."""
    motif = MOTS_DE_TETE.sub("", motif.strip()).lower()
    par_nom = sorted(n for n, d in graphe.nodes(data=True)
                     if motif in n.lower() or motif in d["label"].lower() or motif in d["name"].lower())
    vus = set(par_nom)
    autres = []
    for n, d in sorted(graphe.nodes(data=True)):
        if n in vus:
            continue
        texte = next((t for t in d.get("texts", []) if motif in t.lower()), None)
        if texte is not None:
            autres.append((n, f"displays \"{texte[:60]}\""))
        elif motif in d.get("notes", "").lower():
            autres.append((n, "comment"))
    return [(n, "") for n in par_nom] + autres


def chercher(graphe: nx.DiGraph, motif: str) -> int:
    trouves = recherche(graphe, motif)
    for n, ou in trouves[:60]:
        print(f"  {graphe.nodes[n]['label']:40s} {_lieu(graphe, n):45s} {n}" + (f"  ({ou})" if ou else ""))
    print(f"{len(trouves)} node(s)" + (" (60 shown)" if len(trouves) > 60 else ""))
    return 0 if trouves else 1


def verifier() -> int:
    """La couverture de chaque contribution, lue dans ses sites : le classement des appels, les noms les plus
    frequents de chaque verdict, puis les alertes ; un echec s'il y a une alerte ou un lien pendant."""
    _, _, pendants, sites = assembler(verifier=True)
    alertes = 0
    for qui, liste in sites.items():
        verdicts = Counter(s["verdict"] for s in liste if "verdict" in s)
        print(f"== {qui}: {sum(verdicts.values())} sites classified {dict(verdicts.most_common())}")
        for verdict, n in verdicts.most_common():
            noms = Counter(s["text"] for s in liste if s.get("verdict") == verdict)
            print(f"  {verdict} ({n}): {dict(noms.most_common(12))}")
        a_signaler = [s for s in liste if "alert" in s]
        alertes += len(a_signaler)
        print(f"  alerts: {len(a_signaler)}")
        for s in a_signaler[:60]:
            print(f"    {s['file']}:{s['line']} {s['text']} ({s['alert']})")
        print()
    print(f"== Graph: {len(pendants)} dangling link(s)")
    for e in pendants[:20]:
        print("  ", e["source"], "->", e["target"], e["relation"], e["source_file"], e["source_location"])
    return 1 if alertes or pendants else 0


# ---------- les crochets git

def _dossier_des_crochets() -> Path:
    r = subprocess.run(["git", "rev-parse", "--git-path", "hooks"], cwd=RACINE, capture_output=True, text=True,
                       check=True)
    chemin = Path(r.stdout.strip())
    return chemin if chemin.is_absolute() else RACINE / chemin


def _sans_bloc(texte: str) -> str:
    """Le crochet tel qu'avant `install`, a l'octet pres : le bloc est un ajout exact."""
    for ouvre, ferme in BLOCS:
        debut = texte.find("\n" + ouvre)
        fin = texte.find(ferme, debut)
        if debut >= 0 and fin >= 0:
            # Jusqu'a la fin de la ligne qui ferme le bloc, LF ou CRLF (un editeur a pu convertir le crochet) : un
            # bloc reconnu n'est jamais double.
            texte = texte[:debut] + texte[fin:].partition("\n")[2]
    return texte


def _ignorer_la_sortie() -> None:
    """Ajoute la sortie au .gitignore de l'hote, sauf si git l'ignore deja (sous quelque forme que ce soit)."""
    if subprocess.run(["git", "check-ignore", "-q", f"{SORTIE.name}/"], cwd=RACINE).returncode == 0:
        return
    chemin = RACINE / ".gitignore"
    texte = chemin.read_bytes() if chemin.exists() else b""  # en octets : un .gitignore hors UTF-8 reste intact
    chemin.write_bytes(texte + (b"\n" if texte and not texte.endswith(b"\n") else b"") + f"/{SORTIE.name}/\n".encode())
    print(f"  .gitignore: /{SORTIE.name}/ added")


def installer(retirer: bool = False) -> int:
    """Pose (ou retire) le bloc qui reconstruit le graphe dans chaque
    crochet ; un crochet deja la garde ce qu'il faisait."""
    dossier = _dossier_des_crochets()
    dossier.mkdir(parents=True, exist_ok=True)
    # shortcut: `graphe` doit etre dans le PATH du shell de git, sinon le crochet echoue en silence (la requete
    # suivante reconstruit quand meme) ; un chemin absolu si un client git n'herite pas du PATH.
    bloc = f"\n{BLOCS[0][0]} (graphe install)\ngraphe build --quiet >/dev/null 2>&1 &\n{BLOCS[0][1]}\n"
    for nom in CROCHETS:
        chemin = dossier / nom
        texte = _sans_bloc(chemin.read_bytes().decode("utf-8") if chemin.exists() else "#!/bin/sh\n")
        if not retirer:
            texte += bloc
        # shortcut: un crochet de l'hote reduit a `#!/bin/sh` est efface comme ceux qu'installer a crees ; a
        # distinguer si un hote en garde un.
        if retirer and texte.strip() in ("", "#!/bin/sh"):
            chemin.unlink(missing_ok=True)
            print(f"  {nom}: removed")
            continue
        chemin.write_bytes(texte.encode("utf-8"))
        chemin.chmod(0o755)
        print(f"  {nom}: {'block removed' if retirer else 'set'} ({chemin})")
    if not retirer:
        _ignorer_la_sortie()
    return 0


def _option(arguments: list[str], nom: str, defaut: int) -> int:
    return int(arguments[arguments.index(nom) + 1]) if nom in arguments else defaut


def main(arguments: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if arguments is None else arguments  # la commande `graphe`
    # Lu par un autre programme (un agent, un tube), cp1252 sortait « D?fi ».
    if not sys.stdout.isatty():
        sys.stdout.reconfigure(encoding="utf-8")
    commande, reste = (arguments[0], arguments[1:]) if arguments else ("", [])
    positionnels = [a for i, a in enumerate(reste) if not a.startswith("--")
                    and not (i and reste[i - 1] == "--depth")]
    if commande == "build":
        try:
            return construire(calme="--quiet" in reste)
        except Exception as e:
            if "--quiet" not in reste:
                if isinstance(e, RuntimeError):  # une extension introuvable, un noeud incomplet : le message suffit
                    print(f"graphe: {e}", file=sys.stderr)
                    return 1
                raise
            import traceback  # noqa: PLC0415 - le chemin d'erreur seul
            SORTIE.mkdir(exist_ok=True)
            (SORTIE / "error.txt").write_bytes(traceback.format_exc().encode("utf-8"))
            return 1
    if commande == "check":
        return verifier()
    if commande == "install":
        return installer(retirer="--remove" in reste)
    if commande == "path" and len(positionnels) == 2:
        return chemin(charger(), *positionnels, sans_sens="--undirected" in reste)
    if commande == "explain" and len(positionnels) == 1:
        return expliquer(charger(), positionnels[0], tout="--all" in reste, code="--source" in reste)
    if commande == "callers" and len(positionnels) == 1:
        return appelants(charger(), positionnels[0], _option(reste, "--depth", 2))
    if commande == "search" and len(positionnels) == 1:
        return chercher(charger(), positionnels[0])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
