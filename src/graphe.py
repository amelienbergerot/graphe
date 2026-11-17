"""Le graphe du code de Grid Zero : la simulation Python et le client Godot.

    python tools/graphe.py construire [--calme]      graphe/ : graphe.json, RAPPORT.md, graphe.html
    python tools/graphe.py verifier                  la couverture des deux lecteurs
    python tools/graphe.py chemin A B [--sans-sens]  le plus court chemin de A a B
    python tools/graphe.py expliquer X [--tout] [--source]   ce que X appelle, ce qui l'appelle (et son code)
    python tools/graphe.py appelants X [--profondeur N]
    python tools/graphe.py chercher MOTIF            par le nom, puis les textes affiches et les commentaires
    python tools/graphe.py installer [--retirer]     les crochets git qui le reconstruisent

Un noeud se designe par son id, par son nom (`set_storage_dispatch`,
`ScenarioRunner.tick`), par `fichier::nom` (`scenario.py::tick`) ou, cote
GDScript, par la constante qui precharge son script (`Progress.record`).

Les lecteurs : tools/graphe_python.py (l'ast, les appels resolus par les
types), tools/graphe_godot.py (le GDScript, par motifs) et
tools/graphe_php.py (le service en ligne, ses fonctions et ses actions).
tools/graphe_enrichir.py lit ensuite le texte : la fin de chaque fonction
et de chaque classe, ses textes affiches, son commentaire, les variables de
module et qui les lit, les cles de l'etat que le client lit, et les tickets
(tickets/T-*.md) - qui les cite, ce qu'ils nomment. Les champs d'une classe
sont des noeuds (le lecteur Python).

Les fichiers lus (T-0004, graphe_racine.py) : ceux que git suit, plus les
non suivis non ignores, chacun au lecteur de son extension ; `exclure`, dans
un graphe.toml facultatif a la racine de l'hote, en retire des dossiers.

La mise a jour : `installer` pose des crochets git (post-commit, post-merge,
post-checkout, post-rewrite) qui reconstruisent le graphe en arriere-plan ;
et une requete sur un graphe plus ancien que le code le reconstruit
d'abord.
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx

import graphe_enrichir
import graphe_godot
import graphe_php
import graphe_python
from graphe_racine import CONFIGURATION, RACINE, SORTIE

JSON = SORTIE / "graphe.json"
CROCHETS = ("post-commit", "post-merge", "post-checkout", "post-rewrite")
DEBUT_BLOC = "# >>> graphe du code (python tools/graphe.py installer)"
FIN_BLOC = "# <<< graphe du code"
# Ce qui fait passer de l'appelant a l'appele.
APPELS = {"calls", "uses", "references", "indirect_call", "sends", "dispatches", "lit", "ecrit", "valeur"}
# T-0354 : des noeuds qui ne sont pas du code, chacun leur communaute - un
# ticket ou une valeur relie des fichiers que rien d'autre ne relie, et
# fondrait des communautes sans rapport.
A_PART = {"ticket": "tickets", "valeur": "valeurs", "conseil": "conseils", "iteration": "journal"}
POIDS_HORS_CODE = 4


# ---------- construire

def _sources() -> list[Path]:
    return [p for p in graphe_python.fichiers() + graphe_godot.scripts() + graphe_php.fichiers()
            + sorted((RACINE / "tickets").glob("T-*.md")) + sorted((RACINE / "scenarios").glob("*/scenario.toml"))
            + [RACINE / "docs" / "moonshot" / "journal.md", RACINE / CONFIGURATION] if p.is_file()]


def _commit() -> str | None:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RACINE, capture_output=True, text=True,
                           timeout=10)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def assembler():
    """Les deux lectures fondues en un graphe oriente ; un lien par paire de
    noeuds, qui garde ses relations et ses lieux."""
    python = graphe_python.Lecture()
    godot = graphe_godot.Extraction()
    php = graphe_php.Lecture()
    noeuds = python.noeuds + godot.noeuds + php.noeuds
    liens = python.liens + godot.graphe()["edges"] + php.liens
    graphe = nx.DiGraph()
    for n in sorted(noeuds, key=lambda n: n["id"]):
        graphe.add_node(n["id"], **n)
    pendants = []
    for e in liens:
        s, c = e["source"], e["target"]
        if s not in graphe or c not in graphe:
            pendants.append(e)
            continue
        lieu = f"{e['source_file']}:{e['source_location'].lstrip('L')}"
        if graphe.has_edge(s, c):
            d = graphe[s][c]
            d["relations"].add(e["relation"])
            if lieu not in d["lieux"]:
                d["lieux"].append(lieu)
            if e["confidence"] == "EXTRACTED":
                d["confiance"] = "EXTRACTED"
            if e["context"] and e["context"] not in d["contextes"]:
                d["contextes"].append(e["context"])
        else:
            graphe.add_edge(s, c, relations={e["relation"]}, confiance=e["confidence"], lieux=[lieu],
                            contextes=[e["context"]] if e["context"] else [])
    couverture = {"python": dict(Counter(s["verdict"] for s in python.sites).most_common()),
                  "godot": dict(Counter(s["verdict"] for s in godot.sites).most_common()),
                  "pendants": len(pendants), "ordres_inconnus": len(godot.ordres_inconnus)}
    graphe_enrichir.enrichir(graphe, RACINE)
    return _trie(graphe), couverture, pendants


def _cle_lieu(lieu: str) -> tuple[str, int]:
    fichier, _, ligne = lieu.rpartition(":")
    chiffres = re.match(r"\d*", ligne).group()
    return fichier, int(chiffres or 0)


def _trie(graphe: nx.DiGraph) -> nx.DiGraph:
    """T-0381 : noeuds, liens et lieux dans l'ordre de leur contenu - celui des lecteurs (et du hachage) bougeait graphe.html."""
    trie = nx.DiGraph()
    trie.add_nodes_from(sorted(graphe.nodes(data=True), key=lambda n: n[0]))
    for s, c, d in sorted(graphe.edges(data=True), key=lambda e: (e[0], e[1])):
        trie.add_edge(s, c, **{**d, "lieux": sorted(d["lieux"], key=_cle_lieu), "contextes": sorted(d["contextes"])})
    return trie


