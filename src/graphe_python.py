"""Le graphe du code, cote Python : modules, classes, fonctions et appels.

Lu par l'ast de Python. Un appel est relie a sa cible quand son recepteur
a un type connu : une annotation (parametre, variable, attribut, champ de
dataclass, retour), une construction (`x = Classe(...)`, `self.x =
Classe(...)`), une iteration sur un conteneur type, un retour deduit
(`return Classe(...)`). A defaut, un nom porte par une seule de nos
fonctions est relie par le nom seul (INFERRED) ; porte par plusieurs, il
reste non relie et compte comme ambigu.

Les ordres du client (simulation/server.py) : chaque branche
`if cmd == "x":` devient un noeud de commande, qui porte les appels de sa
branche - le client envoie a la commande, pas a tout handle_command.

`graphe verifier` lit le classement de chaque appel dans les sites de sa
contribution (`contribuer`).
"""

from __future__ import annotations

import ast
import builtins
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import graphe_racine
from graphe_racine import RACINE

SERVEUR = "simulation/server.py"
PREFIXE_COMMANDE = "simulation_server_cmd_"
BUILTINS = set(dir(builtins))
# Les methodes des conteneurs que l'on sait typer : ce qu'elles rendent.
VERS_ELEMENT = {"get", "pop", "setdefault", "__getitem__"}
VERS_CONTENEUR = {"values", "copy", "keys"}


def fichiers() -> list[Path]:
    return graphe_racine.fichiers(".py")


def _id(texte: str) -> str:
    return re.sub(r"\W", "_", texte).lower()


def id_de_commande(cmd: str) -> str:
    return PREFIXE_COMMANDE + _id(cmd)


@dataclass(eq=False)
class Fonction:
    id: str
    nom: str
    qualnom: str
    module: Module
    classe: Classe | None
    parent: Fonction | None
    noeud: ast.FunctionDef | ast.AsyncFunctionDef
    locaux: dict[str, list] = field(default_factory=lambda: defaultdict(list))

    @property
    def decorateurs(self) -> set[str]:
        return {d.id if isinstance(d, ast.Name) else d.attr for d in self.noeud.decorator_list
                if isinstance(d, (ast.Name, ast.Attribute))}


@dataclass(eq=False)
class Classe:
    id: str
    nom: str
    qualnom: str
    module: Module
    noeud: ast.ClassDef
    methodes: dict[str, Fonction] = field(default_factory=dict)
    # nom -> [(expression, "annotation" | "valeur", la fonction ou elle est ecrite)]
    attributs: dict[str, list] = field(default_factory=lambda: defaultdict(list))
    # Les champs annotes dans le corps de la classe (une dataclass) : nom -> ligne.
    champs: dict[str, int] = field(default_factory=dict)


@dataclass(eq=False)
class Module:
    id: str
    nom: str
    rel: str
    arbre: ast.Module
    fonctions: dict[str, Fonction] = field(default_factory=dict)
    classes: dict[str, Classe] = field(default_factory=dict)
    imports: dict[str, tuple] = field(default_factory=dict)
    variables: dict[str, list] = field(default_factory=lambda: defaultdict(list))


def _nom_du_module(rel: str) -> str:
    nom = rel.removesuffix(".py").replace("/", ".")
    return nom.removesuffix(".__init__")


