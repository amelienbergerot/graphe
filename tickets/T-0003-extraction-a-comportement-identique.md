Status: closed
Type: task
Part of: T-0001
Blocked by: T-0002
Created: 2026-11-17

# T-0003 : Extraction à comportement identique

## Ce qu'il faut construire

Le graphe quitte `grid_zero/tools/` pour devenir un paquet Python dans ce dépôt. Ce paquet fournit la commande `graphe`, installée avec `uv tool install -e`. La racine de l'hôte est le dépôt git courant, et non plus l'emplacement du script. Grid Zero garde un `tools/graphe.py` réduit qui transmet ses arguments à la commande, si bien que ses crochets git, son README et les mémoires continuent de marcher. Les tests du graphe et le fichier des manques partent dans ce dépôt ; le fichier des manques devient le backlog unique de l'outil, et chaque entrée nomme son hôte. Rien n'est encore généralisé : les notions de Grid Zero voyagent telles quelles.

## Critères d'acceptation

- [x] `graphe construire`, lancé dans Grid Zero, fait passer le test de référence de T-0002 (le graphe de l'arbre figé, lu par l'outil extrait, est celui de l'instantané).
- [x] `python tools/graphe.py expliquer X` marche toujours dans Grid Zero, ainsi que les crochets posés par `installer`.
- [x] Les tests du graphe passent dans ce dépôt, sans modification de leurs assertions.
- [x] Le fichier des manques vit dans ce dépôt et chaque entrée ouverte nomme son hôte. La mémoire « Noter les manques du graphe » pointe vers lui.
- [x] Le premier commit de ce dépôt cite le commit de Grid Zero d'où vient le code.

## Comments

**2026-11-17, après T-0002.** Le test de référence vit dans Grid Zero (`tools/graphe_reference.py`, `GRAPHE_RACINE`) ; après l'extraction, il lance la commande `graphe` dans l'arbre figé (racine = répertoire courant) au lieu de `tools/graphe.py`. Déclarer scipy dans les dépendances.

**2026-11-17, fait (Grid Zero : son ticket T-0382).**

- Le code vient du commit 23072de de Grid Zero : `src/` garde ses cinq modules à plat (`graphe`, `graphe_python`, `graphe_godot`, `graphe_php`, `graphe_enrichir`), plus `graphe_racine`, seul calcul de la racine : `GRAPHE_RACINE`, sinon `git rev-parse --show-toplevel` depuis le répertoire courant, sinon ce répertoire. `GRAPHE_RACINE` reste pour l'arbre figé, qui n'est pas un dépôt git.
- Installation : `uv tool install -e <graphe> --python 3.14`. networkx, numpy et scipy sont figés aux versions de Grid Zero : la partition de Louvain et les positions de l'instantané en dépendent. Python 3.14 seulement (pas de scipy pour 3.15).
- `graphe_reference.py comparer` : identique à l'instantané, avec l'ancien outil comme avec l'outil extrait.
- Tests : ceux des lecteurs sont ici (`tests/test_graphe.py`, seuls les imports ont changé). Deux tests lisent le vrai Grid Zero, à côté de ce dépôt (`conftest.py`, sautés s'il manque). La couverture de Grid Zero (`graphe verifier`) et le test de référence restent dans Grid Zero.
- Le relais `tools/graphe.py` de Grid Zero pose `GRAPHE_RACINE` sur son dépôt, s'il n'est pas déjà posé, et transmet le code de sortie. Les crochets ont été posés, le post-commit lancé à la main (graphe reconstruit, pas d'`erreur.txt`), puis retirés : il n'y en avait pas avant.
- Pour T-0006 : un changement de l'outil ne périme plus le graphe de Grid Zero, puisque le graphe ne lit plus l'outil dans `tools/`. Et `installer` écrit toujours un crochet qui lance `tools/graphe.py` : juste pour Grid Zero, faux pour un autre hôte.
- `test_le_depot_est_couvert` est resté dans Grid Zero (la couverture est un test de l'hôte, T-0001) : il lance `graphe verifier` et attend 0, au lieu d'appeler `graphe.verifier()`.
