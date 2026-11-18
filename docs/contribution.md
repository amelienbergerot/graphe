# Le contrat `contribute(project)`

Les lecteurs et les extensions locales n'ont qu'une interface : une fonction `contribute(project)` qui rend une **contribution**. Le schéma ci-dessous est le contrat. networkx n'en fait pas partie : une extension ne voit jamais que des dictionnaires et des listes.

## L'assemblage

1. Les lecteurs (`python`, `godot`, `php`) contribuent, puis les extensions déclarées `with_readers`. Leurs nœuds entrent ensemble, triés par l'id, après les reprises (`takeovers`).
2. Le cœur enrichit le graphe : étendues, commentaires, textes affichés, variables de module, documents, etc. Un texte affiché est le seul groupe du motif `displayed_text` de `graphe.toml` (par exemple `'\btr\("([^"]*)"'`) ; sans motif, le cœur n'en cherche pas. Les documents sont les Markdown de l'hôte, ou ceux que désigne la liste `[documents] patterns` (comme `exclude`). Celui dont le nom commence par un identifiant (`[documents] identifier`, une expression régulière, `\bT-\d{4}\b` par défaut) est un ticket, d'id `ticket_<identifiant>` ; les autres sont des `document`.
3. Les autres extensions locales contribuent une à une, dans l'ordre où `graphe.toml` les déclare. Chacune voit le graphe que les précédentes ont laissé.

Un lien dont un bout manque au graphe ne crée pas de nœud. Il est compté comme **pendant** (`dangling`) : `graphe check` échoue alors, et `build` affiche les premiers.

## Déclarer une extension locale

Dans le `graphe.toml` de l'hôte, une table par extension, dans l'ordre d'assemblage :

```toml
[[extensions]]
path = "tools/graphe_grid_zero.py"     # relatif à la racine de l'hôte
with_readers = true                   # facultatif : contribuer avec les lecteurs, avant le cœur
# les autres clés de la table : la configuration de l'extension (project.configuration)
```

Une extension `with_readers` contribue comme un lecteur : elle voit le graphe vide, et ses nœuds passent par le cœur, qui leur donne une fin, un commentaire et, pour un corps, ses lignes. C'est le cas d'un corps découpé dans un autre, comme la branche d'une commande dans la fonction qui aiguille. Elle seule peut rendre des reprises.

Une extension après le cœur voit ce qu'il a ajouté : la fin (`end`) de chaque corps, ses textes (`texts`), les documents. Un même fichier peut être déclaré deux fois, avec et sans `with_readers` : il sait laquelle des deux contribue par `project.configuration["with_readers"]`. Une seule des deux rend des `sites`, sinon la seconde remplace la couverture de la première.

Une extension qui ajoute des nœuds hors du code (des conseils, un journal) leur donne leur propre communauté par `graphe.toml`, comme le cœur le fait pour ses tickets, ses valeurs et ses documents :

```toml
[communities]
separate = { hint = "hints" }       # sorte -> nom de la communauté, après les tickets, les valeurs et les documents
strip_prefixes = ["src/"]           # facultatif : retirés du nom d'une communauté
```

Le fichier est un module Python qui définit `contribute(project)`. Une extension déclarée mais introuvable arrête la construction, avec un message qui donne son chemin. C'est le cas aussi quand le module n'a pas de `contribute`.

Le fichier de l'extension est un fichier de l'hôte comme un autre : le lecteur Python le lit aussi, sauf s'il est exclu par `exclude`.

## `project`

| Attribut | Ce que c'est |
|---|---|
| `project.root` | La racine de l'hôte (`Path`). |
| `project.files(suffix)` | Les fichiers de l'hôte qui finissent par `suffix` (`".py"`), triés. Ce sont ceux que git suit, plus les non suivis non ignorés, moins `exclude`. |
| `project.configuration` | La section de celui qui contribue. Pour un lecteur, c'est la table qui porte son nom (`[godot]`). Pour une extension, c'est sa table `[[extensions]]`. |
| `project.graph` | Le graphe déjà assemblé, sous la forme `{"nodes": {id: nœud}, "links": [lien assemblé]}`. C'est une copie : la modifier ne change rien au graphe. Les lecteurs le reçoivent vide. |
| `project.checking` | Vrai sous `graphe check`. Un lecteur peut alors ajouter ses contrôles coûteux, comme le recomptage des appels GDScript. |

