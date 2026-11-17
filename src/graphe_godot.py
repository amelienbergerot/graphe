"""Le graphe du code, cote client : les scripts GDScript de godot/.

Chaque script .gd (hors godot/tests) devient des noeuds et des liens, que
tools/graphe.py fond avec ceux du Python (tools/graphe_python.py).

    python tools/graphe_godot.py verifier     ce que l'extraction couvre des appels du client

Ce que l'extraction lit, par motifs et non par une grammaire :
- un fichier, ses fonctions (`func`), ses signaux ;
- `const X = preload("res://...")` : X designe ce fichier ;
- une variable typee par X ou faite par `X.new()` : ses appels vont a X ;
- `X.f(...)`, `f(...)`, `self.f(...)` ; une fonction passee en valeur (un
  gestionnaire de signal) ; `call_deferred("f")` ;
- `{"cmd": "..."}` : un ordre au serveur, relie au noeud de sa commande
  (graphe_python.id_de_commande : la branche de handle_command qui la traite).

`verifier` recompte les appels avec un autre lecteur (le tokenize de
Python) et classe chacun : notre code, le moteur (d'apres l'API que Godot
exporte), une fonction anonyme, ambigu ou inconnu. Un appel non relie qui
porte le nom d'une de nos fonctions est un oubli de l'extraction.
"""

from __future__ import annotations

import bisect
import io
import json
import re
import subprocess
import sys
import tempfile
import tokenize
from collections import Counter, defaultdict
from pathlib import Path

from graphe_racine import RACINE

GODOT = RACINE / "godot"
SORTIE = RACINE / "graphe"
GODOT_EXE = GODOT / "Godot_v4.7.2-stable_win64_console.exe"
PREFIXE_COMMANDE = "simulation_server_cmd_"  # graphe_python.id_de_commande

MOTS_CLES = {"if", "elif", "while", "for", "match", "return", "and", "or", "not", "in", "is", "as", "func",
             "await", "var", "const", "signal", "static", "class", "extends", "breakpoint", "pass", "else"}
# Les fonctions du langage, hors de l'API exportee par le moteur.
DU_LANGAGE = {"preload", "load", "assert", "char", "len", "range", "print_debug", "print_stack", "get_stack",
              "inst_to_dict", "dict_to_inst", "is_instance_of", "type_exists", "convert", "Color8", "ord",
              "super", "_init"}
APPELS_PAR_NOM = re.compile(r"""\b(?:call_deferred|callv?|has_method|Callable\(\s*self\s*,)\s*\(?\s*"(\w+)\"""")
ORDRE = re.compile(r'"cmd"\s*:\s*"(\w+)"')


def scripts() -> list[Path]:
    return sorted(p for p in GODOT.rglob("*.gd")
                  if not {"tests", ".godot", "addons"} & set(p.relative_to(GODOT).parts))


def _id(chemin: Path) -> str:
    return re.sub(r"\W", "_", str(chemin.relative_to(RACINE).with_suffix("")).replace("\\", "/")).lower()


def _rel(chemin: Path) -> str:
    return chemin.relative_to(RACINE).as_posix()


def masquer(texte: str) -> tuple[str, list[tuple[int, str]]]:
    """Le texte, chaines et commentaires effaces (les guillemets et les
    retours a la ligne gardes), et chaque chaine : (debut, valeur)."""
    sortie = list(texte)
    chaines = []
    i, n = 0, len(texte)
    while i < n:
        c = texte[i]
        if c == "#":
            j = texte.find("\n", i)
            j = n if j < 0 else j
            sortie[i:j] = " " * (j - i)
            i = j
        elif c in "\"'":
            fin = c * 3 if texte.startswith(c * 3, i) else c
            debut = j = i + len(fin)
            # Une chaine simple du GDScript peut passer a la ligne (lectures.gd).
            while j < n and not texte.startswith(fin, j):
                j += 2 if texte[j] == "\\" else 1
            chaines.append((i, texte[debut:j]))
            for k in range(debut, min(j, n)):
                if sortie[k] != "\n":
                    sortie[k] = " "
            i = j + len(fin)
        else:
            i += 1
    return "".join(sortie), chaines


