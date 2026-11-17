Status: closed
Type: task
Part of: T-0001
Blocked by: T-0007
Created: 2026-11-17

# T-0009 : Extension Grid Zero : l'état, les actions, les conseils, le journal et les textes

## Ce qu'il faut construire

Sortent du cœur et passent dans l'extension locale de Grid Zero :
- les champs de l'état envoyé au client et les clés que le GDScript en lit ;
- les `"action"` postées par le GDScript vers les actions PHP ;
- les conseils de scénario ;
- le journal moonshot.

La notion de texte affiché reste dans le cœur, mais le motif de l'appel qui l'affiche (`I18n.t` et `I18n.tn` chez Grid Zero) vient de la configuration de l'hôte. Les ids des nœuds sont inchangés.

## Critères d'acceptation

- [x] Une recherche dans le code de l'outil ne trouve plus aucun nom propre à Grid Zero (scénario, `EtatDeJeu`, `simulation`, `I18n`, moonshot, etc.).
- [x] Un mini-projet témoin avec son propre motif de texte affiché trouve ses textes avec `chercher`.
- [x] Le test de référence de Grid Zero passe.

## Comments

**2026-11-18, fait.**

- Le motif du texte affiché : la clé `texte_affiche` de `graphe.toml`, une expression régulière dont le seul groupe est le texte (`'\btr\("([^"]*)"'`). Sans elle, le cœur ne cherche aucun texte. Un motif invalide, ou qui n'a pas exactement un groupe, arrête la construction avec un message qui nomme la clé. Grid Zero y met l'ancien motif d'`I18n.t` et `I18n.tn`, tel quel.
- L'extension de Grid Zero (`tools/graphe_grid_zero.py`) est déclarée deux fois. Avec `avec_les_lecteurs`, elle donne les commandes (T-0008). Sans, elle contribue après le cœur, dont elle lit les `fin`, les `textes` et les tickets. Elle prend alors l'état envoyé au client (les clés lues par le GDScript, les champs écrits par mot-clé au constructeur), les `"action"` postées vers les actions PHP, les conseils de scénario et le journal moonshot. Elle sait laquelle des deux contribue par `projet.configuration["avec_les_lecteurs"]`. Elle refait le propriétaire de chaque ligne du cœur (le plus petit corps qui la contient), avec `graphe_enrichir.CORPS` et `_commentaire`. La seconde déclaration ne rend pas de `sites` : la couverture reste `{connu: 44}`.
- Le cœur ne sait plus rien de ces notions. Une recherche dans `src/` (scénario, `EtatDeJeu`, `etat_de_jeu`, `simulation`, `I18n`, moonshot, journal, conseil, itération, `handle_command`, `server.py`, Grid Zero, service en ligne) ne trouve plus rien. Il restait ailleurs des traces de Grid Zero, sorties aussi :
  - `A_PART` ne garde que `ticket` et `valeur`. Un hôte ajoute ses sortes hors du code par `[communautes] a_part` (Grid Zero : `conseil`, `iteration`, dans l'ordre d'avant, d'où les mêmes indices de communauté).
  - `_court` ne retire plus `simulation/` ni `godot/` en dur, mais les préfixes de `[communautes] sans_prefixe`.
  - La fraîcheur (`_sources`) porte sur tous les fichiers de l'hôte (`graphe_racine.fichiers("")`), et non plus sur une liste qui nommait les scénarios et le journal : une extension lit ce qu'elle veut. Un fichier suivi qui change (un README) reconstruit donc aussi le graphe, comme le dit T-0001.
  - Dans `RAPPORT.md`, « Du client au serveur » (qui nommait `handle_command`, reste de T-0008) devient « Les commandes ». « Ce que le graphe ne voit pas » ne cite plus les dossiers de Grid Zero.
  - Les docstrings et les commentaires ne prennent plus leurs exemples dans le jeu.
- Test de référence : identique à l'instantané, sans le reprendre. `graphe verifier` dans Grid Zero rend 0. Un scénario modifié rend le graphe périmé.
- Tests :
  - `test_un_hote_avec_son_motif_de_texte_affiche_trouve_ses_textes` : le critère, avec un motif `dire(`. Sans motif, `chercher` ne trouve rien.
  - `test_un_motif_de_texte_sans_groupe_arrete_la_construction`.
  - `test_l_extension_de_grid_zero_relie_l_etat_les_actions_les_conseils_et_le_journal` (`grid_zero`, l'extension copiée dans un hôte témoin) reprend ce que testait `test_valeurs_mots_cles_conseils_et_journal`. Ce dernier devient `test_une_valeur_ecrite_des_deux_cotes`, la seule partie qui reste au cœur.
- Restent, avec leur `shortcut:` :
  - la racine `res://` = `godot/` du lecteur GDScript. Le cœur et `trouver` passent maintenant par `graphe_godot.res`, un seul endroit à corriger.
  - le repli `tools.` des imports du lecteur Python.
  - deux déclarations d'un même fichier qui rendraient chacune des `sites` : seuls les derniers comptent.
  Les changer ferait bouger le test de référence.
- À trancher : T-0001 range au cœur « les champs passés par mot-clé au constructeur ». Avant, le cœur ne le faisait que pour les classes de l'état de Grid Zero (`PROTOCOLE`), et c'est passé tel quel dans l'extension. Une version générale (toute classe, ses champs écrits par mot-clé) ajouterait des liens et reprendrait l'instantané : un ticket à part, si on la veut.
- L'extension importe `graphe_enrichir` et `graphe_godot`, l'intérieur de l'outil, et non le contrat. T-0011 renommera les deux : l'extension suivra.
