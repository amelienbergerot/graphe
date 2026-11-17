Status: ready-for-agent
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

- [ ] Une recherche dans le code de l'outil ne trouve plus aucun nom propre à Grid Zero (scénario, `EtatDeJeu`, `simulation`, `I18n`, moonshot, etc.).
- [ ] Un mini-projet témoin avec son propre motif de texte affiché trouve ses textes avec `chercher`.
- [ ] Le test de référence de Grid Zero passe.