class Script:
    """Un script lu : ses fonctions, ses alias de preload, ses variables
    typees, ses signaux - et, ligne par ligne, la fonction qui l'englobe."""

    def __init__(self, chemin: Path) -> None:
        self.chemin = chemin
        self.id = _id(chemin)
        self.texte = chemin.read_bytes().decode("utf-8")
        self.masque, self.chaines = masquer(self.texte)
        self.lignes = self.masque.split("\n")
        self.debuts = [0]
        for m in re.finditer("\n", self.masque):
            self.debuts.append(m.end())
        self.fonctions: dict[str, int] = {}
        self.englobante: list[str | None] = [None] * len(self.lignes)
        self.alias: dict[str, str] = {}
        self.types: dict[str, str] = {}
        self.anonymes: set[str] = set()
        self.signaux: dict[str, int] = {}
        self._lire()

    def ligne_de(self, position: int) -> int:
        return bisect.bisect_right(self.debuts, position)

    def chaine_a(self, position: int) -> str | None:
        i = bisect.bisect_left(self.chaines, (position, ""))
        return self.chaines[i][1] if i < len(self.chaines) and self.chaines[i][0] == position else None

    def _lire(self) -> None:
        en_cours, retrait = None, -1
        for numero, ligne in enumerate(self.lignes):
            contenu = ligne.strip()
            decale = len(ligne) - len(ligne.lstrip())
            if en_cours and contenu and decale <= retrait:
                en_cours = None
            m = re.match(r"\s*(?:static\s+)?func\s+([A-Za-z_]\w*)\s*\(", ligne)
            if m:
                en_cours, retrait = m.group(1), decale
                self.fonctions[en_cours] = numero + 1
                for nom, type_ in re.findall(r"(\w+)\s*:\s*([A-Za-z_]\w*)", ligne[m.end():]):
                    self.types[nom] = type_
            self.englobante[numero] = en_cours
            m = re.match(r"\s*signal\s+(\w+)", ligne)
            if m:
                self.signaux[m.group(1)] = numero + 1
        debut_ligne = 0
        for ligne in self.lignes:
            m = re.match(r"\s*(?:@\w+(?:\([^)]*\))?\s+)*(?:static\s+)?(?:const|var)\s+(\w+)\s*(?::\s*([A-Za-z_]\w*))?"
                         r"[^=\n]*?(?::?=\s*(.*))?$", ligne)
            if m:
                nom, type_, valeur = m.group(1), m.group(2), m.group(3) or ""
                p = re.match(r"(?:pre)?load\(\s*\"", valeur)
                if p:
                    chemin = self.chaine_a(debut_ligne + m.start(3) + p.end() - 1)
                    if chemin and chemin.endswith(".gd"):
                        self.alias[nom] = chemin
                else:
                    n = re.match(r"([A-Za-z_]\w*)\.new\(", valeur)
                    if n:
                        self.types[nom] = n.group(1)
                    elif type_:
                        self.types[nom] = type_
                    if re.match(r"func\s*\(", valeur):
                        self.anonymes.add(nom)
            debut_ligne += len(ligne) + 1
        # Une variable declaree Node, faite plus loin par un de nos scripts :
        # c'est ce script qui recoit ses appels.
        for nom, type_ in re.findall(r"(?<![\w.])(\w+)[ \t]*=[ \t]*([A-Za-z_]\w*)\.new\(", self.masque):
            if type_ in self.alias or nom not in self.types:
                self.types[nom] = type_