def communautes(graphe: nx.DiGraph) -> tuple[dict[str, int], dict[int, str]]:
    non_oriente = nx.Graph()
    non_oriente.add_nodes_from(n for n in graphe.nodes if graphe.nodes[n]["sorte"] not in A_PART)
    for s, c, d in graphe.edges(data=True):
        if s != c and s in non_oriente and c in non_oriente:
            poids = non_oriente[s][c]["poids"] if non_oriente.has_edge(s, c) else 0
            non_oriente.add_edge(s, c, poids=poids + len(d["lieux"]))
    groupes = nx.community.louvain_communities(non_oriente, weight="poids", seed=0)
    groupes = sorted(groupes, key=lambda g: (-len(g), min(g)))
    de, noms, vus = {}, {}, Counter()
    for i, groupe in enumerate(groupes):
        for n in groupe:
            de[n] = i
        fichiers = Counter(graphe.nodes[n]["source_file"] for n in sorted(groupe))  # egalites : par l'id
        (premier, nombre), *suite = fichiers.most_common(2)
        nom = _court(premier)
        if suite and suite[0][1] * 3 >= nombre:
            nom += " + " + _court(suite[0][0])
        vus[nom] += 1
        noms[i] = nom if vus[nom] == 1 else f"{nom} ({vus[nom]})"
    for sorte, nom in A_PART.items():
        a_part = [n for n, d in graphe.nodes(data=True) if d["sorte"] == sorte]
        if a_part:
            i = len(noms)
            noms[i] = nom
            de.update(dict.fromkeys(a_part, i))
    return de, noms


