Status: ready-for-agent
Type: task
Part of: T-0001
Blocked by: T-0003
Created: 2026-11-17

# T-0006 : Fraîcheur et installer pour tout hôte

## Ce qu'il faut construire

Le graphe est périmé si un fichier de l'hôte ou un fichier de l'outil est plus récent que lui : une requête le reconstruit d'abord. `graphe installer` pose les crochets git (post-commit, post-merge, post-checkout, post-rewrite), qui appellent la commande globale, et ajoute le dossier de sortie au `.gitignore` de l'hôte s'il n'y est pas. `installer --retirer` enlève les crochets.

## Critères d'acceptation

- [ ] Toucher un fichier de l'outil fait reconstruire le graphe d'un hôte à la requête suivante.
- [ ] `installer` sur un mini-projet témoin pose les quatre crochets et ajoute la sortie au `.gitignore`, une seule fois même s'il est lancé deux fois.
- [ ] `installer --retirer` laisse les crochets de l'hôte tels qu'avant `installer`.
- [ ] Dans Grid Zero, les crochets reconstruisent le graphe après un commit.
