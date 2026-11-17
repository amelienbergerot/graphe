Status: closed
Type: task
Part of: T-0001
Created: 2026-11-17

# T-0002 : Tri des nœuds et des liens, et test de référence, dans Grid Zero

## Ce qu'il faut construire

Dans Grid Zero, avant toute extraction, l'assemblage trie les nœuds et les liens avant de les insérer, pour que les communautés (Louvain, graine fixe) ne dépendent plus de l'ordre des contributions. Un instantané du `graphe.json` de Grid Zero, sans l'horodatage ni le commit, devient le test de référence : un test de Grid Zero compare le graphe construit à l'instantané. C'est le prérequis qui rend toutes les étapes suivantes vérifiables.

Ce ticket se fait dans le dépôt de Grid Zero.

## Critères d'acceptation

- [x] Les nœuds et les liens sont insérés dans un ordre qui ne dépend que de leur contenu.
- [~] On a vérifié une fois, avec le diff noté dans le ticket, que la différence entre le graphe d'avant le tri et celui d'après se limite à la numérotation des communautés.
- [x] L'instantané est committé dans Grid Zero, et un test le compare au graphe construit, sans l'horodatage ni le commit.
- [x] Sabotage : un lien retiré à la main fait échouer le test de référence.
- [x] La suite de Grid Zero passe.

## Comments

**2026-11-17, fait dans Grid Zero (son ticket T-0381, commit 23072de, poussé avec l'étiquette `graphe-reference` → 5337c36).**

- Le graphe de référence est celui d'un **arbre figé** (l'étiquette, par `git archive`), lu par l'outil d'aujourd'hui (`GRAPHE_RACINE`). L'arbre de travail est impossible à figer : le graphe lit `tools/`, donc lui-même. Commandes : `tools/graphe_reference.py comparer|prendre` ; le test est dans `test_graphe.py`.
- Le tri a révélé une autre cause d'ordre : `PYTHONHASHSEED` changeait l'ordre des liens et les positions. Trois graines donnent maintenant le même JSON.
- **Critère 2 non tenu tel qu'écrit** (`[~]`) : nœuds, liens et couverture sont identiques, mais la **partition** des communautés a changé (56 → 57, 2961 nœuds sur 4390 changent de groupe). Louvain dépend de l'ordre de son entrée. L'instantané est pris après le tri ; c'est cette partition qui fait foi. La décision de test de T-0001 est amendée.
- Sabotage : un lien retiré → `liens en moins (1) : [...]`, sur l'assertion.
- Limites pour la suite : l'arbre figé n'est pas un dépôt git et n'a ni `graphe.toml` ni extension (voir les notes de T-0003 et T-0004). La disposition demande scipy (Python 3.14 ; absent du 3.15) : dépendance à déclarer à l'extraction.