def _court(fichier: str) -> str:
    for prefixe in ("simulation/", "godot/"):
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
    graphe, couverture, pendants = assembler()
    de, noms = communautes(graphe)
    positions = disposer(graphe, de)
    donnees = {
        "construit": time.strftime("%Y-%m-%d %H:%M:%S"), "construit_s": time.time(), "commit": _commit(),
        "couverture": couverture, "communautes": {str(i): nom for i, nom in noms.items()},
        "noeuds": [{**graphe.nodes[n], "communaute": de[n], "x": positions[n][0], "y": positions[n][1]}
                   for n in graphe.nodes],
        "liens": [{"source": s, "target": c, "relations": sorted(d["relations"]), "confiance": d["confiance"],
                   "lieux": d["lieux"], "contextes": d["contextes"]} for s, c, d in graphe.edges(data=True)],
    }
    _ecrire(JSON, json.dumps(donnees, ensure_ascii=False))
    _ecrire(SORTIE / "RAPPORT.md", rapport(graphe, donnees, de, noms))
    _ecrire(SORTIE / "graphe.html", page(donnees))
    if not calme:
        print(f"{graphe.number_of_nodes()} noeuds, {graphe.number_of_edges()} liens, {len(noms)} communautes, "
              f"{len(pendants)} lien(s) pendant(s) - {time.monotonic() - debut:.1f} s -> {SORTIE.relative_to(RACINE)}/")
        for e in pendants[:10]:
            print("  pendant", e["source"], "->", e["target"], e["relation"], e["source_file"], e["source_location"])
    return 0


# ---------- le rapport

def _lieu(graphe: nx.DiGraph, n: str) -> str:
    d = graphe.nodes[n]
    return f"{d['source_file']}:{d['source_location'].lstrip('L')}"


def rapport(graphe: nx.DiGraph, donnees: dict, de: dict, noms: dict) -> str:
    c = donnees["couverture"]
    sortes = Counter(d["sorte"] for _, d in graphe.nodes(data=True))
    lignes = [
        "# Le graphe du code", "",
        f"Construit le {donnees['construit']} (commit {donnees['commit']}, arbre de travail compris) "
        "par `python tools/graphe.py construire`.", "",
        f"- {graphe.number_of_nodes()} nœuds : " + ", ".join(f"{n} {s}" for s, n in sortes.most_common()),
        f"- {graphe.number_of_edges()} liens, {len(noms)} communautés, {c['pendants']} lien(s) pendant(s)",
        f"- Appels Python classés : {c['python']}",
        f"- Appels GDScript classés : {c['godot']}",
        "", "`notre` : relié à coup sûr ; `notre?` : relié par le nom seul (INFERRED) ; `ambigu` : un nom que "
        "portent plusieurs de nos fonctions, sur un récepteur non typé - non relié ; `externe`, `moteur` : "
        "hors du dépôt. Le détail : `python tools/graphe.py verifier`.", "",
        "## Les plus reliés", "",
    ]
    def reels(liens) -> int:  # sans la contenance (fichier, classe -> fonction)
        return sum(1 for *_, d in liens if d["relations"] - {"contains", "method"})
    entrants = {n: reels(graphe.in_edges(n, data=True)) for n in graphe.nodes}
    sortants = {n: reels(graphe.out_edges(n, data=True)) for n in graphe.nodes}
    centraux = sorted((n for n in graphe.nodes if graphe.nodes[n]["sorte"] != "fichier"),
                      key=lambda n: (-entrants[n] - sortants[n], n))[:20]
    for n in centraux:
        lignes.append(f"- `{graphe.nodes[n]['label']}` - {entrants[n]} entrants, "
                      f"{sortants[n]} sortants ({_lieu(graphe, n)})")
    lignes += ["", "## Du client au serveur", "",
               "Chaque ordre du client relié à la branche de `handle_command` qui le traite.", ""]
    commandes = sorted(n for n in graphe.nodes if graphe.nodes[n]["sorte"] == "commande")
    for n in commandes:
        envoyeurs = sorted({graphe.nodes[s]["label"] for s in graphe.predecessors(n)
                            if "sends" in graphe[s][n]["relations"]})
        appeles = sorted({graphe.nodes[x]["label"] for x in graphe.successors(n)})
        lignes.append(f"- `{graphe.nodes[n]['nom'].removeprefix('cmd:')}` : envoyé par "
                      f"{', '.join(envoyeurs) or 'aucun script du client'} ; appelle "
                      f"{', '.join(appeles[:8]) or '-'}{' …' if len(appeles) > 8 else ''}")
    imports = nx.DiGraph()
    for s, cible, d in graphe.edges(data=True):
        ss, cc = graphe.nodes[s]["source_file"], graphe.nodes[cible]["source_file"]
        if "imports" in d["relations"] and graphe.nodes[s]["sorte"] == "fichier" and ss != cc:
            imports.add_edge(ss, cc)
    cycles = sorted((cy for cy in nx.simple_cycles(imports, length_bound=4)), key=lambda cy: (len(cy), cy))[:20]
    lignes += ["", "## Cycles d'import (au niveau des modules)", ""]
    lignes += [f"- {' → '.join(cy + cy[:1])}" for cy in cycles] or ["Aucun."]
    lignes += ["", "## Communautés", ""]
    membres = defaultdict(list)
    for n, i in de.items():
        membres[i].append(n)
    minces = 0
    for i in sorted(membres):
        if len(membres[i]) < 4:
            minces += 1
            continue
        tete = sorted(membres[i], key=lambda n: (-graphe.degree(n), n))[:8]
        lignes += [f"### {i} - {noms[i]} ({len(membres[i])} nœuds)", "",
                   ", ".join(f"`{graphe.nodes[n]['label']}`" for n in tete), ""]
    lignes += [f"{minces} communauté(s) de moins de 4 nœuds non détaillée(s).", "",
               "## Ce que le graphe ne voit pas", "",
               "- les appels dynamiques : `getattr`, un rappel rangé dans une variable, un récepteur que rien "
               "ne type (les `ambigu`) ;",
               "- les tests, build/, web/, les scénarios .toml, les shaders, la documentation ;",
               "- le JavaScript de tools/ (drift_references.mjs).", ""]
    return "\n".join(lignes)


