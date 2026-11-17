# Le contrat `contribuer(projet)`

Les lecteurs et les extensions locales n'ont qu'une interface : une fonction `contribuer(projet)` qui rend une **contribution**. Le schéma ci-dessous est le contrat. networkx n'en fait pas partie : une extension ne voit jamais que des dictionnaires et des listes.

## L'assemblage

1. Les lecteurs (`python`, `godot`, `php`) contribuent. Leurs nœuds entrent ensemble, triés par l'id.
2. Le cœur enrichit le graphe : étendues, commentaires, textes affichés, variables de module, documents, etc.
3. Les extensions locales contribuent une à une, dans l'ordre où `graphe.toml` les déclare. Chacune voit le graphe que les précédentes ont laissé.

Un lien dont un bout manque au graphe ne crée pas de nœud. Il est compté comme **pendant** : `graphe verifier` échoue alors, et `construire` affiche les premiers.

## Déclarer une extension locale

Dans le `graphe.toml` de l'hôte, une table par extension, dans l'ordre d'assemblage :

```toml
[[extensions]]
chemin = "tools/graphe_grid_zero.py"   # relatif à la racine de l'hôte
# les autres clés de la table : la configuration de l'extension (projet.configuration)
```

Le fichier est un module Python qui définit `contribuer(projet)`. Une extension déclarée mais introuvable arrête la construction, avec un message qui donne son chemin. C'est le cas aussi quand le module n'a pas de `contribuer`.

Le fichier de l'extension est un fichier de l'hôte comme un autre : le lecteur Python le lit aussi, sauf s'il est exclu par `exclure`.

## `projet`

| Attribut | Ce que c'est |
|---|---|
| `projet.racine` | La racine de l'hôte (`Path`). |
| `projet.fichiers(suffixe)` | Les fichiers de l'hôte qui finissent par `suffixe` (`".py"`), triés. Ce sont ceux que git suit, plus les non suivis non ignorés, moins `exclure`. |
| `projet.configuration` | La section de celui qui contribue. Pour un lecteur, c'est la table qui porte son nom (`[godot]`). Pour une extension, c'est sa table `[[extensions]]`. |
| `projet.graphe` | Le graphe déjà assemblé, sous la forme `{"noeuds": {id: nœud}, "liens": [lien assemblé]}`. C'est une copie : la modifier ne change rien au graphe. Les lecteurs le reçoivent vide. |
| `projet.verifier` | Vrai sous `graphe verifier`. Un lecteur peut alors ajouter ses contrôles coûteux, comme le recomptage des appels GDScript. |

Un **lien assemblé** a un seul exemplaire par paire de nœuds : `source`, `target`, `relations` (une liste triée), `confiance`, `lieux` (`"fichier:ligne"`) et `contextes`. C'est la forme des liens de `graphe.json`.

## La contribution

C'est un dictionnaire. Chaque clé est facultative.

```python
{"noeuds": [...], "liens": [...], "sites": [...]}
```

### Un nœud

| Champ | Obligatoire | Ce que c'est |
|---|---|---|
| `id` | toujours | Un identifiant unique dans le graphe (`outils_aider`). |
| `label` | nœud nouveau | Ce qu'affichent les requêtes (`aider()`). |
| `sorte` | nœud nouveau | `fichier`, `fonction`, `methode`, `classe`, `champ`, `commande`, `action`, `signal`, … ou une sorte propre à l'extension. |
| `source_file` | nœud nouveau | Le chemin relatif à la racine, avec des `/`. |
| `source_location` | nœud nouveau | La ligne, sous la forme `"L12"`. |
| `nom` | nœud nouveau | Le nom par lequel on désigne le nœud (`aider`, `Classe.methode`). |
| autres | non | Des attributs libres. Le cœur en lit certains : `textes` (une liste, montrée par « affiche : »), `notes` (un commentaire), `fin` (la dernière ligne, pour `--source`). |

Un nœud rendu avec un id qui existe déjà **fusionne** ses attributs dans ce nœud : seul `id` est alors obligatoire, et chaque attribut rendu remplace l'ancien. Il manque un champ obligatoire à un nœud nouveau ? La construction s'arrête, avec un message qui nomme celui qui contribue et l'id.

### Un lien

Tous les champs sont obligatoires.

| Champ | Ce que c'est |
|---|---|
| `source`, `target` | Les ids des deux bouts. |
| `relation` | `calls`, `contains`, `imports`, `lit`, `ecrit`, `cite`, `sends`, `dispatches`, … ou une relation propre à l'extension. `appelants` ne suit que les relations d'appel (`APPELS`, dans `graphe.py`). |
| `confidence` | `"EXTRACTED"` (lien sûr) ou `"INFERRED"` (lien établi par le nom seul). Entre deux nœuds, un lien `EXTRACTED` l'emporte. |
| `source_file`, `source_location` | Le lieu du lien (`"L12"`). |
| `context` | Un mot sur le lien (l'alias d'un import, le nom d'un ordre), ou `""`. |

Deux liens entre les mêmes nœuds n'en font qu'un, qui garde toutes leurs relations et tous leurs lieux.

### Un site de couverture

Un site est un endroit du code que celui qui contribue a classé. C'est par exemple un appel, et ce qu'il est devenu.

| Champ | Ce que c'est |
|---|---|
| `fichier`, `ligne`, `texte` | Où est le site, et ce qu'il dit (`runner.set_dispatch`). |
| `nom` | Le nom appelé, s'il y a lieu. |
| `verdict` | Facultatif : le classement (`notre`, `notre?`, `ambigu`, `externe`, `moteur`, …). |
| `alerte` | Facultatif : pourquoi le site est un défaut (« non relié au nom d'une de nos fonctions »). |

Si une contribution a la clé `sites`, même vide, `graphe.json` porte sa couverture : `couverture[<qui>]` compte ses verdicts. `<qui>` est le nom du lecteur ou le chemin de l'extension. `graphe verifier` montre, pour chaque contribution, le compte de chaque verdict, ses textes les plus fréquents et chaque alerte. Il échoue s'il y a une alerte ou un lien pendant.
