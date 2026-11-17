Status: ready-for-agent
Type: task
Part of: T-0001
Blocked by: T-0004
Created: 2026-11-17

# T-0007 : Le contrat contribuer(projet) et les extensions locales

## Ce qu'il faut construire

Les lecteurs et les extensions locales partagent une seule interface : `contribuer(projet)` rend une contribution, c'est-à-dire des nœuds, des liens et, s'il y a lieu, des sites de couverture. `projet` donne la racine, les fichiers de l'hôte, la section de configuration de celui qui contribue et le graphe déjà assemblé, en lecture seule. Un nœud rendu avec un id existant fusionne ses attributs dans ce nœud. L'assemblage passe les lecteurs, puis le cœur, puis les extensions locales dans l'ordre où `graphe.toml` les déclare. `verifier` se nourrit des sites de couverture. Le schéma d'un nœud et d'un lien est documenté comme un contrat, et networkx n'en fait pas partie.

## Critères d'acceptation

- [ ] Les lecteurs Python, GDScript et PHP passent par `contribuer`.
- [ ] Un mini-projet témoin avec une extension locale triviale (un nœud ajouté, un attribut fusionné dans un nœud existant) se construit, et `expliquer` montre les deux.
- [ ] Une extension déclarée mais introuvable arrête la construction avec un message qui la nomme.
- [ ] Le schéma est documenté dans ce dépôt.
- [ ] Le test de référence de Grid Zero passe.

## Comments

**2026-11-17, après T-0002.** À l'entrée de l'assemblage (Python + GDScript + PHP, arbre figé), aucun id de nœud n'est rendu deux fois : la règle de fusion ne change rien aujourd'hui. Si le test de référence bouge à cette étape, chercher d'abord un id rendu par deux contributions.