class Extraction:
    def __init__(self, api: dict | None = None) -> None:
        self.scripts = {f"res://{s.relative_to(GODOT).as_posix()}": Script(s) for s in scripts()}
        self.par_nom: dict[str, list[Script]] = defaultdict(list)
        for s in self.scripts.values():
            for nom in s.fonctions:
                self.par_nom[nom].append(s)
        self.moteur_methodes, self.moteur_noms = _api_du_moteur(api)
        self.commandes = _commandes_du_serveur()
        self.noeuds: list[dict] = []
        self.liens: list[dict] = []
        self.sites: list[dict] = []
        self.ordres_inconnus: list[tuple[str, int, str]] = []
        for s in self.scripts.values():
            self._noeuds(s)
        for s in self.scripts.values():
            self._appels(s)

    def _noeud(self, s: Script, id_: str, label: str, ligne: int, sorte: str, nom: str) -> None:
        self.noeuds.append({"id": id_, "label": label, "sorte": sorte, "source_file": _rel(s.chemin),
                            "source_location": f"L{ligne}", "nom": nom})

    def _lien(self, s: Script, source: str, cible: str, relation: str, ligne: int, sur: bool = True,
              contexte: str = "") -> None:
        self.liens.append({"source": source, "target": cible, "relation": relation,
                           "confidence": "EXTRACTED" if sur else "INFERRED", "context": contexte,
                           "source_file": _rel(s.chemin), "source_location": f"L{ligne}"})

    def _noeuds(self, s: Script) -> None:
        self._noeud(s, s.id, s.chemin.name, 1, "fichier", _rel(s.chemin))
        for nom, ligne in s.fonctions.items():
            self._noeud(s, f"{s.id}_{nom.lower()}", f"{nom}()", ligne, "fonction", nom)
            self._lien(s, s.id, f"{s.id}_{nom.lower()}", "contains", ligne)
        for nom, ligne in s.signaux.items():
            self._noeud(s, f"{s.id}_signal_{nom.lower()}", f"{nom} (signal)", ligne, "signal", nom)
            self._lien(s, s.id, f"{s.id}_signal_{nom.lower()}", "contains", ligne)
        for alias, chemin in s.alias.items():
            if chemin in self.scripts:
                self._lien(s, s.id, self.scripts[chemin].id, "imports", 1, contexte=alias)

    def _contexte(self, s: Script, ligne: int) -> str:
        nom = s.englobante[ligne - 1]
        return f"{s.id}_{nom.lower()}" if nom else s.id

    def _script_de(self, s: Script, recepteur: str) -> Script | None:
        """Le script que designe un recepteur : un alias, ou une variable
        typee par un alias."""
        porteur = s
        for i, segment in enumerate(recepteur.split(".")):
            if i == 0 and segment in porteur.alias:
                cible = porteur.alias[segment]
            elif porteur.types.get(segment) in porteur.alias:
                cible = porteur.alias[porteur.types[segment]]
            else:
                return None
            porteur = self.scripts.get(cible)
            if porteur is None:
                return None
        return porteur

    def _appels(self, s: Script) -> None:
        for m in re.finditer(r"\b([A-Za-z_]\w*)[ \t]*\(", s.masque):
            nom = m.group(1)
            avant = s.masque[max(0, m.start() - 200):m.start()].rstrip()  # une fenetre : le prefixe entier rendait la lecture quadratique
            if nom in MOTS_CLES or re.search(r"\b(?:func|signal)$", avant):
                continue
            recepteur = ""
            if avant.endswith("."):
                r = re.search(r"([A-Za-z_][\w.]*)\s*\.$", avant)
                recepteur = r.group(1) if r and not avant[:r.start()].rstrip().endswith(".") else "<expr>"
                recepteur = recepteur.removeprefix("self.")
                if recepteur == "self":
                    recepteur = ""
            ligne = s.ligne_de(m.start())
            self.sites.append({"script": s, "ligne": ligne, "nom": nom, "recepteur": recepteur,
                               **self._resoudre(s, nom, recepteur, ligne, m.end())})
        for m in re.finditer(r"(?<![.\w])([A-Za-z_]\w*)(?:\.([A-Za-z_]\w*))?\b(?!\s*\()", s.masque):
            tete, suite = m.group(1), m.group(2)
            ligne = s.ligne_de(m.start())
            avant = s.masque[max(0, m.start() - 20):m.start()].rstrip()
            if re.search(r"\bfunc$", avant):
                continue
            if suite is None and tete in s.fonctions:
                self._lien(s, self._contexte(s, ligne), f"{s.id}_{tete.lower()}", "references", ligne)
            elif suite and tete in s.alias and s.alias[tete] in self.scripts:
                cible = self.scripts[s.alias[tete]]
                if suite in cible.fonctions:
                    self._lien(s, self._contexte(s, ligne), f"{cible.id}_{suite.lower()}", "references", ligne)
        for m in APPELS_PAR_NOM.finditer(s.texte):
            if s.masque[m.start()] == s.texte[m.start()] and m.group(1) in s.fonctions:
                ligne = s.ligne_de(m.start())
                self._lien(s, self._contexte(s, ligne), f"{s.id}_{m.group(1).lower()}", "indirect_call", ligne)
        for m in ORDRE.finditer(s.texte):
            if s.masque[m.start()] != '"':
                continue
            ligne = s.ligne_de(m.start())
            if m.group(1) not in self.commandes:
                self.ordres_inconnus.append((_rel(s.chemin), ligne, m.group(1)))
            self._lien(s, self._contexte(s, ligne), PREFIXE_COMMANDE + m.group(1).lower(), "sends", ligne,
                       contexte=m.group(1))

    def _resoudre(self, s: Script, nom: str, recepteur: str, ligne: int, apres: int) -> dict:
        source = self._contexte(s, ligne)
        if not recepteur:
            if nom in s.fonctions:
                self._lien(s, source, f"{s.id}_{nom.lower()}", "calls", ligne)
                return {"verdict": "notre"}
            if nom in DU_LANGAGE or nom in self.moteur_noms or nom in self.moteur_methodes:
                return {"verdict": "moteur"}
            return {"verdict": "inconnu"}
        cible = self._script_de(s, recepteur)
        if cible is not None:
            if nom in cible.fonctions:
                self._lien(s, source, f"{cible.id}_{nom.lower()}", "calls", ligne)
                return {"verdict": "notre"}
            if nom == "new":
                self._lien(s, source, cible.id, "uses", ligne, contexte="new")
                return {"verdict": "notre"}
            return {"verdict": "moteur" if nom in self.moteur_methodes else "inconnu"}
        derniere = recepteur.split(".")[-1]
        if nom in ("connect", "emit", "disconnect", "is_connected"):
            porteur = s if derniere == recepteur else self._script_de(s, recepteur.rsplit(".", 1)[0])
            if porteur is not None and derniere in porteur.signaux:
                relation = "emits" if nom == "emit" else "connects"
                self._lien(s, source, f"{porteur.id}_signal_{derniere.lower()}", relation, ligne)
                return {"verdict": "notre"}
            return {"verdict": "moteur"}
        if nom == "call" and derniere in s.anonymes:
            return {"verdict": "anonyme"}
        tete = recepteur.split(".")[0]
        if (tete in self.moteur_noms or (recepteur == tete and s.types.get(tete) in self.moteur_noms)) \
                and (nom in self.moteur_methodes or nom not in self.par_nom):
            return {"verdict": "moteur"}
        notres = self.par_nom.get(nom, [])
        if notres and nom not in self.moteur_methodes:
            for autre in notres:
                self._lien(s, source, f"{autre.id}_{nom.lower()}", "calls", ligne, sur=False)
            return {"verdict": "notre?" if len(notres) == 1 else "ambigu"}
        if nom in self.moteur_methodes:
            return {"verdict": "ambigu" if notres else "moteur"}
        return {"verdict": "inconnu"}

    def graphe(self) -> dict:
        ids = {n["id"] for n in self.noeuds}
        return {"nodes": self.noeuds,
                "edges": [e for e in self.liens if e["target"] in ids or e["relation"] == "sends"]}


