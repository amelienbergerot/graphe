Status: closed
Type: task
Part of: T-0001
Blocked by: T-0004
Created: 2026-11-17

# T-0007 : Le contrat contribuer(projet) et les extensions locales

## Ce qu'il faut construire

Les lecteurs et les extensions locales partagent une seule interface : `contribuer(projet)` rend une contribution, c'est-à-dire des nœuds, des liens et, s'il y a lieu, des sites de couverture. `projet` donne la racine, les fichiers de l'hôte, la section de configuration de celui qui contribue et le graphe déjà assemblé, en lecture seule. Un nœud rendu avec un id existant fusionne ses attributs dans ce nœud. L'assemblage passe les lecteurs, puis le cœur, puis les extensions locales dans l'ordre où `graphe.toml` les déclare. `verifier` se nourrit des sites de couverture. Le schéma d'un nœud et d'un lien est documenté comme un contrat, et networkx n'en fait pas partie.

## Critères d'acceptation

- [x] Les lecteurs Python, GDScript et PHP passent par `contribuer`.
- [x] Un mini-projet témoin avec une extension locale triviale (un nœud ajouté, un attribut fusionné dans un nœud existant) se construit, et `expliquer` montre les deux.
- [x] Une extension déclarée mais introuvable arrête la construction avec un message qui la nomme.
- [x] Le schéma est documenté dans ce dépôt.
- [x] Le test de référence de Grid Zero passe.

## Comments

**2026-11-17, après T-0002.** À l'entrée de l'assemblage (Python + GDScript + PHP, arbre figé), aucun id de nœud n'est rendu deux fois : la règle de fusion ne change rien aujourd'hui. Si le test de référence bouge à cette étape, chercher d'abord un id rendu par deux contributions.

**2026-11-17, fait.**

- Le contrat : chaque lecteur a sa fonction `contribuer(projet)`, qui rend `{"noeuds", "liens", "sites"}`. `graphe.Projet` donne `racine`, `fichiers(suffixe)`, `configuration` (la table `[python]`, `[godot]` ou `[php]` du lecteur, ou la table `[[extensions]]` de l'extension), `graphe` (une copie du graphe assemblé, faite à la première lecture) et `verifier`. Le schéma est dans `docs/contribution.md`.
- L'assemblage (`graphe.assembler`) : les contributions des lecteurs entrent ensemble, nœuds triés par l'id comme avant. C'est ce qui garde l'ordre d'insertion que lit `enrichir`. Viennent ensuite `enrichir`, puis chaque extension de `[[extensions]]` (`chemin = "…"`, relatif à la racine). Un id déjà présent fusionne ses attributs. Il manque un champ obligatoire à un nœud nouveau ou à un lien ? Le message nomme celui qui contribue et l'id. Une extension introuvable, sans `contribuer` ou qui n'est pas un module Python arrête la construction, avec un message sans trace d'appel. Le module de l'extension est inscrit dans `sys.modules`, pour qu'une `dataclass` y marche.
- `verifier` : une seule construction (au lieu de trois lectures), nourrie par les sites. Un site porte `verdict` (compté dans `couverture`) et, en cas de défaut, `alerte`, qui fait échouer `verifier`. Les contrôles des anciens `graphe_python.verifier` et `graphe_godot.verifier` sont devenus des alertes, et ces deux fonctions ont disparu : un appel non relié qui porte un de nos noms, des appels de l'ast non classés, un ordre inconnu du serveur, et les appels que le recomptage par tokenize trouve et que la lecture a manqués. Ce recomptage ne tourne que sous `verifier` (`projet.verifier`) ; un appel en trop reste sans alerte, comme avant. Dans Grid Zero : code 0, mêmes comptes qu'avant.
- Grid Zero : le test de référence passe (« identique à l'instantané »). `couverture` garde ses clés (`python`, `godot`, `pendants`, `ordres_inconnus`), et PHP, sans sites, n'en ajoute pas.
- Tests (`tests/test_hote.py`) : une extension témoin ajoute un nœud et un lien, et fusionne `textes` dans un nœud du lecteur Python. Elle lit sa table de configuration et le graphe assemblé ; le modifier reste sans effet. `expliquer` montre le tout. Trois autres tests : une extension introuvable arrête la construction en se nommant ; un nœud nouveau sans `nom` l'arrête aussi ; `verifier` échoue sur l'alerte d'une extension, et sa couverture entre dans `graphe.json`.
- Limites :
  - Sortent de la sortie de `verifier` trois informations, qui ne faisaient jamais échouer : « rangés au moteur, au nom d'une de nos fonctions » (GDScript), le nombre d'ordres au serveur et les appels en trop.
  - `couverture["ordres_inconnus"]` compte les sites dont l'alerte est `graphe_godot.ORDRE_INCONNU` (`shortcut:`). C'est à reprendre dans T-0008, quand l'ordre inconnu passera dans l'extension de Grid Zero. La couverture de l'extension ajoutera alors une clé à `graphe.json`, sauf si ses sites n'ont pas de `verdict`.
  - Pour T-0008 : le fichier de l'extension est un `.py` de l'hôte, que le lecteur Python lit aussi. Dans l'arbre figé du test de référence, il ajouterait des nœuds, sauf s'il est exclu (`exclure`) ou rangé hors des fichiers lus.
  - Un site sans `texte`, rendu par une extension, fait planter `verifier` (`KeyError`) : le contrat le dit obligatoire, mais rien ne le vérifie.