Un **lien assemblé** a un seul exemplaire par paire de nœuds : `source`, `target`, `relations` (une liste triée), `confidence`, `locations` (`"fichier:ligne"`) et `contexts`. C'est la forme des liens de `graphe.json`.

## La contribution

C'est un dictionnaire. Chaque clé est facultative.

```python
{"nodes": [...], "links": [...], "sites": [...], "takeovers": [...]}
```

### Un nœud

| Champ | Obligatoire | Ce que c'est |
|---|---|---|
| `id` | toujours | Un identifiant unique dans le graphe (`outils_aider`). |
| `label` | nœud nouveau | Ce qu'affichent les requêtes (`aider()`). |
| `kind` | nœud nouveau | `file`, `function`, `method`, `class`, `field`, `command`, `action`, `signal`, … ou une sorte propre à l'extension. |
| `source_file` | nœud nouveau | Le chemin relatif à la racine, avec des `/`. |
| `source_location` | nœud nouveau | La ligne, sous la forme `"L12"`. |
| `name` | nœud nouveau | Le nom par lequel on désigne le nœud (`aider`, `Classe.methode`). |
| autres | non | Des attributs libres. Le cœur en lit certains : `texts` (une liste, montrée par « displays: »), `notes` (un commentaire), `end` (la dernière ligne, pour `--source`). |

Un nœud rendu avec un id qui existe déjà **fusionne** ses attributs dans ce nœud : seul `id` est alors obligatoire, et chaque attribut rendu remplace l'ancien. Il manque un champ obligatoire à un nœud nouveau ? La construction s'arrête, avec un message qui nomme celui qui contribue et l'id.

### Un lien

Tous les champs sont obligatoires.

| Champ | Ce que c'est |
|---|---|
| `source`, `target` | Les ids des deux bouts. |
| `relation` | `calls`, `contains`, `imports`, `reads`, `writes`, `cites`, `sends`, `dispatches`, … ou une relation propre à l'extension. `callers` ne suit que les relations d'appel (`APPELS`, dans `graphe.py`). |
| `confidence` | `"EXTRACTED"` (lien sûr) ou `"INFERRED"` (lien établi par le nom seul). Entre deux nœuds, un lien `EXTRACTED` l'emporte. |
| `source_file`, `source_location` | Le lieu du lien (`"L12"`). |
| `context` | Un mot sur le lien (l'alias d'un import, le nom d'un ordre), ou `""`. |

Deux liens entre les mêmes nœuds n'en font qu'un, qui garde toutes leurs relations et tous leurs lieux.

### Une reprise (`takeovers`)

Seulement pour une extension `with_readers`. Les liens qui partent de `from` depuis les lignes `lines` de `source_file` partent désormais de `to`. Une reprise ne touche que les liens des lecteurs, avant l'assemblage. Les reprises s'appliquent dans l'ordre : une reprise voit les précédentes. Pour une branche dans une branche, on rend donc celle du dehors d'abord.

| Champ | Ce que c'est |
|---|---|
| `from`, `to` | Le nœud qui perd les liens, celui qui les prend. |
| `source_file` | Le fichier des lignes, comme dans un lien. |
| `lines` | `[début, fin]`, bornes comprises. |

### Un site de couverture

Un site est un endroit du code que celui qui contribue a classé. C'est par exemple un appel, et ce qu'il est devenu.

| Champ | Ce que c'est |
|---|---|
| `file`, `line`, `text` | Où est le site, et ce qu'il dit (`runner.set_dispatch`). |
| `name` | Le nom appelé, s'il y a lieu. |
| `verdict` | Facultatif : le classement (`ours`, `ours?`, `ambiguous`, `external`, `engine`, …). |
| `alert` | Facultatif : pourquoi le site est un défaut (« not linked to the name of one of our functions »). |

Si une contribution a la clé `sites`, même vide, `graphe.json` porte sa couverture : `coverage[<qui>]` compte ses verdicts. `<qui>` est le nom du lecteur ou le chemin de l'extension. `graphe check` montre, pour chaque contribution, le compte de chaque verdict, ses textes les plus fréquents et chaque alerte. Il échoue s'il y a une alerte ou un lien pendant.
