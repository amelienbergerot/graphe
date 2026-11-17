"""T-0004, T-0005, T-0006 : la commande `graphe` sur un mini-projet hote temoin.

Les fichiers lus sont ceux que git suit, plus les non suivis non ignores,
chacun au lecteur de son extension ; `graphe.toml` exclut des dossiers.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from conftest import GRID_ZERO, grid_zero

APPELANT = "from outils import aider\n\n\ndef travailler():\n    return aider()\n"
APPELE = "def aider():\n    return 1\n"


def _graphe(hote: Path, *arguments: str, env: dict | None = None) -> subprocess.CompletedProcess:
    # La racine est fixee a l'import : un processus a part, sur l'hote temoin (pas sur Grid Zero, cf. conftest).
    env = {**(env or os.environ), "GRAPHE_RACINE": str(hote)}
    return subprocess.run([sys.executable, "-c", "import sys, graphe; sys.exit(graphe.main(sys.argv[1:]))",
                           *arguments], cwd=hote, env=env, capture_output=True, text=True, encoding="utf-8")


def _hote(tmp_path: Path, fichiers: dict[str, str], suivi: str = "outils.py") -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for rel, texte in fichiers.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(texte, encoding="utf-8")
    subprocess.run(["git", "add", suivi], cwd=tmp_path, check=True)  # le reste n'est pas suivi
    return tmp_path


def _fichiers_lus(hote: Path) -> set[str]:
    donnees = json.loads((hote / "graphe" / "graphe.json").read_bytes())
    return {n["source_file"] for n in donnees["noeuds"]}


def test_un_hote_sans_configuration_se_construit_et_repond(tmp_path: Path):
    hote = _hote(tmp_path, {"outils.py": APPELE, "travail.py": APPELANT})
    r = _graphe(hote, "construire")
    assert r.returncode == 0, r.stderr
    assert _fichiers_lus(hote) == {"outils.py", "travail.py"}
    r = _graphe(hote, "expliquer", "aider")
    assert r.returncode == 0, r.stderr
    assert "travailler" in r.stdout


def test_graphe_toml_exclut_des_dossiers_et_les_fichiers_sans_lecteur_sont_ignores(tmp_path: Path):
    hote = _hote(tmp_path, {
        "outils.py": APPELE, "travail.py": APPELANT,
        "graphe.toml": 'exclure = ["**/tests", "brouillon"]\n',
        "paquet/tests/test_outils.py": APPELANT, "tests/test_travail.py": APPELANT,
        "brouillon/essai.py": APPELANT, "paquet/brouillon/garde.py": APPELE,  # brouillon/ de la racine seulement
        "donnees/mesures.xml": "<mesures/>\n",
        ".gitignore": "ignore.py\n", "ignore.py": APPELANT,
    })
    r = _graphe(hote, "construire")
    assert r.returncode == 0, r.stderr
    assert _fichiers_lus(hote) == {"outils.py", "travail.py", "paquet/brouillon/garde.py"}


# T-0005 : un programme externe (Godot, pour le lecteur GDScript) se cherche dans graphe.toml, puis le PATH.
SCRIPT_GD = "extends Node\n\n\nfunc _ready():\n\tadd_child(Node.new())\n"


def _sans_godot() -> dict:
    """Un PATH reduit a git : Godot n'y est pas, quelle que soit la machine."""
    return {**os.environ, "PATH": str(Path(shutil.which("git")).parent)}


def _moteur(hote: Path) -> int:
    donnees = json.loads((hote / "graphe" / "graphe.json").read_bytes())
    return donnees["couverture"]["godot"].get("moteur", 0)


def test_sans_godot_le_lecteur_gdscript_continue_et_nomme_la_cle(tmp_path: Path):
    hote = _hote(tmp_path, {"godot/main.gd": SCRIPT_GD}, suivi="godot/main.gd")
    r = _graphe(hote, "construire", env=_sans_godot())
    assert r.returncode == 0, r.stderr
    assert "[godot]" in r.stderr and "executable" in r.stderr
    assert _moteur(hote) == 0
    assert not (hote / "graphe" / "extension_api.json").exists()  # rien en cache : la cle servira au prochain coup