def _api_du_moteur(api: dict | None) -> tuple[set[str], set[str]]:
    """Les methodes et les noms (classes, fonctions globales) de l'API que
    Godot exporte (--dump-extension-api)."""
    garde = SORTIE / "extension_api.json"
    if api is None and not garde.exists():
        SORTIE.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory() as dossier:
            subprocess.run([str(GODOT_EXE), "--headless", "--dump-extension-api"], cwd=dossier,
                           capture_output=True, timeout=180, check=False)
            garde.write_bytes((Path(dossier) / "extension_api.json").read_bytes())
    if api is None:
        api = json.loads(garde.read_bytes())
    methodes, noms = set(), set()
    for classe in api["classes"] + api["builtin_classes"]:
        noms.add(classe["name"])
        methodes |= {m["name"] for m in classe.get("methods", [])}
        methodes |= {s["name"] for s in classe.get("signals", [])}
    noms |= {f["name"] for f in api["utility_functions"]}
    noms |= {s["name"] for s in api["singletons"]}
    return methodes, noms


def _commandes_du_serveur() -> set[str]:
    texte = (RACINE / "simulation" / "server.py").read_bytes().decode("utf-8")
    bloc = re.search(r"COMMANDES = frozenset\(\{(.*?)\}\)", texte, re.S).group(1)
    return set(re.findall(r'"(\w+)"', bloc))


# ---------- verifier

