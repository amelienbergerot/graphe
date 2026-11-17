"""Le coeur : ce que le graphe tire du texte des sources, une fois les
lecteurs passes (graphe_manques.md).

Pour chaque fonction, methode, commande ou action :
- `fin` : sa derniere ligne - la premiere ligne non vide qui revient a son
  retrait ferme son corps (Python, GDScript et PHP sont lus de meme) ;
  `expliquer X --source` imprime ses lignes ;
- `textes` : les textes qu'elle affiche, par le motif `texte_affiche` de
  graphe.toml (T-0009) - un texte vu a l'ecran mene a son code ; sans motif,
  aucun ;
- `notes` : le commentaire juste au-dessus d'elle - un concept dit en
  francais (« clarte ») mene a la fonction qui l'a en commentaire.

Et :
- un noeud par variable ou constante de module (Python : une affectation en
  colonne 0 ; GDScript : `const`/`var` en colonne 0, hors `preload`), relie
  aux fonctions qui la lisent (`lit`) ou l'ecrivent (`ecrit`) - dans son
  fichier par le nom, ailleurs par `X.NOM` quand ce nom n'existe qu'une fois ;
- une classe et ses champs ont leur fin et leur commentaire ;
- Python : `alias.CONSTANTE`, ou `alias` est un module importe sous ce nom,
  lit la constante de ce module (EXTRACTED) ;
- un noeud par ticket (tickets/T-*.md) : le code qui le cite (`T-0337` dans
  son corps ou son commentaire) y mene par `cite`, et le ticket mene aux
  fonctions qu'il nomme entre accents graves (`nomme`, par le nom) ;
- un noeud `valeur` par chaine (un identifiant, `"coupee"`) ecrite a la fois
  en Python et en GDScript, relie a chaque corps qui l'ecrit (`valeur`) : ce
  qu'un cote emet et ce que l'autre compare.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import networkx as nx

import graphe_godot
import graphe_racine

CORPS = {"fonction", "methode", "commande", "action", "classe"}
# Une etendue et un commentaire, sans etre un corps qui possede ses lignes.
ETENDUS = CORPS | {"champ"}
PY_ALIAS = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import\s+(\w+)(?:\s+as\s+(\w+))?|import\s+([\w.]+)\s+as\s+(\w+))\s*$")
PY_QUALIFIE = re.compile(r"\b([a-z_]\w*)\.(\w+)\b")
TICKET = re.compile(r"\bT-(\d{4})\b")
NOMME = re.compile(r"`([A-Za-z_][\w.]*?)(?:\(\))?`")
PY_VARIABLE = re.compile(r"^([A-Za-z_]\w*)\s*(?::[^=]+)?=(?!=)")
GD_VARIABLE = re.compile(r"^(?:static\s+)?(const|var)\s+(\w+)\b(.*)$")
PRECHARGE = re.compile(r'^const\s+(\w+)\s*=\s*preload\("res://([^"]+\.gd)"\)', re.M)
QUALIFIE = re.compile(r"\b([A-Z]\w*)\.(\w+)\b")
# Des noms trop courants pour etre suivis d'un fichier a l'autre par le nom.
NOM_MIN = 4
VALEUR = re.compile(r'"([a-z][a-z0-9_]{3,})"')
VALEUR_FICHIERS_MAX = 8
VALEUR_CORPS_MAX = 10


def _retrait(ligne: str) -> int:
    return len(ligne.expandtabs(4)) - len(ligne.expandtabs(4).lstrip())


def _commentaire(ligne: str) -> str | None:
    s = ligne.strip()
    for debut in ("#", "//", "/**", "/*", "*"):
        if s.startswith(debut):
            return s[len(debut):].strip().removesuffix("*/").strip()
    return None


def etendue(lignes: list[str], debut: int) -> int:
    """La derniere ligne (1 = la premiere du fichier) du bloc qui commence a
    `debut` : avant la premiere ligne non vide, hors commentaire, qui revient
    au retrait de `debut` ou en deca. Une fermeture `}` ou `)` a ce retrait
    est du bloc."""
    if debut < 1 or debut > len(lignes):
        return debut
    base = _retrait(lignes[debut - 1])
    fin = debut
    ouvertes = lignes[debut - 1].count("(") - lignes[debut - 1].count(")")
    for i in range(debut, len(lignes)):
        ligne = lignes[i]
        if ouvertes > 0:  # une signature sur plusieurs lignes
            ouvertes += ligne.count("(") - ligne.count(")")
            fin = i + 1
            continue
        s = ligne.strip()
        if not s or _commentaire(ligne) is not None and _retrait(ligne) > base:
            continue
        if _retrait(ligne) <= base:
            if s[0] in "})]" and _retrait(ligne) == base:
                fin = i + 1
            break
        fin = i + 1
    return fin


def notes(lignes: list[str], debut: int) -> str:
    """Le commentaire juste au-dessus de la ligne `debut` (les decorateurs
    sautes), en une ligne."""
    i = debut - 2
    while i >= 0 and lignes[i].strip().startswith("@"):
        i -= 1
    morceaux = []
    while i >= 0:
        texte = _commentaire(lignes[i])
        if texte is None:
            break
        morceaux.append(texte)
        i -= 1
    return " ".join(reversed([m for m in morceaux if m]))


def _variables(rel: str, lignes: list[str]) -> list[tuple[str, int, str]]:
    """(nom, ligne, sorte) des variables et constantes de module."""
    trouvees = []
    if rel.endswith(".py"):
        for i, ligne in enumerate(lignes, start=1):
            m = PY_VARIABLE.match(ligne)
            if m and m.group(1) not in ("__all__",):
                nom = m.group(1)
                trouvees.append((nom, i, "constante" if nom.lstrip("_").isupper() else "variable"))
    elif rel.endswith(".gd"):
        for i, ligne in enumerate(lignes, start=1):
            m = GD_VARIABLE.match(ligne)
            if m and "preload(" not in m.group(3) and "load(" not in m.group(3):
                trouvees.append((m.group(2), i, "constante" if m.group(1) == "const" else "variable"))
    vus = set()
    return [t for t in trouvees if not (t[0] in vus or vus.add(t[0]))]


def _ajouter_lien(graphe: nx.DiGraph, s: str, c: str, relation: str, lieu: str, confiance: str) -> None:
    if graphe.has_edge(s, c):
        d = graphe[s][c]
        d["relations"].add(relation)
        if lieu not in d["lieux"]:
            d["lieux"].append(lieu)
    else:
        graphe.add_edge(s, c, relations={relation}, confiance=confiance, lieux=[lieu], contextes=[])


def motif_des_textes(racine: Path) -> re.Pattern | None:
    """`texte_affiche` (graphe.toml) : le motif d'un appel qui affiche un texte, le texte dans son seul groupe."""
    brut = graphe_racine.configuration(racine).get("texte_affiche")
    if brut is None:
        return None
    try:
        motif = re.compile(brut)
    except (re.error, TypeError) as e:
        raise RuntimeError(f"texte_affiche ({graphe_racine.CONFIGURATION}) : {e}") from None
    if motif.groups != 1:
        raise RuntimeError(f"texte_affiche ({graphe_racine.CONFIGURATION}) : il faut un seul groupe, le texte "
                           f"affiche ; il y en a {motif.groups}")
    return motif