def test_avec_la_cle_les_appels_au_moteur_sont_resolus(tmp_path: Path):
    # Un faux Godot : il ecrit une API ou Node a add_child, la ou on le lance.
    # shortcut: un .cmd, Windows seulement (hors perimetre de T-0001) ; un script Python si l'outil sort de Windows.
    api = '{"classes":[{"name":"Node","methods":[{"name":"add_child"}]}],' \
          '"builtin_classes":[],"utility_functions":[],"singletons":[]}'
    hote = _hote(tmp_path, {"godot/main.gd": SCRIPT_GD, "outils/godot.cmd": f"@echo {api}> extension_api.json\n",
                            "graphe.toml": '[godot]\nexecutable = "outils/godot.cmd"\n'}, suivi="godot/main.gd")
    r = _graphe(hote, "construire", env=_sans_godot())
    assert r.returncode == 0, r.stderr
    assert "introuvable" not in r.stderr
    assert _moteur(hote) >= 1


# T-0006 : le graphe est perime si un fichier de l'hote ou de l'outil est plus recent que lui.
OUTIL = Path(__file__).resolve().parents[1] / "src"
RECONSTRUCTION = "reconstruction"


def test_un_graphe_plus_ancien_que_l_outil_se_reconstruit(tmp_path: Path):
    hote = _hote(tmp_path, {"outils.py": APPELE, "travail.py": APPELANT})
    assert _graphe(hote, "construire").returncode == 0
    # L'outil plus recent que le graphe, sans toucher ses fichiers : l'hote et le graphe vieillis.
    for f in ("outils.py", "travail.py"):
        os.utime(hote / f, (0, 0))
    json_ = hote / "graphe" / "graphe.json"
    outil = max(p.stat().st_mtime for p in OUTIL.glob("graphe*.py"))
    os.utime(json_, (outil + 3600, outil + 3600))  # temoin : plus recent que tout, rien a reconstruire
    r = _graphe(hote, "expliquer", "aider")
    assert r.returncode == 0 and RECONSTRUCTION not in r.stderr, r.stderr
    os.utime(json_, (outil - 1, outil - 1))
    r = _graphe(hote, "expliquer", "aider")
    assert r.returncode == 0 and RECONSTRUCTION in r.stderr, r.stderr


def _crochets(hote: Path) -> dict[str, bytes]:
    dossier = hote / ".git" / "hooks"
    return {p.name: p.read_bytes() for p in dossier.glob("post-*") if p.suffix != ".sample"}


def test_installer_pose_les_crochets_et_ignore_la_sortie_une_seule_fois(tmp_path: Path):
    hote = _hote(tmp_path, {"outils.py": APPELE, ".gitignore": ".venv/"})  # sans fin de ligne
    (hote / ".git" / "hooks" / "post-commit").write_bytes(b"#!/bin/sh\necho avant\n")
    avant = _crochets(hote)
    for _ in range(2):
        assert _graphe(hote, "installer").returncode == 0
    crochets = _crochets(hote)
    assert set(crochets) == {"post-commit", "post-merge", "post-checkout", "post-rewrite"}
    for texte in crochets.values():
        assert texte.count(b"graphe construire --calme") == 1 and b"tools/graphe.py" not in texte
    assert crochets["post-commit"].startswith(b"#!/bin/sh\necho avant\n")
    assert (hote / ".gitignore").read_text(encoding="utf-8") == ".venv/\n/graphe/\n"
    assert _graphe(hote, "installer", "--retirer").returncode == 0
    assert _crochets(hote) == avant


def test_installer_reconnait_la_sortie_deja_ignoree(tmp_path: Path):
    hote = _hote(tmp_path, {"outils.py": APPELE, ".gitignore": "# le graphe\ngraphe/*\n"})
    assert _graphe(hote, "installer").returncode == 0
    assert (hote / ".gitignore").read_text(encoding="utf-8") == "# le graphe\ngraphe/*\n"
    # Un crochet passe en CRLF par un editeur : son bloc est reconnu, pas double.
    crochet = hote / ".git" / "hooks" / "post-merge"
    crochet.write_bytes(crochet.read_bytes().replace(b"\n", b"\r\n"))
    assert _graphe(hote, "installer").returncode == 0
    assert crochet.read_bytes().count(b"graphe construire --calme") == 1


