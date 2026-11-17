# Un outil installé une fois, des extensions locales dans chaque hôte

Le graphe est né dans `grid_zero/tools/` avec des chemins et des notions de Grid Zero écrits en dur (scénarios, protocole `EtatDeJeu`, commandes `simulation_server_cmd_`). Il devient un dépôt séparé, installé comme commande globale en mode éditable (`uv tool install -e`), et tout ce qui ne vaut que pour un hôte sort du cœur : c'est une extension locale, rangée dans le dépôt de l'hôte et déclarée dans son `graphe.toml`.

## Options écartées

- Une copie du dossier dans chaque projet : chaque correction serait à reporter à la main, et les copies divergeraient.
- Un sous-module git : la même source, mais une mise à jour à tirer dans chaque hôte, pour un seul utilisateur.
- Garder les notions de Grid Zero dans le cœur derrière des options : le cœur saurait des choses d'un hôte, ce qu'une publication rendrait illisible.
