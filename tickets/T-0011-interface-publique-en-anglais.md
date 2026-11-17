Status: ready-for-agent
Type: task
Part of: T-0001
Blocked by: T-0005, T-0006, T-0008, T-0009, T-0010
Created: 2026-11-17

# T-0011 : Interface publique en anglais

## Ce qu'il faut construire

Tout ce qu'un utilisateur ou un hôte voit passe en anglais : les commandes, les clés de `graphe.toml`, les champs du JSON, les sortes de nœuds et de relations, les messages, `graphe.html` et le rapport. Grid Zero migre dans la même étape : son `tools/graphe.py`, son extension locale, son `graphe.toml`, son README, ses mémoires qui citent les commandes, et une nouvelle prise de l'instantané de référence avec les noms traduits.

## Critères d'acceptation

- [ ] Plus aucun mot français dans l'interface. La commande d'aide le montre.
- [ ] Dans Grid Zero, le nouvel instantané ne diffère de l'ancien que par la traduction des noms. Vérification par une table de correspondance appliquée à l'ancien instantané.
- [ ] Les mémoires et le README de Grid Zero citent les nouvelles commandes.
- [ ] Les tests de ce dépôt et de Grid Zero passent.