# ---------- la page

def page(donnees: dict) -> str:
    noeuds = donnees["noeuds"]
    index = {n["id"]: i for i, n in enumerate(noeuds)}
    compact = {
        "n": [[n["label"], n["source_file"], n["source_location"].lstrip("L"), n["communaute"], n["x"], n["y"],
               n["sorte"], n["id"]] for n in noeuds],
        "l": [[index[e["source"]], index[e["target"]], ",".join(e["relations"]), e["confiance"] == "EXTRACTED"]
              for e in donnees["liens"]],
        "c": donnees["communautes"], "t": donnees["construit"], "k": donnees["commit"],
    }
    texte = json.dumps(compact, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return PAGE.replace("__DONNEES__", texte)


PAGE = r"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Graphe du code</title>
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
<aside id="cote"><header><h1>Graphe du code</h1><input id="cherche" type="search" list="noms" placeholder="Chercher une fonction, un fichier…" autocomplete="off"><datalist id="noms"></datalist>
<label><input id="contient" type="checkbox"> liens de contenance (fichier → fonction)</label></header>
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
if(!n){f.innerHTML=`<p class="ou">${N.length} nœuds, ${L.length} liens. Construit le ${esc(D.t)} (commit ${esc(D.k)}).</p><p class="ou">Molette : zoom. Glisser : déplacer. Clic : un nœud et ses liens.</p>`}
else{f.innerHTML=`<h2>${esc(n.label)}</h2><div class="ou">${esc(n.sorte)} · ${esc(n.fichier)}:${n.ligne} · ${esc(D.c[n.c])}<br>${esc(n.id)}</div><h3 style="color:var(--texte)">Ce qu'il appelle</h3>${groupe(n.sort.filter(l=>l.rel!=='contains'&&l.rel!=='method'),'t')||'<p class=ou>rien</p>'}<h3 style="color:var(--texte)">Ce qui l'appelle</h3>${groupe(n.entr.filter(l=>l.rel!=='contains'&&l.rel!=='method'),'s')||'<p class=ou>rien</p>'}`}
if(n&&centrer){const r=cv.getBoundingClientRect();vue.z=Math.max(vue.z,fit*6);vue.x=r.width/2-n.x*vue.z;vue.y=r.height/2-n.y*vue.z}dessiner()}
document.getElementById('fiche').addEventListener('click',e=>{const a=e.target.closest('a[data-i]');if(a)choisir(N[+a.dataset.i],true)});
const dl=document.getElementById('noms');dl.innerHTML=N.filter(n=>n.sorte!=='fichier'||true).map(n=>`<option value="${esc(n.label)} — ${esc(n.fichier)}">`).join('');
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
    """Le graphe ; reconstruit d'abord s'il est plus ancien que le code."""
    if not JSON.exists() or (not tel_quel and max((p.stat().st_mtime for p in _sources()), default=0) > JSON.stat().st_mtime):
        print("(le graphe est plus ancien que le code : reconstruction)", file=sys.stderr)
        construire(calme=True)
    donnees = json.loads(JSON.read_bytes())
    graphe = nx.DiGraph(communautes=donnees["communautes"])
    for n in donnees["noeuds"]:
        graphe.add_node(n["id"], **n)
    for e in donnees["liens"]:
        graphe.add_edge(e["source"], e["target"], **{k: v for k, v in e.items() if k not in ("source", "target")})
    return graphe