# T-0007 : une extension locale, declaree par graphe.toml, contribue comme un lecteur.
EXTENSION = '''
def contribuer(projet):
    noeuds = projet.graphe["noeuds"]
    if "outils_aider" not in noeuds:  # le graphe deja assemble, lecteurs et coeur compris
        return {"noeuds": [], "liens": []}
    noeuds["outils_aider"]["label"] = "abime"  # lecture seule : sans effet sur le graphe
    return {
        "noeuds": [
            {"id": "regle_politesse", "label": "politesse", "sorte": "regle", "source_file": "regles.txt",
             "source_location": "L1", "nom": "politesse"},
            {"id": "outils_aider", "textes": [projet.configuration["salut"]]},  # fusionne dans le noeud du lecteur
        ],
        "liens": [{"source": "regle_politesse", "target": "outils_aider", "relation": "exige",
                   "confidence": "EXTRACTED", "source_file": "regles.txt", "source_location": "L1", "context": ""}],
    }
'''
AVEC_EXTENSION = '[[extensions]]\nchemin = "ext/regles_du_temoin.py"\nsalut = "Bonjour"\n'


def test_une_extension_locale_ajoute_un_noeud_et_enrichit_un_noeud_existant(tmp_path: Path):
    hote = _hote(tmp_path, {"outils.py": APPELE, "travail.py": APPELANT, "ext/regles_du_temoin.py": EXTENSION,
                            "graphe.toml": AVEC_EXTENSION})
    r = _graphe(hote, "construire")
    assert r.returncode == 0, r.stderr
    r = _graphe(hote, "expliquer", "aider")
    assert r.returncode == 0, r.stderr
    assert "aider()" in r.stdout and "abime" not in r.stdout
    assert "affiche : Bonjour" in r.stdout
    assert "exige (1)" in r.stdout and "politesse (regles.txt:1)" in r.stdout
    assert "travailler" in r.stdout  # ce que le lecteur avait lie reste
    r = _graphe(hote, "expliquer", "politesse")
    assert r.returncode == 0 and "[regle]" in r.stdout, r.stdout


def test_une_extension_introuvable_arrete_la_construction_et_se_nomme(tmp_path: Path):
    hote = _hote(tmp_path, {"outils.py": APPELE, "graphe.toml": AVEC_EXTENSION})
    r = _graphe(hote, "construire")
    assert r.returncode != 0
    assert "ext/regles_du_temoin.py" in r.stderr and "Traceback" not in r.stderr
    assert not (hote / "graphe" / "graphe.json").exists()


def test_un_noeud_nouveau_sans_ses_champs_arrete_la_construction(tmp_path: Path):
    hote = _hote(tmp_path, {"outils.py": APPELE, "graphe.toml": AVEC_EXTENSION,
                            "ext/regles_du_temoin.py": 'def contribuer(projet):\n'
                                                '    return {"noeuds": [{"id": "orphelin", "label": "x"}]}\n'})
    r = _graphe(hote, "construire")
    assert r.returncode != 0
    assert "ext/regles_du_temoin.py" in r.stderr and "orphelin" in r.stderr and "nom" in r.stderr


def test_verifier_se_nourrit_des_sites_d_une_extension(tmp_path: Path):
    sites = '[{"verdict": "lu", "fichier": "regles.txt", "ligne": 1, "nom": "a", "texte": "a"},' \
            ' {"fichier": "regles.txt", "ligne": 2, "nom": "b", "texte": "b", "alerte": "regle orpheline"}]'
    hote = _hote(tmp_path, {"outils.py": APPELE, "graphe.toml": AVEC_EXTENSION,
                            "ext/regles_du_temoin.py": f"def contribuer(projet):\n    return {{'sites': {sites}}}\n"})
    r = _graphe(hote, "verifier")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "== ext/regles_du_temoin.py : 1 sites classes {'lu': 1}" in r.stdout
    assert "regles.txt:2 b (regle orpheline)" in r.stdout
    assert _graphe(hote, "construire").returncode == 0
    couverture = json.loads((hote / "graphe" / "graphe.json").read_bytes())["couverture"]
    assert couverture["ext/regles_du_temoin.py"] == {"lu": 1} and "php" not in couverture


# T-0008 : une extension qui contribue avec les lecteurs, avant le coeur, et reprend les liens de lignes.
AIGUILLAGE = 'from outils import aider\n\n\ndef aiguiller(ordre):\n    if ordre == "aide":\n        return aider()\n    return 0\n'
BRANCHE = '''
def contribuer(projet):
    assert projet.graphe["noeuds"] == {}  # comme un lecteur : rien d'assemble encore
    return {
        "noeuds": [{"id": "branche_aide", "label": "aide", "sorte": "commande", "source_file": "aiguillage.py",
                    "source_location": "L5", "nom": "aide"}],
        "reprises": [{"de": "aiguillage_aiguiller", "vers": "branche_aide", "source_file": "aiguillage.py",
                      "lignes": [6, 6]}],
    }
'''


