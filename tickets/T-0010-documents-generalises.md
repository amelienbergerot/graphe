Status: ready-for-agent
Type: task
Part of: T-0001
Blocked by: T-0007
Created: 2026-11-17

# T-0010 : Documents généralisés

## Ce qu'il faut construire

Tous les fichiers Markdown de l'hôte sont des documents par défaut, et `graphe.toml` peut les restreindre par une liste de motifs. Un document cite un nœud qu'il nomme entre accents graves, et un autre document par un identifiant dont le motif est configurable (celui des tickets `T-` suivi de quatre chiffres par défaut). Le code qui contient un identifiant de document cite ce document. Grid Zero restreint sa liste à ses tickets. L'outil se lit lui-même, tickets compris : c'est son troisième hôte.

## Critères d'acceptation

- [ ] `graphe expliquer` sur une fonction de ce dépôt nomme le ticket qui la cite.
- [ ] Un mini-projet témoin avec un motif d'identifiant à lui relie ses documents entre eux.
- [ ] Le test de référence de Grid Zero passe.