def _nu(label: str) -> str:
    return label.removesuffix("()").lstrip(".")


def _prechargements(racine: Path = RACINE) -> dict[str, set[str]]:
    """Les constantes qui prechargent un script GDScript, et ce script :
    `const Progress = preload("res://settings/progress.gd")` -> godot/settings/progress.gd."""
    motif = re.compile(r'^const\s+(\w+)\s*=\s*preload\("res://([^"]+\.gd)"\)', re.M)
    alias: dict[str, set[str]] = defaultdict(set)
    for chemin in graphe_godot.scripts():
        for nom, cible in motif.findall(chemin.read_bytes().decode("utf-8", "replace")):
            alias[nom].add("godot/" + cible)
    return alias


def trouver(graphe: nx.DiGraph, texte: str) -> list[str]:
    if texte in graphe:
        return [texte]
    fichier, _, nom = texte.rpartition("::")
    trouves = []
    for n, d in graphe.nodes(data=True):
        if fichier and not (d["source_file"].endswith(fichier) or fichier in d["source_file"]):
            continue
        if nom in (d["nom"], _nu(d["label"]), d["label"]) or d["nom"].endswith("." + nom):
            trouves.append(n)
    if not trouves and not fichier and "." in nom:
        # `Progress.record` : Progress precharge godot/settings/progress.gd.
        tete, _, membre = nom.partition(".")
        scripts = _prechargements().get(tete, set())
        trouves = [n for n, d in graphe.nodes(data=True)
                   if d["source_file"] in scripts and membre in (d["nom"], _nu(d["label"]))]
    return sorted(trouves)


def _un(graphe: nx.DiGraph, texte: str) -> str | None:
    trouves = trouver(graphe, texte)
    if len(trouves) == 1:
        return trouves[0]
    if not trouves:
        print(f"aucun noeud pour {texte!r} - essayer : python tools/graphe.py chercher {texte}")
    else:
        print(f"{texte!r} designe {len(trouves)} noeuds ; preciser par l'id ou par fichier::nom :")
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

    def poids(x: str, y: str, _d: dict) -> int:
        # T-0354 : sans le sens, une valeur ou un ticket relie tout ce qui
        # l'ecrit ; il ne sert que faute de chemin par le code.
        hors_code = graphe.nodes[x]["sorte"] in A_PART or graphe.nodes[y]["sorte"] in A_PART
        return POIDS_HORS_CODE if sans_sens and hors_code else 1

    try:
        etapes = nx.shortest_path(vu, source, cible, weight=poids)
    except nx.NetworkXNoPath:
        print("aucun chemin" + ("" if sans_sens else " dans le sens des liens (essayer --sans-sens)"))
        return 1
    print(f"{len(etapes) - 1} etape(s) :")
    print(f"  {_etiquette(graphe, etapes[0])}")
    for x, y in zip(etapes, etapes[1:], strict=False):
        sens, d = ("-->", graphe[x][y]) if graphe.has_edge(x, y) else ("<--", graphe[y][x])
        sur = "" if d["confiance"] == "EXTRACTED" else " [par le nom]"
        print(f"    {sens} {','.join(d['relations'])}{sur}  {d['lieux'][0]}")
        print(f"  {_etiquette(graphe, y)}")
    return 0