def test_une_extension_avec_les_lecteurs_reprend_les_liens_de_ses_lignes(tmp_path: Path):
    hote = _hote(tmp_path, {"outils.py": APPELE, "aiguillage.py": AIGUILLAGE, "ext/branches.py": BRANCHE,
                            "graphe.toml": '[[extensions]]\nchemin = "ext/branches.py"\navec_les_lecteurs = true\n'})
    r = _graphe(hote, "construire")
    assert r.returncode == 0, r.stderr
    donnees = json.loads((hote / "graphe" / "graphe.json").read_bytes())
    liens = {(e["source"], e["target"]) for e in donnees["liens"]}
    assert ("branche_aide", "outils_aider") in liens
    assert ("aiguillage_aiguiller", "outils_aider") not in liens
    branche = next(n for n in donnees["noeuds"] if n["id"] == "branche_aide")
    assert branche["fin"] == 6  # un corps pour le coeur, qui l'a vu


# T-0008 : les commandes du serveur de Grid Zero, par son extension locale (tools/graphe_grid_zero.py).
CLIENT = 'extends Node\n\n\nfunc envoyer():\n\t_poster({"cmd": "pas"})\n\t_poster({"cmd": "invente"})\n' \
         '\t# _poster({"cmd": "en_commentaire"})\n\n\nfunc _poster(m):\n\tpass\n'
EXTENSION_GRID_ZERO = '[[extensions]]\nchemin = "tools/graphe_grid_zero.py"\navec_les_lecteurs = true\n'


@grid_zero
def test_l_extension_de_grid_zero_relie_les_commandes_et_signale_un_ordre_inconnu(tmp_path: Path):
    from test_graphe import FLOTTE, MOTEUR, SERVEUR
    hote = _hote(tmp_path, {
        "simulation/moteur.py": MOTEUR, "simulation/flotte.py": FLOTTE, "simulation/server.py": SERVEUR,
        "godot/client.gd": CLIENT, "graphe.toml": EXTENSION_GRID_ZERO,
        "tools/graphe_grid_zero.py": (GRID_ZERO / "tools" / "graphe_grid_zero.py").read_text(encoding="utf-8"),
    }, suivi="simulation")
    r = _graphe(hote, "construire", env=_sans_godot())
    assert r.returncode == 0, r.stderr
    donnees = json.loads((hote / "graphe" / "graphe.json").read_bytes())
    liens = {(e["source"], e["target"]): e["relations"] for e in donnees["liens"]}
    s, m, cmd = "simulation_server_", "simulation_moteur_moteur_", "simulation_server_cmd_"
    assert liens[(f"{s}handle_command", f"{cmd}pas")] == ["dispatches"]
    assert "calls" in liens[(f"{cmd}pas", f"{m}pas")]  # la commande porte les appels de sa branche
    assert (f"{s}handle_command", f"{m}pas") not in liens
    # une branche a deux commandes : la premiere la porte, l'autre y mene
    assert "calls" in liens[(f"{cmd}liste", f"{m}fabrique")]
    assert liens[(f"{cmd}relister", f"{cmd}liste")] == ["dispatches"]
    # une commande sans branche a elle a quand meme son noeud
    assert f"{cmd}rien" in {n["id"] for n in donnees["noeuds"]}
    assert liens[("godot_client_envoyer", f"{cmd}pas")] == ["sends"]
    r = _graphe(hote, "verifier", env=_sans_godot())
    assert r.returncode == 1, r.stdout + r.stderr
    assert "godot/client.gd:6 invente (ordre inconnu du serveur)" in r.stdout
    assert "en_commentaire" not in r.stdout


# T-0009 : le motif de l'appel qui affiche un texte vient de l'hote ; `chercher` trouve ses textes.
AFFICHEUR = 'def accueillir():\n    return dire("Bienvenue au port")\n'


