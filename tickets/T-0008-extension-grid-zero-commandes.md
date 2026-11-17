Status: closed
Type: task
Part of: T-0001
Blocked by: T-0007
Created: 2026-11-17

# T-0008 : Extension Grid Zero : les commandes du serveur

## Ce qu'il faut construire

Les branches de commande du serveur (lues aujourd'hui dans le lecteur Python), les ordres que le client envoie (lus dans le lecteur GDScript) et la vérification des ordres inconnus du serveur sortent des lecteurs. Ils passent dans l'extension locale de Grid Zero, rangée dans Grid Zero et déclarée dans son `graphe.toml`. L'extension relit le module du serveur elle-même. Les ids des nœuds de commande et les liens `dispatches` et `sends` sont inchangés. C'est l'étape la plus risquée du découpage.

## Critères d'acceptation

- [x] Les lecteurs Python et GDScript ne contiennent plus rien des commandes de Grid Zero.
- [x] `graphe verifier` dans Grid Zero signale toujours un ordre inconnu du serveur. Témoin : un ordre inventé dans un script de test le fait signaler.
- [x] Le test de référence de Grid Zero passe.

## Comments

**2026-11-17, fait.**

- La mesure d'abord : sans les branches dans le lecteur Python, le test de référence perdait 33 nœuds et 217 liens, et gagnait 88 liens et `valeur_erreurs`. Le cœur traite une commande comme un corps : sa fin, ses lignes (les `lit`, `ecrit`, `valeur` de sa branche), et le seuil `VALEUR_CORPS_MAX`. Une extension qui passe après le cœur ne peut que rajouter : elle ne rendait pas ce graphe. L'utilisateur veut le graphe le plus complet et le plus précis.
- Le contrat grandit de deux choses (`docs/contribution.md`, `GLOSSARY.md`) :
  - `avec_les_lecteurs = true`, dans la table `[[extensions]]` : l'extension contribue avec les lecteurs, avant le cœur. Comme eux, elle voit le graphe vide, et ses nœuds entrent triés avec les leurs.
  - les **reprises** (`{"de", "vers", "source_file", "lignes": [début, fin]}`) : les liens qui partent de `de` depuis ces lignes partent de `vers`. Elles s'appliquent dans l'ordre, avant l'assemblage. Une extension après le cœur qui en rend arrête la construction.
- L'extension : `grid_zero/tools/graphe_grid_zero.py`, déclarée dans le `graphe.toml` de Grid Zero. Elle relit `simulation/server.py` par l'`ast`, avec le parcours du lecteur : les nœuds de commande, `dispatches`, « même branche », la commande sans branche menée par `handle_command`, et une reprise par branche (celle du dehors d'abord, pour `scenarios` / `tirer_des_crises`). Côté GDScript, elle relie les `{"cmd": …}` par `graphe_godot.Script` du lecteur (la fonction englobante, les commentaires masqués). Un site par ordre : verdict `connu` ou `inconnu`, alerte « ordre inconnu du serveur ».
- Les lecteurs Python et GDScript ne savent plus rien des commandes. Le cœur ne compte plus `ordres_inconnus` (fin du `shortcut:` de T-0007).
- Test de référence : nœuds, liens et communautés identiques. Seule `couverture` change, comme convenu avec l'utilisateur : `ordres_inconnus: 0` sort, et `tools/graphe_grid_zero.py: {connu: 44}` entre. L'instantané a été repris après ce constat. `graphe_reference.py` copie l'extension dans l'arbre figé et l'exclut de la lecture, parce que l'arbre figé ne l'avait pas. Dans l'arbre de travail, le lecteur Python la lit.
- Témoin : un ordre `ordre_invente` ajouté à `godot/editeur/editeur.gd` fait échouer `graphe verifier` (code 1, `editeur.gd:1550 ordre_invente (ordre inconnu du serveur)`, un lien pendant). Fichier rendu ensuite. Sans lui, `verifier` rend 0.
- Tests : `test_chaque_commande_porte_les_appels_de_sa_branche` quitte `test_graphe.py`. Il devient `test_l_extension_de_grid_zero_relie_les_commandes_et_signale_un_ordre_inconnu` (`test_hote.py`, marqué `grid_zero`, l'extension copiée dans un hôte témoin), avec l'ordre inventé et un ordre en commentaire. Le contrat a son test sans Grid Zero : `test_une_extension_avec_les_lecteurs_reprend_les_liens_de_ses_lignes`.
- Limites :
  - L'extension importe `graphe_godot.Script`, l'intérieur du lecteur GDScript, et non le contrat. T-0011 renommera ce lecteur : l'extension suivra, dans la même étape.
  - Une `def` imbriquée dans une branche y laisserait ses décorateurs (`shortcut:` dans l'extension). Grid Zero n'en a pas.
  - La section « Du client au serveur » de `RAPPORT.md` (`graphe.py`) parle encore de `handle_command` : pour T-0009, qui chasse les noms de Grid Zero dans l'outil.