def source(graphe: nx.DiGraph, n: str) -> str:
    """Les lignes du noeud, numerotees ; "" sans etendue connue."""
    d = graphe.nodes[n]
    debut, fin = int(d["source_location"].lstrip("L") or 0), int(d.get("fin", 0))
    if not fin or not (RACINE / d["source_file"]).is_file():
        return ""
    lignes = (RACINE / d["source_file"]).read_bytes().decode("utf-8", "replace").splitlines()
    return "\n".join(f"{i:5d}  {lignes[i - 1]}" for i in range(debut, min(fin, len(lignes)) + 1))


def expliquer(graphe: nx.DiGraph, x: str, tout: bool, code: bool = False) -> int:
    n = _un(graphe, x)
    if n is None:
        return 2
    d = graphe.nodes[n]
    fin = f"-{d['fin']}" if d.get("fin") and d["fin"] != int(d["source_location"].lstrip("L") or 0) else ""
    print(f"{d['label']}  [{d['sorte']}]  {_lieu(graphe, n)}{fin}")
    print(f"  id : {n}")
    print(f"  communaute : {graphe.graph['communautes'][str(d['communaute'])]}")
    if d.get("notes"):
        print(f"  note : {d['notes'][:300]}")
    for texte in d.get("textes", [])[:10]:
        print(f"  affiche : {texte}")
    if code:
        print("\n" + (source(graphe, n) or "  (pas d'etendue connue)"))
    limite = None if tout else 25
    for titre, paires in (("ce qu'il appelle", [(c, graphe[n][c]) for c in graphe.successors(n)]),
                          ("ce qui l'appelle", [(s, graphe[s][n]) for s in graphe.predecessors(n)])):
        par = defaultdict(list)
        for autre, lien in paires:
            for r in lien["relations"]:
                par[r].append((autre, lien))
        print(f"\n{titre} :" + ("" if par else " rien"))
        for r in sorted(par):
            print(f"  {r} ({len(par[r])})")
            for autre, lien in sorted(par[r], key=lambda p: _etiquette(graphe, p[0]))[:limite]:
                sur = "" if lien["confiance"] == "EXTRACTED" else " [par le nom]"
                print(f"    {_etiquette(graphe, autre)}{sur}")
            if limite and len(par[r]) > limite:
                print(f"    ... et {len(par[r]) - limite} de plus (--tout)")
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
        print(f"niveau {niveau} ({len(suivant)}) :")
        for s in sorted(suivant, key=lambda s: _etiquette(graphe, s)):
            print(f"  {_etiquette(graphe, s)}")
        front = suivant
    if len(vus) == 1:
        print("personne ne l'appelle (dans ce que le graphe voit)")
    return 0


# `def reset`, `func _ready`, `class Gabarit` : le nom, sans le mot du langage.
MOTS_DE_TETE = re.compile(r"^(?:async\s+def|def|static\s+func|func|class|function|const|var)\s+")


def recherche(graphe: nx.DiGraph, motif: str) -> list[tuple[str, str]]:
    """(noeud, ou) : par le nom d'abord ; puis, si un texte affiche ou un
    commentaire le contient, avec ce qui l'a trouve."""
    motif = MOTS_DE_TETE.sub("", motif.strip()).lower()
    par_nom = sorted(n for n, d in graphe.nodes(data=True)
                     if motif in n.lower() or motif in d["label"].lower() or motif in d["nom"].lower())
    vus = set(par_nom)
    autres = []
    for n, d in sorted(graphe.nodes(data=True)):
        if n in vus:
            continue
        texte = next((t for t in d.get("textes", []) if motif in t.lower()), None)
        if texte is not None:
            autres.append((n, f"affiche « {texte[:60]} »"))
        elif motif in d.get("notes", "").lower():
            autres.append((n, "commentaire"))
    return [(n, "") for n in par_nom] + autres


