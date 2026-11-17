Status: ready-for-agent
Type: task
Part of: T-0001
Blocked by: T-0011
Created: 2026-11-17

# T-0013 : La skill Claude Code

## Ce qu'il faut construire

Une skill Claude Code, livrée dans ce dépôt et installée une fois pour le compte. Elle apprend l'outil à l'agent dans tous les projets : quand préférer le graphe à grep, comment désigner un nœud (id, nom, `Classe.methode`, `fichier::nom`), quelles requêtes existent, et où noter un manque (le backlog de l'outil, en nommant l'hôte). Elle remplace les deux mémoires « graphe » de Grid Zero.

## Critères d'acceptation

- [ ] La skill est installée et se déclenche dans un dépôt autre que Grid Zero, quand l'agent cherche du code.
- [ ] Les deux mémoires « graphe » de Grid Zero sont retirées, et leur contenu utile est dans la skill.
- [ ] Le dépôt documente comment l'installer.