def enrichir(graphe: nx.DiGraph, racine: Path) -> None:
    affiche = motif_des_textes(racine)
    par_fichier: dict[str, list[str]] = defaultdict(list)
    for n, d in graphe.nodes(data=True):
        par_fichier[d["source_file"]].append(n)
    textes_des_fichiers: dict[str, list[str]] = {}
    for rel in par_fichier:
        chemin = racine / rel
        if chemin.is_file():
            textes_des_fichiers[rel] = chemin.read_bytes().decode("utf-8", "replace").splitlines()

    # Les corps : fin, textes, notes.
    corps: dict[str, tuple[str, int, int]] = {}
    for rel, ids in par_fichier.items():
        lignes = textes_des_fichiers.get(rel)
        if lignes is None:
            continue
        for n in ids:
            d = graphe.nodes[n]
            if d["sorte"] not in ETENDUS:
                continue
            debut = int(d["source_location"].lstrip("L") or 0)
            fin = etendue(lignes, debut)
            d["fin"] = fin
            texte = "\n".join(lignes[debut - 1:fin])
            trouves = [t.replace('\\"', '"') for t in affiche.findall(texte)] if affiche else []
            if trouves:
                d["textes"] = trouves
            note = notes(lignes, debut)
            if note:
                d["notes"] = note
            if d["sorte"] in CORPS:
                corps[n] = (rel, debut, fin)

    # Chaque ligne a son proprietaire : le plus petit corps qui la contient -
    # la branche d'une commande plutot que la fonction qui aiguille (ses
    # appels aussi : les reprises d'une extension, T-0008). La ligne de tete n'est
    # pas un usage.
    proprietaires: dict[str, dict[int, str]] = defaultdict(dict)
    for n, (rel, debut, fin) in sorted(corps.items(), key=lambda c: c[1][2] - c[1][1], reverse=True):
        for i in range(debut + 1, fin + 1):
            proprietaires[rel][i] = n

    # Les variables et constantes de module.
    fichier_id = {graphe.nodes[n]["source_file"]: n for n in graphe.nodes if graphe.nodes[n]["sorte"] == "fichier"}
    variables: dict[str, dict[str, str]] = defaultdict(dict)  # fichier -> nom -> id
    noms_de_module: dict[str, list[str]] = defaultdict(list)
    for rel, lignes in textes_des_fichiers.items():
        fid = fichier_id.get(rel)
        if fid is None:
            continue
        for nom, ligne, sorte in _variables(rel, lignes):
            vid = f"{fid}_{nom.lower()}"
            if vid in graphe:
                vid += "_" + sorte
            graphe.add_node(vid, id=vid, label=nom, sorte=sorte, source_file=rel, source_location=f"L{ligne}",
                            nom=nom, fin=etendue(lignes, ligne))
            note = notes(lignes, ligne)
            if note:
                graphe.nodes[vid]["notes"] = note
            _ajouter_lien(graphe, fid, vid, "contains", f"{rel}:{ligne}", "EXTRACTED")
            variables[rel][nom] = vid
            noms_de_module[nom].append(vid)
    uniques = {nom: ids[0] for nom, ids in noms_de_module.items() if len(ids) == 1 and len(nom) >= NOM_MIN}
    ailleurs = re.compile(r"\b\w+\.(" + "|".join(sorted(map(re.escape, uniques), key=len, reverse=True)) + r")\b") \
        if uniques else None
    ecriture = r"\s*(?:[-+*/]?=(?!=)|\.(?:append|extend|clear|pop|update|insert|remove|add|discard|erase)\()"
    usages: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    fichiers_py = {rel for rel in textes_des_fichiers if rel.endswith(".py")}
    for rel, lignes in textes_des_fichiers.items():
        locales = variables.get(rel, {})
        # GDScript : `Script.CONSTANTE`, ou Script precharge un script (res:// : godot/, graphe_godot.GODOT).
        alias = {nom: graphe_godot.res(cible) for nom, cible in PRECHARGE.findall("\n".join(lignes))} \
            if rel.endswith(".gd") else {}
        # Python : `alias.CONSTANTE`, alias un module importe sous ce nom.
        alias_py = _alias_python(lignes, fichiers_py) if rel.endswith(".py") else {}
        ici = re.compile(r"(?<![\w.])(" + "|".join(sorted(map(re.escape, locales), key=len, reverse=True)) + r")\b") \
            if locales else None
        for i, n in proprietaires.get(rel, {}).items():
            ligne = lignes[i - 1]
            if _commentaire(ligne) is not None:
                continue
            lieu = f"{rel}:{i}"
            if ici is not None:
                for m in ici.finditer(ligne):
                    ecrit = re.match(ecriture, ligne[m.end():])
                    _ajouter_lien(graphe, n, locales[m.group(1)], "ecrit" if ecrit else "lit", lieu, "EXTRACTED")
            if alias and "." in ligne:
                for tete, nom in set(QUALIFIE.findall(ligne)):
                    vid = variables.get(alias.get(tete, ""), {}).get(nom)
                    if vid:
                        _ajouter_lien(graphe, n, vid, "lit", lieu, "EXTRACTED")
            elif ailleurs is not None and "." in ligne:
                surs = set()
                for tete, nom in set(PY_QUALIFIE.findall(ligne)) if alias_py else ():
                    vid = variables.get(alias_py.get(tete, ""), {}).get(nom)
                    if vid:
                        _ajouter_lien(graphe, n, vid, "lit", lieu, "EXTRACTED")
                        surs.add(nom)
                for nom in set(ailleurs.findall(ligne)) - surs:
                    vid = uniques[nom]
                    # `examen.graine` en Python ne lit pas une variable GDScript.
                    autre = graphe.nodes[vid]["source_file"]
                    if autre != rel and Path(autre).suffix == Path(rel).suffix:
                        _ajouter_lien(graphe, n, vid, "lit", lieu, "INFERRED")
            # T-0354 : les valeurs ecrites dans un langage et lues dans l'autre.
            if '"' in ligne and rel.endswith((".py", ".gd")):
                for v in set(VALEUR.findall(ligne)):
                    usages[v].append((n, lieu, Path(rel).suffix))

    _relier_les_valeurs(graphe, usages)
    _relier_les_tickets(graphe, racine, corps, textes_des_fichiers)