def chercher(graphe: nx.DiGraph, motif: str) -> int:
    trouves = recherche(graphe, motif)
    for n, ou in trouves[:60]:
        print(f"  {graphe.nodes[n]['label']:40s} {_lieu(graphe, n):45s} {n}" + (f"  ({ou})" if ou else ""))
    print(f"{len(trouves)} noeud(s)" + (" (60 montres)" if len(trouves) > 60 else ""))
    return 0 if trouves else 1


def verifier() -> int:
    print("== Python")
    python = graphe_python.verifier()
    print("\n== GDScript")
    godot = graphe_godot.verifier()
    _, couverture, pendants = assembler()
    print(f"\n== Graphe : {len(pendants)} lien(s) pendant(s)")
    for e in pendants[:20]:
        print("  ", e["source"], "->", e["target"], e["relation"], e["source_file"], e["source_location"])
    return 1 if python or godot or pendants else 0


# ---------- les crochets git

def _dossier_des_crochets() -> Path:
    r = subprocess.run(["git", "rev-parse", "--git-path", "hooks"], cwd=RACINE, capture_output=True, text=True,
                       check=True)
    chemin = Path(r.stdout.strip())
    return chemin if chemin.is_absolute() else RACINE / chemin


def _sans_bloc(texte: str) -> str:
    if DEBUT_BLOC not in texte:
        return texte
    avant, _, reste = texte.partition(DEBUT_BLOC)
    _, _, apres = reste.partition(FIN_BLOC)
    return avant.rstrip("\n") + "\n" + apres.lstrip("\n")


def installer(retirer: bool = False, dossier: Path | None = None) -> int:
    """Pose (ou retire) le bloc qui reconstruit le graphe dans chaque
    crochet ; un crochet deja la garde ce qu'il faisait."""
    dossier = dossier or _dossier_des_crochets()
    dossier.mkdir(parents=True, exist_ok=True)
    python = Path(sys.executable).as_posix()
    bloc = (f'{DEBUT_BLOC}\n"{python}" "$(git rev-parse --show-toplevel)/tools/graphe.py" construire --calme '
            f'>/dev/null 2>&1 &\n{FIN_BLOC}\n')
    for nom in CROCHETS:
        chemin = dossier / nom
        texte = chemin.read_bytes().decode("utf-8") if chemin.exists() else "#!/bin/sh\n"
        texte = _sans_bloc(texte)
        if not retirer:
            texte = texte.rstrip("\n") + "\n" + bloc
        if retirer and texte.strip() in ("", "#!/bin/sh"):
            chemin.unlink(missing_ok=True)
            print(f"  {nom} : retire")
            continue
        chemin.write_bytes(texte.encode("utf-8"))
        chemin.chmod(0o755)
        print(f"  {nom} : {'bloc retire' if retirer else 'pose'} ({chemin})")
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
                    and not (i and reste[i - 1] == "--profondeur")]
    if commande == "construire":
        try:
            return construire(calme="--calme" in reste)
        except Exception:
            if "--calme" not in reste:
                raise
            import traceback  # noqa: PLC0415 - le chemin d'erreur seul
            SORTIE.mkdir(exist_ok=True)
            (SORTIE / "erreur.txt").write_bytes(traceback.format_exc().encode("utf-8"))
            return 1
    if commande == "verifier":
        return verifier()
    if commande == "installer":
        return installer(retirer="--retirer" in reste)
    if commande == "chemin" and len(positionnels) == 2:
        return chemin(charger(), *positionnels, sans_sens="--sans-sens" in reste)
    if commande == "expliquer" and len(positionnels) == 1:
        return expliquer(charger(), positionnels[0], tout="--tout" in reste, code="--source" in reste)
    if commande == "appelants" and len(positionnels) == 1:
        return appelants(charger(), positionnels[0], _option(reste, "--profondeur", 2))
    if commande == "chercher" and len(positionnels) == 1:
        return chercher(charger(), positionnels[0])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
