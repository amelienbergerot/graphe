Status: closed
Type: task
Part of: T-0001
Blocked by: T-0003
Created: 2026-11-17

# T-0004 : Configuration : fichiers suivis par git, lecteur par extension, graphe.toml

## Ce qu'il faut construire

L'outil marche dans un dépôt sans configuration. Il prend les fichiers suivis par git (plus les fichiers non suivis et non ignorés) et donne chacun au lecteur que désigne son extension. Un fichier qu'aucun lecteur ne prend est ignoré. Un `graphe.toml` facultatif, à la racine de l'hôte, exclut des dossiers. Celui de Grid Zero reproduit exactement l'ensemble des fichiers lu aujourd'hui (dossiers de la simulation et des outils, le client Godot, le service en ligne, sans les tests ni build).

## Critères d'acceptation

- [x] Un mini-projet témoin sans `graphe.toml` se construit et répond à `expliquer`.
- [x] Un mini-projet témoin dont `graphe.toml` exclut un dossier n'en a aucun nœud.
- [x] Un fichier d'une extension qu'aucun lecteur ne prend n'arrête pas la construction.
- [x] Le `graphe.toml` de Grid Zero est committé dans Grid Zero, et le test de référence passe.

## Comments

**2026-11-17, après T-0002.** L'arbre figé du test de référence est extrait par `git archive` : ce n'est pas un dépôt git, et il n'a pas de `graphe.toml`. Pour lire « les fichiers suivis par git », le test devra extraire l'arbre par `git worktree add --detach` (avec `core.autocrlf=false`) et y poser le `graphe.toml` de l'arbre de travail - de même pour l'extension locale à partir de T-0007.

**2026-11-17, fait (Grid Zero : son ticket T-0383).**

- `graphe_racine.fichiers(suffixe)` : `git ls-files -z --cached --others --exclude-standard`, moins les fichiers absents (supprimés, pas encore indexés), moins la sortie `graphe/`, moins `exclure` du `graphe.toml`. Un motif désigne un fichier ou l'un de ses dossiers (`PurePosixPath.full_match`) : `build` est le build/ de la racine, `**/tests` tout dossier tests/. Hors d'un dépôt git : une erreur qui le dit. Chaque lecteur garde sa fonction (`graphe_python.fichiers`, `graphe_godot.scripts`, `graphe_php.fichiers`), réduite à son suffixe.
- Le `graphe.toml` de Grid Zero : `exclure = ["build", "**/tests", "web/**/tests.php", "godot/**/addons"]`. Le test de référence passe (et échoue avec `exclure = []`). Il sort l'arbre figé par `git worktree add --detach`, sans crochets : sinon, le post-checkout lancerait l'ancien outil dans l'arbre figé.
- Sur l'arbre de travail de Grid Zero, un seul fichier sort du graphe : `godot/net/cle_du_defi.gd`, que git ignore (une clé produite).
- Tests : `tests/test_hote.py`, la commande `graphe` sur deux hôtes témoins (un sans configuration, un avec `exclure`, un fichier ignoré et un `.xml`).
- Pour que l'hôte témoin se construise, le cœur saute Godot quand il n'y a aucun `.gd`, et la lecture de `simulation/server.py` rend un ensemble vide s'il manque. Rien de plus : le chemin de Godot est l'objet de T-0005, et les commandes du serveur celui de T-0008.
- Limites, écrites :
  - `res://` part toujours de `godot/` (`shortcut:` dans `graphe_godot.py`). Un `.gd` hors de `godot/` casse la construction : à régler (chercher `project.godot`) avant un hôte GDScript autre que Grid Zero.
  - Pour T-0006 : la fraîcheur ne voit ni un fichier supprimé, ni une modification du `.gitignore`. `graphe.toml` est maintenant compté parmi les sources. Une requête lance `git ls-files` trois fois, une par lecteur.