def _relier_les_valeurs(graphe: nx.DiGraph, usages: dict[str, list[tuple[str, str, str]]]) -> None:
    """T-0354 : une valeur ecrite en Python et en GDScript devient un noeud ;
    son nom garde ses guillemets, pour ne pas rendre ambigu le nom d'une
    fonction qui s'ecrit de meme. Une valeur ecrite dans plus de
    VALEUR_FICHIERS_MAX fichiers (`"name"`, `"tick"`) ne dit rien et
    raccourcissait un chemin non oriente sur trois : pas de noeud."""
    for v, us in sorted(usages.items()):
        if {s for _, _, s in us} != {".py", ".gd"}:
            continue
        if (len({lieu.rsplit(":", 1)[0] for _, lieu, _ in us}) > VALEUR_FICHIERS_MAX
                or len({n for n, _, _ in us}) > VALEUR_CORPS_MAX):
            continue
        vid = f"valeur_{v}"
        rel, ligne = min(lieu for _, lieu, s in us if s == ".py").rsplit(":", 1)
        graphe.add_node(vid, id=vid, label=f'"{v}"', sorte="valeur", source_file=rel, source_location=f"L{ligne}",
                        nom=f'"{v}"', fin=int(ligne))
        for n, lieu, _ in us:
            _ajouter_lien(graphe, n, vid, "valeur", lieu, "EXTRACTED")


