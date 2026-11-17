Status: closed
Type: task
Part of: T-0001
Blocked by: T-0003
Created: 2026-11-17

# T-0006 : Fraîcheur et installer pour tout hôte

## Ce qu'il faut construire

Le graphe est périmé si un fichier de l'hôte ou un fichier de l'outil est plus récent que lui : une requête le reconstruit d'abord. `graphe installer` pose les crochets git (post-commit, post-merge, post-checkout, post-rewrite), qui appellent la commande globale, et ajoute le dossier de sortie au `.gitignore` de l'hôte s'il n'y est pas. `installer --retirer` enlève les crochets.

## Critères d'acceptation

- [x] Toucher un fichier de l'outil fait reconstruire le graphe d'un hôte à la requête suivante.
- [x] `installer` sur un mini-projet témoin pose les quatre crochets et ajoute la sortie au `.gitignore`, une seule fois même s'il est lancé deux fois.
- [x] `installer --retirer` laisse les crochets de l'hôte tels qu'avant `installer`.
- [x] Dans Grid Zero, les crochets reconstruisent le graphe après un commit.

## Comments

**2026-11-17, fait.**

- Fraîcheur : `charger` compare `graphe.json` aux fichiers de l'hôte (`_sources`) et à ceux de l'outil (`_outil` : les `graphe*.py` à côté de `graphe.py`, soit `src/` en installation éditable). Les modules à venir (T-0007) y entrent seuls s'ils gardent le préfixe `graphe`.
- `installer` : le bloc appelle la commande globale (`graphe construire --calme`, en arrière-plan), plus `python … tools/graphe.py`. Le bloc est un ajout exact, précédé d'un saut de ligne : `--retirer` rend le crochet à l'octet près, et efface ceux que `installer` a créés. Le début du bloc est reconnu par son préfixe `# >>> graphe du code`, donc un ancien bloc (posé par Grid Zero) est remplacé, pas doublé ; sa fin l'est en LF comme en CRLF.
- `.gitignore` : `/graphe/` est ajouté, sauf si git ignore déjà la sortie (`git check-ignore graphe/`, sous quelque forme que ce soit : Grid Zero a `graphe/`). L'ajout se fait en octets, un `.gitignore` hors UTF-8 reste intact. `--retirer` n'y touche pas.
- Tests (`tests/test_hote.py`) : un graphe plus ancien que l'outil se reconstruit à la requête (et un témoin plus récent ne se reconstruit pas), sans toucher aux fichiers de l'outil ; `installer` lancé deux fois sur un hôte témoin (un crochet déjà là, un `.gitignore` sans fin de ligne) ; `--retirer` rend les crochets à l'octet près ; un `.gitignore` qui a déjà `graphe/` reste tel quel. L'ancien test des crochets (`test_graphe.py`, par le paramètre `dossier`, retiré) est couvert par ceux-là.
- Grid Zero : le test de référence passe. Le critère des crochets a été vérifié sur un clone jetable de Grid Zero (les crochets du vrai dépôt n'ont pas été posés) : `graphe installer`, un commit, et le `graphe.json` reconstruit en arrière-plan porte ce commit, sans `erreur.txt` ; `.gitignore` inchangé ; `--retirer` n'a laissé aucun crochet.
- Limites :
  - Un crochet de l'hôte réduit à `#!/bin/sh` est effacé par `--retirer`, comme un crochet que `installer` a créé.
  - Un ancien bloc (posé par Grid Zero avant T-0006), une fois retiré, laisse le crochet sans son saut de ligne final. Sans effet aujourd'hui : Grid Zero n'a aucun crochet posé.
  - Le crochet compte sur `graphe` dans le PATH du shell de git. Sinon il échoue en silence, et la requête suivante reconstruit quand même le graphe.
  - Laissé de T-0005 : le cache `graphe/extension_api.json` n'est toujours pas renouvelé quand `[godot] executable` change. Le test de référence de Grid Zero copie ce cache, donc le lier à `graphe.toml` demande prudence. Il faut toujours l'effacer à la main.