def _appels_par_tokenize(chemin: Path) -> Counter:
    """Les appels d'un script, lus par un autre lecteur : le tokenize de
    Python (le GDScript lui ressemble assez : chaines, commentaires,
    retraits). Un nom suivi d'une parenthese, hors definition. Une chaine
    simple qui passe a la ligne, que Python refuse, recoit une barre
    oblique de continuation la ou il s'arrete : les numeros de ligne restent."""
    lignes = chemin.read_bytes().decode("utf-8").split("\n")
    while True:
        try:
            jetons = list(tokenize.generate_tokens(io.StringIO("\n".join(lignes)).readline))
            break
        except tokenize.TokenError as e:
            if "unterminated string" not in e.args[0]:
                raise
            lignes[e.args[1][0] - 1] += "\\"
    sites = Counter()
    for i, jeton in enumerate(jetons[:-1]):
        suivant = jetons[i + 1]
        precedent = jetons[i - 1] if i else None
        if jeton.type == tokenize.NAME and suivant.string == "(" and jeton.string not in MOTS_CLES \
                and not (precedent and precedent.string in ("func", "signal")):
            sites[(jeton.start[0], jeton.string)] += 1
    return sites


def verifier() -> int:
    extraction = Extraction()
    lus = Counter((_rel(site["script"].chemin), site["ligne"], site["nom"]) for site in extraction.sites)
    recomptes = Counter()
    for s in extraction.scripts.values():
        for (ligne, nom), n in _appels_par_tokenize(s.chemin).items():
            recomptes[(_rel(s.chemin), ligne, nom)] += n
    manques = recomptes - lus
    en_trop = lus - recomptes
    print(f"{len(extraction.scripts)} scripts, {sum(recomptes.values())} appels recomptes par tokenize, "
          f"{sum(lus.values())} lus par l'extraction")
    print(f"  manques par l'extraction : {sum(manques.values())} ; en trop : {sum(en_trop.values())}")
    for cle in sorted(manques)[:20]:
        print("    manque", *cle)
    for cle in sorted(en_trop)[:20]:
        print("    en trop", *cle)
    verdicts = Counter(site["verdict"] for site in extraction.sites)
    print("  classement :", dict(verdicts.most_common()))
    oublis = [site for site in extraction.sites if site["verdict"] == "inconnu" and site["nom"] in extraction.par_nom]
    ambigus = [site for site in extraction.sites if site["verdict"] == "ambigu"]
    print(f"  appels non relies qui portent le nom d'une de nos fonctions : {len(oublis)} ; "
          f"ambigus (nom chez nous et dans le moteur, recepteur non type) : {len(ambigus)}")
    for site in oublis + ambigus:
        print(f"    {_rel(site['script'].chemin)}:{site['ligne']} {site['recepteur'] or '-'}.{site['nom']} "
              f"({site['verdict']})")
    # Le contre-controle : un appel range au moteur qui porte le nom d'une de
    # nos fonctions sur un recepteur que l'extraction ne sait pas typer.
    douteux = [s for s in extraction.sites if s["verdict"] == "moteur" and s["nom"] in extraction.par_nom
               and s["recepteur"] and extraction._script_de(s["script"], s["recepteur"]) is None]
    print(f"  ranges au moteur, au nom d'une de nos fonctions : {len(douteux)}",
          dict(Counter(f"{s['recepteur']}.{s['nom']}" for s in douteux).most_common(40)))
    devines = [s for s in extraction.sites if s["verdict"] == "notre?"]
    print(f"  relies par le nom seul (recepteur non type, nom unique chez nous) : {len(devines)}")
    for site in devines:
        print(f"    {_rel(site['script'].chemin)}:{site['ligne']} {site['recepteur']}.{site['nom']}")
    inconnus = Counter(f"{site['recepteur'] or '-'}.{site['nom']}" for site in extraction.sites
                       if site["verdict"] == "inconnu" and site["nom"] not in extraction.par_nom)
    print(f"  autres inconnus : {sum(inconnus.values())}", dict(inconnus.most_common(30)))
    print(f"  ordres au serveur : {sum(1 for e in extraction.liens if e['relation'] == 'sends')}, "
          f"inconnus du serveur : {extraction.ordres_inconnus}")
    return 1 if manques or oublis or extraction.ordres_inconnus else 0


if __name__ == "__main__":
    commande = sys.argv[1:2]
    if commande == ["verifier"]:
        sys.exit(verifier())
    print(__doc__)
    sys.exit(2)