def _alias_python(lignes: list[str], fichiers: set[str]) -> dict[str, str]:
    """Les modules importes sous un nom : nom -> fichier."""
    alias = {}
    for ligne in lignes:
        m = PY_ALIAS.match(ligne)
        if not m:
            continue
        if m.group(1):
            module, nom = f"{m.group(1)}.{m.group(2)}", m.group(3) or m.group(2)
        else:
            module, nom = m.group(4), m.group(5)
        chemin = module.replace(".", "/")
        for rel in (chemin + ".py", chemin + "/__init__.py"):
            if rel in fichiers:
                alias[nom] = rel
    return alias


def _relier_les_tickets(graphe: nx.DiGraph, racine: Path, corps: dict, textes: dict[str, list[str]]) -> None:
    tickets = {}
    for chemin in sorted((racine / "tickets").glob("T-[0-9][0-9][0-9][0-9]*.md")):
        numero = chemin.name[2:6]
        texte = chemin.read_bytes().decode("utf-8", "replace")
        titre = next((ligne.split(":", 1)[1].strip() for ligne in texte.splitlines()[:8]
                      if ligne.startswith("title:")), chemin.stem)
        tid = f"ticket_t_{numero}"
        rel = chemin.relative_to(racine).as_posix()
        graphe.add_node(tid, id=tid, label=f"T-{numero}", sorte="ticket", source_file=rel, source_location="L1",
                        nom=f"T-{numero}", notes=titre, fin=len(texte.splitlines()))
        tickets[numero] = (tid, rel, texte)
    if not tickets:
        return
    # Le code qui cite un ticket, dans son corps ou son commentaire.
    for n, (rel, debut, fin) in corps.items():
        lignes = textes.get(rel, [])
        cites = set(TICKET.findall("\n".join(lignes[debut - 1:fin]))) | set(
            TICKET.findall(graphe.nodes[n].get("notes", "")))
        for numero in sorted(cites):
            if numero in tickets:
                _ajouter_lien(graphe, n, tickets[numero][0], "cite", f"{rel}:{debut}", "EXTRACTED")
    # Les fonctions qu'un ticket nomme : un nom porte par un seul corps.
    porteurs: dict[str, list[str]] = defaultdict(list)
    for n in corps:
        d = graphe.nodes[n]
        if d["sorte"] in ("fonction", "methode", "classe"):
            porteurs[d["nom"].rsplit(".", 1)[-1]].append(n)
    for tid, rel, texte in tickets.values():
        for nom in set(NOMME.findall(texte)):
            dernier = nom.rsplit(".", 1)[-1]
            if len(dernier) >= NOM_MIN and len(porteurs.get(dernier, [])) == 1:
                _ajouter_lien(graphe, tid, porteurs[dernier][0], "nomme", rel, "INFERRED")


def lignes_sans_commentaires(lignes: list[str]) -> list[str]:
    return [ligne for ligne in lignes if _commentaire(ligne) is None]
