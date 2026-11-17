Status: closed
Type: task
Part of: T-0001
Blocked by: T-0004
Created: 2026-11-17

# T-0005 : Chemins réglables des programmes externes

## Ce qu'il faut construire

Un lecteur qui lance un programme externe (aujourd'hui seul le lecteur GDScript, qui lance Godot pour lire l'API du moteur) le cherche dans cet ordre : la clé `executable` de sa section dans `graphe.toml`, puis le PATH. S'il ne le trouve pas, il continue sans lui, avec un avertissement qui nomme la clé à régler, et les appels qu'il aurait résolus restent non résolus. Le chemin de l'exécutable Godot n'est plus écrit en dur. La règle vaut pour tout futur lecteur du même genre.

## Critères d'acceptation

- [x] Un mini-projet GDScript sans Godot se construit, et l'avertissement nomme la clé.
- [x] Avec la clé renseignée, les appels au moteur sont résolus.
- [x] Le `graphe.toml` de Grid Zero donne son exécutable Godot, et le test de référence passe.

## Comments

**2026-11-17, fait (Grid Zero : son ticket T-0384).**

- `graphe_racine.executable(section, nom)` : la clé `executable` de `[section]` du `graphe.toml`, relative à la racine (un chemin absolu reste absolu), puis `nom` dans le PATH, sinon `None`. Une clé qui désigne un fichier absent est signalée, puis le PATH est essayé. Sans programme, l'avertissement nomme `[section] executable`. C'est la règle de tout lecteur qui lance un programme.
- Le lecteur GDScript : la section `[godot]`, le programme `godot`. Il ne cherche Godot qu'à défaut du cache `graphe/extension_api.json`. Sans Godot, l'API du moteur est vide et rien n'entre au cache : la clé, une fois réglée, sert à la construction suivante. Un Godot qui échoue, ou qui rend un JSON illisible, est traité comme un Godot absent (avertissement qui nomme la clé, rien au cache).
- Grid Zero : `[godot] executable = "godot/Godot_v4.7.2-stable_win64_console.exe"`. Le test de référence passe. Il copie le cache dans l'arbre figé, donc il ne lit pas la clé : la clé a été vérifiée à part, en retirant le cache de l'arbre de travail. Godot, lancé par la clé, a redonné un `extension_api.json` identique à l'octet près. `graphe verifier` : code de sortie 0.
- Tests (`tests/test_hote.py`) : un hôte GDScript sans Godot (PATH réduit à git), qui se construit, nomme la clé et ne range aucun appel au moteur ; le même hôte avec la clé, vers un faux Godot `.cmd` (Windows seulement, `shortcut:` noté), qui en range.
- Limites :
  - Sans API, un appel au moteur qui porte le nom d'une de nos fonctions est deviné vers la nôtre (`notre?`, lien `INFERRED`), comme tout appel hors de l'API. Il est donc mal résolu, et non « non résolu ». C'est sans effet chez Grid Zero, qui a l'API.
  - Pour T-0006 : le cache de l'API n'est jamais renouvelé, même quand la clé change (un autre Godot). Il faut alors l'effacer à la main.
