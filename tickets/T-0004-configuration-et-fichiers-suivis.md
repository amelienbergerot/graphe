Status: ready-for-agent
Type: task
Part of: T-0001
Blocked by: T-0003
Created: 2026-11-17

# T-0004 : Configuration : fichiers suivis par git, lecteur par extension, graphe.toml

## Ce qu'il faut construire

L'outil marche dans un dépôt sans configuration. Il prend les fichiers suivis par git (plus les fichiers non suivis et non ignorés) et donne chacun au lecteur que désigne son extension. Un fichier qu'aucun lecteur ne prend est ignoré. Un `graphe.toml` facultatif, à la racine de l'hôte, exclut des dossiers. Celui de Grid Zero reproduit exactement l'ensemble des fichiers lu aujourd'hui (dossiers de la simulation et des outils, le client Godot, le service en ligne, sans les tests ni build).

## Critères d'acceptation

- [ ] Un mini-projet témoin sans `graphe.toml` se construit et répond à `expliquer`.
- [ ] Un mini-projet témoin dont `graphe.toml` exclut un dossier n'en a aucun nœud.
- [ ] Un fichier d'une extension qu'aucun lecteur ne prend n'arrête pas la construction.
- [ ] Le `graphe.toml` de Grid Zero est committé dans Grid Zero, et le test de référence passe.

## Comments

**2026-11-17, après T-0002.** L'arbre figé du test de référence est extrait par `git archive` : ce n'est pas un dépôt git, et il n'a pas de `graphe.toml`. Pour lire « les fichiers suivis par git », le test devra extraire l'arbre par `git worktree add --detach` (avec `core.autocrlf=false`) et y poser le `graphe.toml` de l'arbre de travail - de même pour l'extension locale à partir de T-0007.