def test_un_hote_avec_son_motif_de_texte_affiche_trouve_ses_textes(tmp_path: Path):
    hote = _hote(tmp_path, {"outils.py": AFFICHEUR})
    r = _graphe(hote, "chercher", "bienvenue")
    assert r.returncode == 1, r.stdout  # sans motif, pas de texte affiche
    (hote / "graphe.toml").write_text(r"""texte_affiche = '\bdire\("([^"]*)"'""", encoding="utf-8")
    r = _graphe(hote, "chercher", "bienvenue")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "outils_accueillir" in r.stdout and "affiche « Bienvenue au port »" in r.stdout


def test_un_motif_de_texte_sans_groupe_arrete_la_construction(tmp_path: Path):
    hote = _hote(tmp_path, {"outils.py": AFFICHEUR, "graphe.toml": "texte_affiche = 'dire'\n"})
    r = _graphe(hote, "construire")
    assert r.returncode == 1 and "texte_affiche" in r.stderr and "Traceback" not in r.stderr, r.stderr


# T-0009 : l'etat, les actions, les conseils et le journal de Grid Zero, par son extension apres le coeur.
ETAT = '''from dataclasses import dataclass


@dataclass
class EtatDeJeu:
    raison_du_jour: str = ""


def construire(x) -> EtatDeJeu:
    return EtatDeJeu(raison_du_jour=x)
'''
LECTURE = 'func texte(state: Dictionary) -> String:\n\tif state.get("raison_du_jour"):\n' \
          '\t\t_poster({"action": "liste"})\n\treturn I18n.t("le réglage tient, sans rien")\n\n\n' \
          'func _poster(m):\n\tpass\n'
PHP_ACTIONS = "<?php\nswitch ($action) {\n    case 'liste':\n        break;\n}\n"
GRID_ZERO_TOML = r'''texte_affiche = '\bI18n\.tn?\(\s*"((?:[^"\\]|\\.)*)"'

[communautes]
a_part = { conseil = "conseils", iteration = "journal" }

[[extensions]]
chemin = "tools/graphe_grid_zero.py"
avec_les_lecteurs = true

[[extensions]]
chemin = "tools/graphe_grid_zero.py"
'''


@grid_zero
def test_l_extension_de_grid_zero_relie_l_etat_les_actions_les_conseils_et_le_journal(tmp_path: Path):
    hote = _hote(tmp_path, {
        "simulation/game/etat_de_jeu.py": ETAT, "godot/lecture.gd": LECTURE, "web/api.php": PHP_ACTIONS,
        "scenarios/lecon/scenario.toml": "[[hints]]\ntick = 4\ntext = \"Quand la fréquence dit « le réglage "
                                         "tient … », attendez.\"\n",
        "tickets/T-0998-essai.md": "---\nid: T-0998\ntitle: Essai\n---\n",
        "tickets/T-0999-essai.md": "---\nid: T-0999\ntitle: Essai\n---\n",
        "docs/moonshot/journal.md": "# Journal\n\n## Itération 7 - un essai (T-0998 à T-0999, 2026-11-05)\n",
        "graphe.toml": GRID_ZERO_TOML,
        "tools/graphe_grid_zero.py": (GRID_ZERO / "tools" / "graphe_grid_zero.py").read_text(encoding="utf-8"),
    }, suivi="simulation")
    r = _graphe(hote, "construire", env=_sans_godot())
    assert r.returncode == 0, r.stderr
    donnees = json.loads((hote / "graphe" / "graphe.json").read_bytes())
    liens = {(e["source"], e["target"]): e["relations"] for e in donnees["liens"]}
    f, champ = "simulation_game_etat_de_jeu_", "simulation_game_etat_de_jeu_etatdejeu_raison_du_jour"
    assert "ecrit" in liens[(f"{f}construire", champ)]  # par mot-cle, au constructeur de l'etat
    assert "lit" in liens[("godot_lecture_texte", champ)]  # par sa cle
    assert liens[("godot_lecture_texte", "web_api_action_liste")] == ["sends"]
    assert "cite" in liens[("conseil_lecon_0", "godot_lecture_texte")]
    assert {c for s, c in liens if s == "iteration_7"} == {"ticket_t_0998", "ticket_t_0999"}
    noms, de = donnees["communautes"], {n["id"]: n["communaute"] for n in donnees["noeuds"]}
    assert noms[str(de["iteration_7"])] == "journal" and noms[str(de["conseil_lecon_0"])] == "conseils"
    assert set(donnees["couverture"]) == {"python", "godot", "pendants"}  # pas de serveur : pas de sites