class Lecture:
    """Tous nos modules lus, et chaque appel classe."""

    def __init__(self, chemins: list[Path] | None = None, racine: Path = RACINE) -> None:
        self.racine = racine
        self.modules: dict[str, Module] = {}
        for chemin in chemins if chemins is not None else fichiers():
            rel = chemin.relative_to(racine).as_posix()
            arbre = ast.parse(chemin.read_bytes(), filename=rel)
            m = Module(_id(rel.removesuffix(".py")), _nom_du_module(rel), rel, arbre)
            self.modules[m.nom] = m
        self.fonctions: list[Fonction] = []
        self.classes: list[Classe] = []
        for m in self.modules.values():
            self._lire_module(m)
        self.par_nom: dict[str, list[Fonction]] = defaultdict(list)
        for f in self.fonctions:
            self.par_nom[f.nom].append(f)
        self.noms_de_classes = {c.nom for c in self.classes}
        self.commandes = self._commandes()
        self.noeuds: list[dict] = []
        self.liens: list[dict] = []
        self.sites: list[dict] = []
        self._memo: dict = {}
        self._en_cours: set = set()
        self._commandes_vues: set[str] = set()
        self._emettre()

    # ---------- lecture des definitions

    def _lire_module(self, m: Module) -> None:
        for noeud in m.arbre.body:
            self._lire_import(m, noeud)
        for noeud in self._instructions(m.arbre.body):
            if isinstance(noeud, (ast.Assign, ast.AnnAssign)):
                self._noter_affectation(m.variables, noeud, None)
        self._lire_corps(m, m.arbre.body, m.id, "", None, None)

    @staticmethod
    def _entrees_d_import(m: Module, noeud: ast.stmt) -> dict[str, tuple]:
        if isinstance(noeud, ast.Import):
            return {a.asname or a.name.split(".")[0]: ("module", a.name if a.asname else a.name.split(".")[0])
                    for a in noeud.names}
        if isinstance(noeud, ast.ImportFrom):
            base = noeud.module or ""
            if noeud.level:
                paquet = m.nom.split(".") if m.rel.endswith("__init__.py") else m.nom.split(".")[:-1]
                paquet = paquet[:len(paquet) - noeud.level + 1]
                base = ".".join(paquet + ([base] if base else []))
            return {a.asname or a.name: ("symbole", base, a.name) for a in noeud.names}
        return {}

    def _lire_import(self, m: Module, noeud: ast.stmt) -> None:
        if isinstance(noeud, (ast.Import, ast.ImportFrom)):
            m.imports.update(self._entrees_d_import(m, noeud))
        elif isinstance(noeud, (ast.If, ast.Try)):
            for sous in [*noeud.body, *getattr(noeud, "orelse", []), *getattr(noeud, "finalbody", []),
                         *[s for h in getattr(noeud, "handlers", []) for s in h.body]]:
                self._lire_import(m, sous)

    def _lire_corps(self, m: Module, corps: list, parent_id: str, prefixe: str, classe: Classe | None,
                    fonction: Fonction | None) -> None:
        for noeud in self._definitions(corps):
            if isinstance(noeud, ast.ClassDef):
                qual = prefixe + noeud.name
                c = Classe(f"{m.id}_{_id(qual)}", noeud.name, qual, m, noeud)
                self.classes.append(c)
                if fonction is None and classe is None:
                    m.classes[noeud.name] = c
                elif fonction is not None:
                    fonction.locaux[noeud.name].append((c, "classe", fonction, (noeud.lineno, None)))
                elif classe is not None:
                    classe.attributs[noeud.name].append((noeud, "classe", None))
                for sous in noeud.body:
                    if isinstance(sous, (ast.Assign, ast.AnnAssign)):
                        self._noter_affectation(c.attributs, sous, None)
                    if isinstance(sous, ast.AnnAssign) and isinstance(sous.target, ast.Name):
                        c.champs[sous.target.id] = sous.lineno
                self._lire_corps(m, noeud.body, c.id, qual + ".", c, None)
            else:
                qual = prefixe + noeud.name
                f = Fonction(f"{m.id}_{_id(qual)}", noeud.name, qual, m, classe, fonction, noeud)
                self.fonctions.append(f)
                if fonction is not None:
                    fonction.locaux[noeud.name].append((f, "def", fonction, (noeud.lineno, None)))
                if fonction is None:
                    if classe is not None:
                        classe.methodes[noeud.name] = f
                    else:
                        m.fonctions[noeud.name] = f
                self._lire_locaux(f)
                self._lire_corps(m, noeud.body, f.id, qual + ".", None, f)

    @staticmethod
    def _instructions(corps: list):
        """Les instructions d'un corps, y compris sous un if ou un try, sans
        entrer dans les def et class."""
        pile = list(corps)
        while pile:
            noeud = pile.pop(0)
            yield noeud
            if isinstance(noeud, (ast.If, ast.Try, ast.With, ast.For, ast.While)):
                pile[0:0] = [*noeud.body, *getattr(noeud, "orelse", []), *getattr(noeud, "finalbody", []),
                             *[s for h in getattr(noeud, "handlers", []) for s in h.body]]

    @staticmethod
    def _definitions(corps: list):
        """Les def et class d'un corps, y compris sous un if ou un try."""
        pile = list(corps)
        while pile:
            noeud = pile.pop(0)
            if isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                yield noeud
            elif isinstance(noeud, (ast.If, ast.Try, ast.With, ast.For, ast.While)):
                pile[0:0] = [*noeud.body, *getattr(noeud, "orelse", []), *getattr(noeud, "finalbody", []),
                             *[s for h in getattr(noeud, "handlers", []) for s in h.body]]

    @staticmethod
    def _noter_affectation(table: dict, noeud: ast.stmt, fonction: Fonction | None, lieu: tuple = ()) -> None:
        if isinstance(noeud, ast.AnnAssign) and isinstance(noeud.target, ast.Name):
            table[noeud.target.id].append((noeud.annotation, "annotation", fonction, *lieu))
        elif isinstance(noeud, ast.Assign):
            for cible in noeud.targets:
                if isinstance(cible, ast.Name):
                    table[cible.id].append((noeud.value, "valeur", fonction, *lieu))

    def _lire_locaux(self, f: Fonction) -> None:
        # Chaque source d'une variable locale porte son lieu : (ligne, None)
        # pour une affectation, (debut, fin) pour une variable de comprehension.
        a = f.noeud.args
        params = [*a.posonlyargs, *a.args, *a.kwonlyargs]
        debut = (f.noeud.lineno, None)
        for i, p in enumerate(params):
            if p.annotation is not None:
                f.locaux[p.arg].append((p.annotation, "annotation", f, debut))
            elif i == 0 and f.classe is not None and f.parent is None and "staticmethod" not in f.decorateurs:
                f.locaux[p.arg].append(
                    (f.classe, "classe" if "classmethod" in f.decorateurs else "instance", f, debut))
        globaux = {nom for n in self._propres(f.noeud) if isinstance(n, ast.Global) for nom in n.names}
        for noeud in self._propres(f.noeud):
            if isinstance(noeud, (ast.Import, ast.ImportFrom)):
                for local, imp in self._entrees_d_import(f.module, noeud).items():
                    f.locaux[local].append((imp, "import", f, (noeud.lineno, None)))
                    if local in globaux:  # le chargement differe de server.py
                        f.module.imports[local] = imp
            elif isinstance(noeud, (ast.Assign, ast.AnnAssign)):
                lieu = (noeud.lineno, None)
                self._noter_affectation(f.locaux, noeud, f, (lieu,))
                cibles = noeud.targets if isinstance(noeud, ast.Assign) else [noeud.target]
                for cible in cibles:
                    if isinstance(cible, ast.Tuple):
                        for i, el in enumerate(cible.elts):
                            if isinstance(el, ast.Name):
                                f.locaux[el.id].append(((noeud.value, i), "deballe", f, lieu))
                    self._noter_attribut(f, cible, noeud)
            elif isinstance(noeud, (ast.For, ast.AsyncFor)):
                self._noter_iteration(f, noeud.target, noeud.iter, (noeud.lineno, None))
            elif isinstance(noeud, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
                for g in noeud.generators:
                    self._noter_iteration(f, g.target, g.iter, (noeud.lineno, noeud.end_lineno))
            elif isinstance(noeud, (ast.With, ast.AsyncWith)):
                for item in noeud.items:
                    if isinstance(item.optional_vars, ast.Name):
                        f.locaux[item.optional_vars.id].append(
                            (item.context_expr, "valeur", f, (noeud.lineno, None)))
            elif isinstance(noeud, ast.NamedExpr):
                f.locaux[noeud.target.id].append((noeud.value, "valeur", f, (noeud.lineno, None)))

    def _noter_attribut(self, f: Fonction, cible: ast.expr, noeud: ast.stmt) -> None:
        """`self.x = ...` ou `self.x: T = ...` dans une methode : un attribut
        de la classe."""
        if not (isinstance(cible, ast.Attribute) and isinstance(cible.value, ast.Name)):
            return
        methode = f
        while methode.parent is not None:
            methode = methode.parent
        if methode.classe is None:
            return
        premier = (methode.noeud.args.posonlyargs + methode.noeud.args.args)[:1]
        if not premier or premier[0].arg != cible.value.id:
            return
        if isinstance(noeud, ast.AnnAssign):
            methode.classe.attributs[cible.attr].append((noeud.annotation, "annotation", f))
        else:
            methode.classe.attributs[cible.attr].append((noeud.value, "valeur", f))

    @staticmethod
    def _noter_iteration(f: Fonction, cible: ast.expr, iterable: ast.expr, lieu: tuple) -> None:
        if isinstance(cible, ast.Name):
            f.locaux[cible.id].append((iterable, "element", f, lieu))
        elif isinstance(cible, ast.Tuple):
            for i, el in enumerate(cible.elts):
                if isinstance(el, ast.Name):
                    f.locaux[el.id].append(((iterable, i), "element_deballe", f, lieu))

    @staticmethod
    def _propres(noeud: ast.AST):
        """Les noeuds d'une fonction, sans ceux de ses fonctions et classes
        imbriquees (les lambdas en font partie)."""
        pile = list(ast.iter_child_nodes(noeud))
        while pile:
            n = pile.pop()
            yield n
            if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                pile.extend(ast.iter_child_nodes(n))

    def _commandes(self) -> set[str]:
        m = self.modules.get(_nom_du_module(SERVEUR))
        if m is None:
            return set()
        for noeud in m.arbre.body:
            if isinstance(noeud, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "COMMANDES"
                                                     for t in noeud.targets):
                return {c.value for c in ast.walk(noeud.value) if isinstance(c, ast.Constant)
                        and isinstance(c.value, str)}
        return set()

    # ---------- les types

    def _module(self, nom: str) -> Module | None:
        if nom in self.modules:
            return self.modules[nom]
        return self.modules.get(f"tools.{nom}")  # les outils s'importent entre eux depuis tools/

    def _du_module(self, m: Module, nom: str):
        if nom in m.fonctions:
            return ("fonction", m.fonctions[nom])
        if nom in m.classes:
            return ("classe", m.classes[nom])
        if nom in m.imports:
            return self._import(m, m.imports[nom], nom)
        if nom in m.variables:
            return self._des_sources(m.variables[nom], None, m)
        if nom in BUILTINS:
            return ("externe", nom)
        return None

    def _import(self, m: Module, imp: tuple, nom: str):
        if imp[0] == "module":
            cible = self._module(imp[1])
            return ("module", cible) if cible else ("externe", imp[1])
        cible = self._module(imp[1])
        if cible is None:
            sous = self._module(f"{imp[1]}.{imp[2]}")
            return ("module", sous) if sous else ("externe", f"{imp[1]}.{imp[2]}")
        sous = self._module(f"{imp[1]}.{imp[2]}")
        if sous is not None and imp[2] not in cible.fonctions and imp[2] not in cible.classes:
            return ("module", sous)
        return self._garde(("import", imp), lambda: self._du_module(cible, imp[2]))

    def _garde(self, cle, calcul):
        if cle in self._memo:
            return self._memo[cle]
        if cle in self._en_cours:
            return None
        self._en_cours.add(cle)
        try:
            resultat = calcul()
        finally:
            self._en_cours.discard(cle)
        self._memo[cle] = resultat
        return resultat

    @staticmethod
    def _au_lieu(sources: list, ligne: int | None) -> list:
        """Les sources d'une variable vues de la ligne ou elle sert : celle de
        la comprehension qui l'englobe, puis les affectations qui precedent,
        la plus proche d'abord, puis les suivantes (une boucle)."""
        if ligne is None:
            return [s for s in sources if len(s) <= 3 or s[3][1] is None]
        dedans = [s for s in sources if len(s) > 3 and s[3][1] is not None and s[3][0] <= ligne <= s[3][1]]
        avant = sorted((s for s in sources if len(s) > 3 and s[3][1] is None and s[3][0] <= ligne),
                       key=lambda s: -s[3][0])
        apres = [s for s in sources if len(s) > 3 and s[3][1] is None and s[3][0] > ligne]
        return dedans[::-1] + avant + apres + [s for s in sources if len(s) <= 3]

    def _des_sources(self, sources: list, f: Fonction | None, m: Module):
        for source, sorte, ou, *_ in sources:
            portee = ou if ou is not None else f
            t = self._source(source, sorte, portee, m)
            if t is not None:
                return t
        return None

    def _source(self, source, sorte: str, f: Fonction | None, m: Module):
        if sorte == "annotation":
            return self._annotation(source, f, m)
        if sorte in ("instance", "classe"):
            return (sorte, source)
        if sorte == "def":
            return ("fonction", source)
        if sorte == "import":
            return self._import(m, source, "")
        if sorte == "valeur":
            return self.type_de(source, f, m)
        if sorte == "element":
            return self._element(self.type_de(source, f, m))
        if sorte == "element_deballe":
            iterable, i = source
            t = self.type_de(iterable, f, m)
            if t and t[0] == "externe":
                return t
            if t and t[0] == "paires":
                return t[1][i] if i < len(t[1]) else None
            if t and t[0] == "conteneur" and t[2]:
                return t[2][i] if i < len(t[2]) else None
            return None
        if sorte == "deballe":
            valeur, i = source
            t = self.type_de(valeur, f, m)
            if t and t[0] == "externe":
                return t
            if t and t[0] == "conteneur" and t[2]:
                return t[2][i] if i < len(t[2]) else None
            return None
        return None

    @staticmethod
    def _element(t):
        if t and t[0] == "conteneur":
            return t[1]
        if t and t[0] == "paires":
            return ("conteneur", None, list(t[1]))
        if t and t[0] == "externe":
            return ("externe", "element")  # ce qui sort d'un objet hors du depot n'est pas a nous
        return None

    def _annotation(self, a, f: Fonction | None, m: Module):
        """Le type que designe une annotation, en instance."""
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            try:
                a = ast.parse(a.value, mode="eval").body
            except SyntaxError:
                return None
        if isinstance(a, ast.BinOp) and isinstance(a.op, ast.BitOr):
            return self._annotation(a.left, f, m) or self._annotation(a.right, f, m)
        if isinstance(a, ast.Subscript):
            tete = self._nom_final(a.value)
            args = a.slice.elts if isinstance(a.slice, ast.Tuple) else [a.slice]
            if tete in ("Optional", "ClassVar", "Final", "Annotated"):
                return self._annotation(args[0], f, m)
            if tete == "Union":
                return next((t for t in (self._annotation(x, f, m) for x in args) if t), None)
            if tete in ("list", "List", "set", "Set", "frozenset", "Sequence", "Iterable", "Iterator", "deque",
                        "Generator", "Collection", "MutableSequence"):
                return ("conteneur", self._annotation(args[0], f, m), None)
            if tete in ("dict", "Dict", "Mapping", "MutableMapping", "defaultdict", "OrderedDict") and len(args) == 2:
                return ("dict", self._annotation(args[0], f, m), self._annotation(args[1], f, m))
            if tete in ("tuple", "Tuple"):
                return ("conteneur", None, [self._annotation(x, f, m) for x in args])
            if tete in ("type", "Type"):
                t = self._annotation(args[0], f, m)
                return ("classe", t[1]) if t and t[0] == "instance" else None
            return self._annotation(a.value, f, m)
        if isinstance(a, (ast.Name, ast.Attribute)):
            t = self.type_de(a, f, m)
            if t and t[0] == "classe":
                return ("instance", t[1])
            return ("externe", self._nom_final(a)) if t is None or t[0] == "externe" else None
        return None

    @staticmethod
    def _nom_final(e: ast.expr) -> str:
        if isinstance(e, ast.Name):
            return e.id
        if isinstance(e, ast.Attribute):
            return e.attr
        return ""

    def _nom_local(self, nom: str, f: Fonction | None, m: Module, ligne: int | None = None):
        portee = f
        while portee is not None:
            if nom in portee.locaux:
                ici = ligne if portee is f else None
                sources = self._au_lieu(portee.locaux[nom], ici)
                if sources:
                    return self._garde(("local", portee.id, nom, ici),
                                       lambda p=portee, s=sources: self._des_sources(s, p, m))
            portee = portee.parent
        return self._du_module(m, nom)

    def type_de(self, e: ast.expr, f: Fonction | None, m: Module):
        """Ce que vaut une expression : ("module" | "classe" | "instance" |
        "fonction", objet), un conteneur, ("externe", nom), ou None."""
        if isinstance(e, ast.Name):
            return self._nom_local(e.id, f, m, e.lineno)
        if isinstance(e, ast.Attribute):
            if isinstance(e.value, ast.Call) and isinstance(e.value.func, ast.Name) and e.value.func.id == "super":
                classe = self._classe_englobante(f)
                return self._de_classe(classe, e.attr, sauter=True) if classe else None
            return self.attribut(self.type_de(e.value, f, m), e.attr)
        if isinstance(e, ast.Call):
            return self._resultat(e, f, m)
        if isinstance(e, ast.Subscript):
            t = self.type_de(e.value, f, m)
            if t and t[0] == "externe":
                return ("externe", "element")
            if t and t[0] == "dict":
                return t[2]
            if t and t[0] == "conteneur":
                if t[2] and isinstance(e.slice, ast.Constant) and isinstance(e.slice.value, int):
                    return t[2][e.slice.value] if e.slice.value < len(t[2]) else None
                return t[1]
            return None
        if isinstance(e, (ast.List, ast.Set)):
            types = [self.type_de(x, f, m) for x in e.elts if not isinstance(x, ast.Starred)]
            return ("conteneur", next((t for t in types if t), None), None)
        if isinstance(e, ast.Tuple):
            return ("conteneur", None, [self.type_de(x, f, m) for x in e.elts])
        if isinstance(e, ast.Dict):
            valeurs = [self.type_de(v, f, m) for v in e.values if v is not None]
            return ("dict", None, next((t for t in valeurs if t), None))
        if isinstance(e, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            return ("conteneur", self.type_de(e.elt, f, m), None)
        if isinstance(e, ast.DictComp):
            return ("dict", None, self.type_de(e.value, f, m))
        if isinstance(e, ast.IfExp):
            return self.type_de(e.body, f, m) or self.type_de(e.orelse, f, m)
        if isinstance(e, ast.BoolOp):
            return next((t for t in (self.type_de(v, f, m) for v in e.values) if t and t[0] != "externe"), None)
        if isinstance(e, ast.NamedExpr):
            return self.type_de(e.value, f, m)
        if isinstance(e, ast.Await):
            return self.type_de(e.value, f, m)
        if isinstance(e, (ast.Constant, ast.JoinedStr, ast.BinOp, ast.Compare, ast.UnaryOp)):
            return ("externe", type(e).__name__)
        return None

    @staticmethod
    def _classe_englobante(f: Fonction | None) -> Classe | None:
        while f is not None and f.parent is not None:
            f = f.parent
        return f.classe if f else None

    def _mro(self, c: Classe, vus: set | None = None) -> list:
        """La classe et ses bases (les notres) ; une base hors du depot est
        rendue comme ("externe", nom)."""
        vus = vus if vus is not None else set()
        if c.id in vus:
            return []
        vus.add(c.id)
        ordre = [c]
        for base in c.noeud.bases:
            t = self.type_de(base, None, c.module)
            if t and t[0] == "classe":
                ordre += self._mro(t[1], vus)
            else:
                ordre.append(("externe", self._nom_final(base)))
        return ordre

    def _de_classe(self, c: Classe, nom: str, instance: bool = True, sauter: bool = False):
        externe = False
        for porteur in self._mro(c)[1 if sauter else 0:]:
            if isinstance(porteur, tuple):
                externe = True
                continue
            if nom in porteur.methodes:
                methode = porteur.methodes[nom]
                if "property" in methode.decorateurs or "cached_property" in methode.decorateurs:
                    return self._retour(methode) if instance else ("fonction", methode)
                return ("fonction", methode)
            if nom in porteur.attributs:
                sources = porteur.attributs[nom]
                if sources and sources[0][1] == "classe":
                    imbriquee = next((k for k in self.classes if k.noeud is sources[0][0]), None)
                    return ("classe", imbriquee) if imbriquee else None
                t = self._garde(("attribut", porteur.id, nom),
                                lambda p=porteur: self._des_sources(p.attributs[nom], None, p.module))
                return t if t is not None else ("attribut", porteur, nom)
        if externe or nom.startswith("__"):
            return ("externe", nom)
        return ("absent", c, nom)

    def attribut(self, t, nom: str):
        if t is None:
            return None
        sorte = t[0]
        if sorte == "module":
            return self._du_module(t[1], nom) or ("absent", t[1], nom)
        if sorte in ("instance", "classe"):
            return self._de_classe(t[1], nom, instance=sorte == "instance")
        if sorte == "dict":
            if nom in VERS_ELEMENT:
                return ("rend", t[2])
            if nom == "values":
                return ("rend", ("conteneur", t[2], None))
            if nom == "items":
                return ("rend", ("paires", (t[1], t[2])))
            return ("externe", nom)
        if sorte == "conteneur":
            if nom in VERS_ELEMENT:
                return ("rend", t[1])
            if nom in VERS_CONTENEUR:
                return ("rend", t)
            return ("externe", nom)
        if sorte in ("externe", "paires"):
            return ("externe", nom)
        return None

    def _retour(self, f: Fonction):
        def calcul():
            if f.noeud.returns is not None:
                return self._annotation(f.noeud.returns, f, f.module)
            for n in self._propres(f.noeud):
                if isinstance(n, ast.Return) and n.value is not None:
                    t = self.type_de(n.value, f, f.module)
                    if t is not None:
                        return t
            return None
        return self._garde(("retour", f.id), calcul)

    def _resultat(self, appel: ast.Call, f: Fonction | None, m: Module):
        if isinstance(appel.func, ast.Name) and appel.func.id == "super":
            return None
        cible = self.type_de(appel.func, f, m)
        if cible is None:
            return None
        if cible[0] == "classe":
            return ("instance", cible[1])
        if cible[0] == "fonction":
            if cible[1].nom == "__new__" or cible[1].nom == "__init__":
                return None
            return self._retour(cible[1])
        if cible[0] == "rend":
            return cible[1]
        if cible[0] == "externe":
            if cible[1] in ("replace", "deepcopy", "copy") and appel.args:
                return self.type_de(appel.args[0], f, m)
            if cible[1] in ("sorted", "list", "reversed", "tuple", "set", "frozenset") and appel.args:
                t = self.type_de(appel.args[0], f, m)
                return ("conteneur", self._element(t), None) if t and t[0] in ("conteneur", "dict") else t
            if cible[1] in ("enumerate",) and appel.args:
                return ("conteneur", ("conteneur", None, [("externe", "int"), self._element(
                    self.type_de(appel.args[0], f, m))]), None)
            if cible[1] in ("zip",) and appel.args:
                return ("conteneur", ("conteneur", None, [self._element(self.type_de(a, f, m))
                                                          for a in appel.args]), None)
            if cible[1] in ("min", "max", "next") and appel.args:
                return self._element(self.type_de(appel.args[0], f, m))
            if cible[1] in ("cast",) and appel.args:
                return self._annotation(appel.args[0], f, m)
            return ("externe", cible[1])
        return None

    # ---------- le graphe

    def _noeud(self, id_: str, label: str, sorte: str, rel: str, ligne: int, nom: str) -> None:
        self.noeuds.append({"id": id_, "label": label, "sorte": sorte, "source_file": rel,
                            "source_location": f"L{ligne}", "nom": nom})

    def _lien(self, source: str, cible: str, relation: str, rel: str, ligne: int, sur: bool = True,
              contexte: str = "") -> None:
        self.liens.append({"source": source, "target": cible, "relation": relation,
                           "confidence": "EXTRACTED" if sur else "INFERRED", "context": contexte,
                           "source_file": rel, "source_location": f"L{ligne}"})

    def _emettre(self) -> None:
        for m in self.modules.values():
            self._noeud(m.id, Path(m.rel).name, "fichier", m.rel, 1, m.nom)
            for local, imp in m.imports.items():
                cible = self._module(imp[1])
                if imp[0] == "symbole" and self._module(f"{imp[1]}.{imp[2]}") is not None:
                    cible = self._module(f"{imp[1]}.{imp[2]}")
                if cible is not None and cible is not m:
                    self._lien(m.id, cible.id, "imports", m.rel, 1, contexte=local)
                if imp[0] == "symbole" and cible is not None:
                    t = self._import(m, imp, local)
                    if t and t[0] in ("fonction", "classe"):
                        self._lien(m.id, t[1].id, "imports", m.rel, 1, contexte=local)
        for c in self.classes:
            self._noeud(c.id, c.nom, "classe", c.module.rel, c.noeud.lineno, c.qualnom)
            self._lien(c.module.id if "." not in c.qualnom else self._parent_id(c), c.id, "contains",
                       c.module.rel, c.noeud.lineno)
            for base in c.noeud.bases:
                t = self.type_de(base, None, c.module)
                if t and t[0] == "classe":
                    self._lien(c.id, t[1].id, "inherits", c.module.rel, c.noeud.lineno)
            for nom, ligne in c.champs.items():
                self._noeud(self.id_de_champ(c, nom), f"{c.nom}.{nom}", "champ", c.module.rel, ligne,
                            f"{c.qualnom}.{nom}")
                self._lien(c.id, self.id_de_champ(c, nom), "contains", c.module.rel, ligne)
        for f in self.fonctions:
            label = f"{'.' if f.classe else ''}{f.nom}()"
            self._noeud(f.id, label, "methode" if f.classe else "fonction", f.module.rel, f.noeud.lineno, f.qualnom)
            if f.classe is not None:
                self._lien(f.classe.id, f.id, "method", f.module.rel, f.noeud.lineno)
            else:
                self._lien(f.parent.id if f.parent else f.module.id, f.id, "contains", f.module.rel, f.noeud.lineno)
        for m in self.modules.values():
            corps = [n for n in m.arbre.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                                                     ast.ClassDef))]
            self._parcourir(corps, m.id, None, m)
        for c in self.classes:
            corps = [n for n in c.noeud.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                                                     ast.ClassDef))]
            self._parcourir(corps + c.noeud.bases + c.noeud.decorator_list, c.id, None, c.module)
        for f in self.fonctions:
            a = f.noeud.args
            entetes = [*f.noeud.decorator_list, *a.defaults, *[d for d in a.kw_defaults if d is not None]]
            self._parcourir(entetes, f.parent.id if f.parent else (f.classe.id if f.classe else f.module.id),
                            f.parent, f.module)
            self._parcourir(f.noeud.body, f.id, f, f.module)
            for p in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg]:
                if p is not None:
                    self._types(p.annotation, f.id, f, f.module)
            self._types(f.noeud.returns, f.id, f, f.module)
        ids = {n["id"] for n in self.noeuds}
        for cmd in sorted(self.commandes):
            if id_de_commande(cmd) not in ids:
                # Une commande sans branche a elle : traitee par handle_command en bloc.
                hc = f"{_id(SERVEUR.removesuffix('.py'))}_handle_command"
                self._noeud(id_de_commande(cmd), f'"{cmd}" (commande)', "commande", SERVEUR, 1, f"cmd:{cmd}")
                self._lien(hc, id_de_commande(cmd), "dispatches", SERVEUR, 1, contexte=cmd)
                ids.add(id_de_commande(cmd))

    def _parent_id(self, c: Classe) -> str:
        parent = c.qualnom.rsplit(".", 1)[0]
        for autre in self.classes:
            if autre.module is c.module and autre.qualnom == parent:
                return autre.id
        for f in self.fonctions:
            if f.module is c.module and f.qualnom == parent:
                return f.id
        return c.module.id

    def _commandes_du_test(self, test: ast.expr) -> list[str]:
        if not isinstance(test, ast.Compare) or len(test.ops) != 1:
            return []
        droite = test.comparators[0]
        if isinstance(test.ops[0], ast.Eq) and isinstance(droite, ast.Constant):
            valeurs = [droite.value]
        elif isinstance(test.ops[0], ast.In) and isinstance(droite, (ast.Tuple, ast.Set, ast.List)):
            valeurs = [e.value for e in droite.elts if isinstance(e, ast.Constant)]
        else:
            return []
        return [v for v in valeurs if isinstance(v, str) and v in self.commandes]

    def _parcourir(self, noeuds: list, proprietaire: str, f: Fonction | None, m: Module) -> None:
        pile = [(n, proprietaire) for n in reversed(noeuds)]
        appeles = set()
        while pile:
            n, qui = pile.pop()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(n, ast.If) and m.rel == SERVEUR and (cmds := self._commandes_du_test(n.test)):
                for cmd in cmds:
                    cid = id_de_commande(cmd)
                    if cid not in self._commandes_vues:
                        self._commandes_vues.add(cid)
                        self._noeud(cid, f'"{cmd}" (commande)', "commande", m.rel, n.lineno, f"cmd:{cmd}")
                    self._lien(qui, cid, "dispatches", m.rel, n.lineno, contexte=cmd)
                # Une branche a plusieurs commandes : la premiere la porte, les autres y menent.
                corps_de = id_de_commande(cmds[0])
                for autre in cmds[1:]:
                    self._lien(id_de_commande(autre), corps_de, "dispatches", m.rel, n.lineno, contexte="meme branche")
                pile.extend((x, qui) for x in reversed(n.orelse))
                pile.extend((x, corps_de) for x in reversed(n.body))
                pile.append((n.test, qui))
                continue
            if isinstance(n, ast.AnnAssign):
                self._types(n.annotation, qui, f, m)
                pile.extend((x, qui) for x in (n.value, n.target) if x is not None)
                continue
            if isinstance(n, ast.Call):
                appeles.add(id(n.func))
                self._appel(n, qui, f, m)
            elif isinstance(n, (ast.Name, ast.Attribute)) and isinstance(n.ctx, ast.Load) \
                    and id(n) not in appeles:
                if isinstance(n, ast.Attribute):
                    self._propriete(n, qui, f, m)
                    self._champ(n, qui, f, m, "lit")
                self._reference(n, qui, f, m)
            elif isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Store):
                self._champ(n, qui, f, m, "ecrit")
            elif isinstance(n, (ast.Import, ast.ImportFrom)) and f is not None:
                for local, imp in self._entrees_d_import(m, n).items():
                    cible = self._import(m, imp, local)
                    if cible and cible[0] in ("fonction", "classe", "module") and cible[1] is not m:
                        self._lien(qui, cible[1].id, "imports", m.rel, n.lineno, contexte=local)
            pile.extend((x, qui) for x in reversed(list(ast.iter_child_nodes(n))))

    def _reference(self, n: ast.expr, qui: str, f: Fonction | None, m: Module, contexte: str = "") -> None:
        """Une de nos fonctions passee en valeur (un rappel, une cle de tri,
        une tache de pool), ou une de nos classes nommee sans etre appelee
        (isinstance, une annotation : contexte « type »)."""
        t = self.type_de(n, f, m)
        if t and t[0] == "fonction" and t[1].id != qui and "property" not in t[1].decorateurs:
            self._lien(qui, t[1].id, "references", m.rel, n.lineno, contexte=contexte)
        elif t and t[0] == "classe" and t[1].id != qui:
            self._lien(qui, t[1].id, "references", m.rel, n.lineno, contexte=contexte)

    def _propriete(self, n: ast.Attribute, qui: str, f: Fonction | None, m: Module) -> None:
        """Lire une propriete, c'est appeler sa fonction."""
        recepteur = self.type_de(n.value, f, m)
        if not recepteur or recepteur[0] != "instance":
            return
        for porteur in self._mro(recepteur[1]):
            if isinstance(porteur, tuple):
                continue
            methode = porteur.methodes.get(n.attr)
            if methode is not None:
                if {"property", "cached_property"} & methode.decorateurs and methode.id != qui:
                    self._lien(qui, methode.id, "calls", m.rel, n.lineno, contexte="propriete")
                return

    def id_de_champ(self, c: Classe, nom: str) -> str:
        id_ = f"{c.id}_{_id(nom)}"
        return id_ + "_champ" if nom in c.methodes or nom in self.noms_de_classes else id_

    def _champ(self, n: ast.Attribute, qui: str, f: Fonction | None, m: Module, relation: str) -> None:
        """`etat.demand_mw` : lire ou ecrire le champ d'une de nos classes,
        quand le type du recepteur est connu - le premier porteur dans l'ordre
        des bases."""
        recepteur = self.type_de(n.value, f, m)
        if not recepteur or recepteur[0] != "instance":
            return
        for porteur in self._mro(recepteur[1]):
            if isinstance(porteur, tuple):
                return
            if n.attr in porteur.champs:
                self._lien(qui, self.id_de_champ(porteur, n.attr), relation, m.rel, n.lineno)
                return
            if n.attr in porteur.methodes:
                return

    def _types(self, annotation: ast.expr | None, qui: str, f: Fonction | None, m: Module) -> None:
        """Les classes qu'une annotation nomme, chaines comprises."""
        if annotation is None:
            return
        for n in ast.walk(annotation):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                try:
                    self._types(ast.parse(n.value, mode="eval").body, qui, f, m)
                except SyntaxError:
                    pass
            elif isinstance(n, ast.Name) or (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)):
                if isinstance(n, ast.Name) and any(isinstance(a, ast.Attribute) and a.value is n
                                                   for a in ast.walk(annotation)):
                    continue
                self._reference(n, qui, f, m, contexte="type")

    def _appel(self, appel: ast.Call, qui: str, f: Fonction | None, m: Module) -> None:
        func = appel.func
        nom = self._nom_final(func)
        site = {"rel": m.rel, "ligne": appel.lineno, "nom": nom, "expr": ast.unparse(func)[:80]}
        t = self.type_de(func, f, m)
        if t and t[0] == "fonction":
            self._lien(qui, t[1].id, "calls", m.rel, appel.lineno)
            verdict = "notre"
        elif t and t[0] == "classe":
            self._lien(qui, t[1].id, "uses", m.rel, appel.lineno, contexte="instancie")
            verdict = "notre"
        elif t and t[0] in ("externe", "rend"):
            verdict = "externe"
        elif t and t[0] == "attribut":
            verdict = "attribut"  # un attribut appele : un rappel range dans l'objet
        elif t and t[0] == "absent":
            verdict = "absent"
        else:
            recepteur = None
            if isinstance(func, ast.Attribute):
                recepteur = self.type_de(func.value, f, m)
            if recepteur and recepteur[0] in ("externe", "conteneur", "dict", "paires"):
                verdict = "externe"
            elif not nom:
                verdict = "dynamique"
            elif isinstance(func, ast.Name):
                verdict = "local" if self._est_local(nom, f) else "inconnu"
            else:
                notres = self.par_nom.get(nom, [])
                if len(notres) == 1:
                    self._lien(qui, notres[0].id, "calls", m.rel, appel.lineno, sur=False)
                    verdict = "notre?"
                elif notres:
                    verdict = "ambigu"
                    site["candidats"] = len(notres)
                else:
                    verdict = "externe?"
        site["verdict"] = verdict
        self.sites.append(site)

    @staticmethod
    def _est_local(nom: str, f: Fonction | None) -> bool:
        while f is not None:
            a = f.noeud.args
            if nom in f.locaux or nom in {p.arg for p in [*a.posonlyargs, *a.args, *a.kwonlyargs]} \
                    or (a.vararg and a.vararg.arg == nom) or (a.kwarg and a.kwarg.arg == nom):
                return True
            f = f.parent
        return False


def contribuer(projet) -> dict:
    """La contribution du lecteur Python (docs/contribution.md) : un site par appel, et ses alertes."""
    lecture = Lecture(projet.fichiers(".py"), projet.racine)
    nos_noms = set(lecture.par_nom) | lecture.noms_de_classes
    sites = []
    for s in lecture.sites:
        site = {"verdict": s["verdict"], "fichier": s["rel"], "ligne": s["ligne"], "nom": s["nom"], "texte": s["expr"]}
        if s["verdict"] in ("inconnu", "externe?", "absent") and s["nom"] in nos_noms:
            site["alerte"] = "non relie au nom d'une de nos fonctions"
        sites.append(site)
    if projet.verifier:
        total = sum(1 for m in lecture.modules.values() for n in ast.walk(m.arbre) if isinstance(n, ast.Call))
        if total != len(lecture.sites):
            sites.append({"fichier": "", "ligne": 0, "nom": "", "alerte": "appels de l'ast non classes",
                          "texte": f"{total} appels dans l'ast, {len(lecture.sites)} classes"})
    return {"noeuds": lecture.noeuds, "liens": lecture.liens, "sites": sites}
