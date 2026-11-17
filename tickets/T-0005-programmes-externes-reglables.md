Status: ready-for-agent
Type: task
Part of: T-0001
Blocked by: T-0004
Created: 2026-11-17

# T-0005 : Chemins réglables des programmes externes

## Ce qu'il faut construire

Un lecteur qui lance un programme externe (aujourd'hui seul le lecteur GDScript, qui lance Godot pour lire l'API du moteur) le cherche dans cet ordre : la clé `executable` de sa section dans `graphe.toml`, puis le PATH. S'il ne le trouve pas, il continue sans lui, avec un avertissement qui nomme la clé à régler, et les appels qu'il aurait résolus restent non résolus. Le chemin de l'exécutable Godot n'est plus écrit en dur. La règle vaut pour tout futur lecteur du même genre.

## Critères d'acceptation

- [ ] Un mini-projet GDScript sans Godot se construit, et l'avertissement nomme la clé.
- [ ] Avec la clé renseignée, les appels au moteur sont résolus.
- [ ] Le `graphe.toml` de Grid Zero donne son exécutable Godot, et le test de référence passe.
