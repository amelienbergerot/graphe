Status: closed
Type: task
Part of: T-0001
Blocked by: T-0005, T-0006, T-0008, T-0009, T-0010
Created: 2026-11-17

# T-0011 : Interface publique en anglais

## Ce qu'il faut construire

Tout ce qu'un utilisateur ou un hôte voit passe en anglais : les commandes, les clés de `graphe.toml`, les champs du JSON, les sortes de nœuds et de relations, les messages, `graphe.html` et le rapport. Grid Zero migre dans la même étape : son `tools/graphe.py`, son extension locale, son `graphe.toml`, son README, ses mémoires qui citent les commandes, et une nouvelle prise de l'instantané de référence avec les noms traduits.

## Critères d'acceptation

- [x] Plus aucun mot français dans l'interface. La commande d'aide le montre.
- [x] Dans Grid Zero, le nouvel instantané ne diffère de l'ancien que par la traduction des noms. Vérification par une table de correspondance appliquée à l'ancien instantané.
- [x] Les mémoires et le README de Grid Zero citent les nouvelles commandes.
- [x] Les tests de ce dépôt et de Grid Zero passent.

## Comments

**2026-11-18, fait.** La table de correspondance, qui sert aussi d'index des nouveaux noms :

| Ce qui change | Avant → après |
|---|---|
| Commandes | `construire` → `build` (`--calme` → `--quiet`), `verifier` → `check`, `chemin` → `path` (`--sans-sens` → `--undirected`), `expliquer` → `explain` (`--tout` → `--all`), `appelants` → `callers` (`--profondeur` → `--depth`), `chercher` → `search`, `installer` → `install` (`--retirer` → `--remove`) |
| Sortie, environnement | `RAPPORT.md` → `REPORT.md`, `erreur.txt` → `error.txt`, `GRAPHE_RACINE` → `GRAPHE_ROOT` |
| `graphe.toml` | `exclure` → `exclude`, `texte_affiche` → `displayed_text`, `[documents] motifs`/`identifiant` → `patterns`/`identifier`, `[communautes] a_part`/`sans_prefixe` → `[communities] separate`/`strip_prefixes`, `[[extensions]] chemin`/`avec_les_lecteurs` → `path`/`with_readers` |
| JSON | `noeuds`/`liens` → `nodes`/`links`, `couverture` → `coverage` (`pendants` → `dangling`), `communautes` → `communities`, `construit`/`construit_s` → `built`/`built_s` ; nœud : `sorte`, `nom`, `fin`, `textes`, `communaute` → `kind`, `name`, `end`, `texts`, `community` ; lien : `confiance`, `lieux`, `contextes` → `confidence`, `locations`, `contexts` |
| Sortes | `fichier`, `fonction`, `methode`, `classe`, `champ`, `constante`, `commande`, `valeur` → `file`, `function`, `method`, `class`, `field`, `constant`, `command`, `value` ; Grid Zero : `conseil` → `hint` |
| Relations | `lit`, `ecrit`, `cite`, `nomme`, `valeur` → `reads`, `writes`, `cites`, `names`, `value` |
| Contextes | `instancie`, `propriete` → `instantiates`, `property` ; Grid Zero : `meme branche` → `same branch` |
| Verdicts | `notre`, `notre?`, `ambigu`, `anonyme`, `moteur`, `externe`, `externe?`, `attribut`, `inconnu`, `dynamique` → `ours`, `ours?`, `ambiguous`, `anonymous`, `engine`, `external`, `external?`, `attribute`, `unknown`, `dynamic` ; Grid Zero : `connu` → `known` |
| Ids | `valeur_` → `value_`, `_constante` et `_champ` (le suffixe d'un id déjà pris) → `_constant` et `_field` ; Grid Zero : `conseil_` → `hint_` |
| Contrat | `contribuer(projet)` → `contribute(project)` ; `projet.racine`, `fichiers()`, `graphe`, `verifier` → `project.root`, `files()`, `graph`, `checking` ; `reprises` (`de`, `vers`, `lignes`) → `takeovers` (`from`, `to`, `lines`) ; site : `fichier`, `ligne`, `texte`, `nom`, `alerte` → `file`, `line`, `text`, `name`, `alert` |

- La vérification : l'ancien instantané de Grid Zero, traduit champ par champ par cette table (étiquettes des conseils, des itérations et des commandes comprises) puis retrié, est identique au nouveau (Grid Zero, T-0388) : 4390 nœuds, 16728 liens, 258 ids renommés. Les communautés et les positions n'ont pas bougé : aucun id renommé ne change d'ordre parmi les nœuds du code.
- Restent en français, pour T-0012 : le code, les docstrings hors aide, `docs/contribution.md` (ses identifiants sont à jour), le glossaire, les ADR, `graphe_manques.md`. Les données de l'hôte (étiquettes, commentaires, textes affichés) restent ce qu'elles sont.
- `install` reconnaît un bloc d'avant (`# >>> graphe du code`) et le remplace en entier.
- L'extension de Grid Zero importe encore `graphe_enrichir` et `graphe_godot` par leur nom : T-0012 devra la suivre si ces modules changent de nom.
