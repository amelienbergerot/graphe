Status: ready-for-agent
Type: task
Part of: T-0001
Blocked by: T-0011
Created: 2026-11-17

# T-0014 : Lecteur JS avec tree-sitter, branché sur dpe

## Ce qu'il faut construire

Un lecteur fondé sur tree-sitter (ADR 0002) lit les fichiers `.js` et `.mjs`. Il produit les modules, les fonctions, les classes et leurs méthodes, et résout les appels par le nom et par les imports. Le choix des grammaires (un paquet commun ou un paquet par langage) se fait ici. dpe devient le deuxième hôte : son `graphe.toml` exclut le dossier de débogage, et ses données XML sont ignorées sans réglage.

## Critères d'acceptation

- [ ] Un mini-projet JS témoin, avec un import nommé, un import par défaut et un appel de méthode, donne les liens attendus.
- [ ] `graphe expliquer` marche sur une fonction du moteur de calcul de dpe, et nomme le ticket qui la cite.
- [ ] La couverture de `verifier` sur dpe est notée dans ce ticket, comme référence.
- [ ] Les appels que le lecteur manque sur dpe sont notés dans le backlog, avec l'hôte.
