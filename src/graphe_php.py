"""Le PHP de l'hote dans le graphe du code.

Un lecteur sommaire, par motifs, comme celui du GDScript :
- un noeud par fichier, un par fonction (`function lire(`) ;
- dans un point d'entree a actions (`switch ($action)`), un noeud par
  `case 'x':` - sorte « action » ; deux `case` a la suite partagent un
  corps : le premier mene au second, qui le porte ;
- les appels entre nos fonctions, par leur nom.

Ce qui envoie a ces actions, depuis un autre langage, revient a une
extension locale de l'hote (T-0009).
"""

from __future__ import annotations

import re
from pathlib import Path

from graphe_enrichir import etendue, lignes_sans_commentaires
import graphe_racine
from graphe_racine import RACINE

FONCTION = re.compile(r"^function\s+(\w+)\s*\(")
ACTION = re.compile(r"^\s*case\s+'(\w+)'\s*:\s*$")
APPEL = re.compile(r"\b(\w+)\s*\(")


def fichiers(racine: Path = RACINE) -> list[Path]:
    return graphe_racine.fichiers(".php", racine)


def _id(chemin: Path, racine: Path) -> str:
    return re.sub(r"\W", "_", chemin.relative_to(racine).with_suffix("").as_posix()).lower()


def contribuer(projet) -> dict:
    """La contribution du lecteur PHP (docs/contribution.md) : ni appels classes, ni sites."""
    lecture = Lecture(projet.fichiers(".php"), projet.racine)
    return {"noeuds": lecture.noeuds, "liens": lecture.liens}


def id_d_action(fichier_id: str, action: str) -> str:
    return f"{fichier_id}_action_{action.lower()}"


class Lecture:
    def __init__(self, chemins: list[Path] | None = None, racine: Path = RACINE) -> None:
        self.noeuds: list[dict] = []
        self.liens: list[dict] = []
        definies: dict[str, str] = {}
        corps: list[tuple[str, str, int, list[str]]] = []  # (id, fichier, ligne, lignes du corps)
        for chemin in fichiers(racine) if chemins is None else chemins:
            rel = chemin.relative_to(racine).as_posix()
            fid = _id(chemin, racine)
            lignes = chemin.read_bytes().decode("utf-8", "replace").splitlines()
            self._noeud(fid, chemin.name, "fichier", rel, 1, rel)
            precedente = ""  # une action sans corps, qui mene a la suivante
            for i, ligne in enumerate(lignes, start=1):
                f, a = FONCTION.match(ligne), ACTION.match(ligne)
                if not (f or a):
                    continue
                if f:
                    nid = f"{fid}_{f.group(1).lower()}"
                    definies[f.group(1)] = nid
                    self._noeud(nid, f"{f.group(1)}()", "fonction", rel, i, f.group(1))
                else:
                    nid = id_d_action(fid, a.group(1))
                    self._noeud(nid, a.group(1), "action", rel, i, a.group(1))
                    if precedente:
                        self._lien(precedente, nid, "dispatches", rel, i)
                self._lien(fid, nid, "contains", rel, i)
                fin = etendue(lignes, i)
                precedente = nid if a and fin == i else ""
                corps.append((nid, rel, i, lignes_sans_commentaires(lignes[i:fin])))
        for nid, rel, i, lignes_du_corps in corps:
            vus = set()
            for texte in lignes_du_corps:
                for m in APPEL.finditer(texte):
                    cible = definies.get(m.group(1))
                    if cible and cible != nid and cible not in vus:
                        vus.add(cible)
                        self._lien(nid, cible, "calls", rel, i)

    def _noeud(self, nid: str, label: str, sorte: str, rel: str, ligne: int, nom: str) -> None:
        self.noeuds.append({"id": nid, "label": label, "sorte": sorte, "source_file": rel,
                            "source_location": f"L{ligne}", "nom": nom})

    def _lien(self, source: str, cible: str, relation: str, rel: str, ligne: int) -> None:
        self.liens.append({"source": source, "target": cible, "relation": relation, "confidence": "EXTRACTED",
                           "source_file": rel, "source_location": f"L{ligne}", "context": ""})
