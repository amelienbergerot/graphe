Status: ready-for-agent
Type: spec
Created: 2026-11-17

# Le graphe, un outil autonome pour tous mes projets

## Le problème

Le graphe du code est né dans Grid Zero et ne sert qu'à Grid Zero. L'agent qui travaille sur 4cast ou sur dpe n'a que grep et la lecture de fichiers, alors que le graphe localise le code avec 2 à 12 fois moins de tokens. On ne peut pas l'emporter ailleurs : les dossiers lus, la sortie, l'exécutable Godot et les notions du jeu (scénarios, protocole client-serveur, commandes du serveur, service en ligne, journal moonshot) sont écrits en dur dans les lecteurs et dans l'enrichissement. Aucun lecteur ne sait lire du JavaScript, du TypeScript ou du Svelte. Enfin, ce qui manque au graphe est noté dans un fichier propre à Grid Zero, et l'agent n'apprend l'outil que par des mémoires propres à Grid Zero.

## La solution

Le graphe devient un outil installé une fois, en commande globale (`graphe`), qui sert n'importe quel projet hôte. Lancé dans un dépôt sans aucune configuration, il lit les fichiers suivis par git avec le lecteur de leur langage et répond aux mêmes questions qu'aujourd'hui : expliquer, appelants, chemin, chercher. Un `graphe.toml` facultatif sert à exclure des dossiers, donner le chemin d'un programme externe, régler les documents et déclarer les extensions locales. Ce qui ne vaut que pour Grid Zero devient une extension locale rangée dans Grid Zero, et Grid Zero obtient exactement le même graphe qu'avant (ADR 0001). De nouveaux lecteurs, fondés sur tree-sitter (ADR 0002), ouvrent l'outil à dpe (`.mjs`) puis à 4cast (TypeScript, Svelte et PHP). Une skill Claude Code apprend l'outil à l'agent dans tous les projets. L'outil reste en français pendant l'extraction, puis il passe en anglais avant d'accueillir un deuxième hôte : c'est la condition pour pouvoir le publier un jour.

## Récits d'utilisation

1. En tant qu'agent qui travaille dans un projet hôte, je veux taper `graphe expliquer X` dans n'importe quel dépôt, pour localiser du code sans grep.
2. En tant qu'agent, je veux désigner un nœud par son id, son nom, `Classe.methode` ou `fichier::nom`, pour ne pas avoir à connaître les ids internes.
3. En tant qu'agent, je veux `graphe appelants X --profondeur N`, pour mesurer la portée d'un changement avant de le faire.
4. En tant qu'agent, je veux `graphe chemin A B`, pour comprendre comment une action mène à un effet.
5. En tant qu'agent, je veux `graphe chercher MOTIF` par nom, par texte affiché et par commentaire, pour retrouver le code d'un texte vu à l'écran ou d'un concept.
6. En tant qu'agent, je veux `expliquer X --source`, pour lire le corps d'une fonction sans ouvrir son fichier.
7. En tant qu'agent, je veux que `expliquer X` liste les documents qui citent X, pour retrouver le ticket qui a motivé un code.
8. En tant qu'agent, je veux qu'une requête sur un graphe périmé le reconstruise d'abord, pour ne jamais raisonner sur un graphe faux.
9. En tant qu'agent, je veux que le graphe soit aussi considéré comme périmé quand l'outil lui-même a changé, pour profiter tout de suite d'un lecteur corrigé.
10. En tant qu'agent, je veux des réponses courtes et denses, pour dépenser peu de tokens.
11. En tant qu'agent qui arrive dans un nouveau projet, je veux une skill qui me dise quand préférer le graphe à grep, comment désigner un nœud et où noter un manque, pour utiliser l'outil sans mémoire propre au projet.
12. En tant qu'agent qui trouve une question à laquelle le graphe ne sait pas répondre, je veux noter le manque dans le backlog unique de l'outil, en nommant l'hôte, pour que l'outil s'améliore au même endroit pour tous les projets.
13. En tant que développeur, je veux installer l'outil une fois en mode éditable, pour qu'une correction serve à tous les hôtes sans copie.
14. En tant que développeur, je veux que l'outil marche dans un dépôt sans configuration, pour l'essayer sur un projet en une commande.
15. En tant que développeur, je veux exclure des dossiers par `graphe.toml`, par exemple le `scratch_debug` de dpe, pour garder le graphe sur le code qui compte.
16. En tant que développeur, je veux que les fichiers qu'aucun lecteur ne prend, comme le XML de dpe, soient ignorés sans configuration.
17. En tant que développeur, je veux régler le chemin de chaque programme externe qu'un lecteur lance, comme l'exécutable Godot, dans `graphe.toml`, pour que l'outil marche quelle que soit l'installation.
18. En tant que développeur, je veux qu'un lecteur trouve son programme dans le PATH quand `graphe.toml` ne le donne pas, et qu'il continue sans lui avec un avertissement qui nomme la clé à régler quand il ne le trouve pas, pour qu'un programme absent ne casse jamais la construction.
19. En tant que développeur de Grid Zero, je veux que mon graphe reste identique après l'extraction, pour ne rien perdre de ce que les tickets T-0353 et T-0354 ont construit.
20. En tant que développeur de Grid Zero, je veux garder `python tools/graphe.py …`, mes crochets git et mes habitudes, pour que l'extraction ne me coûte rien au quotidien.
21. En tant que développeur de Grid Zero, je veux que les conseils de scénario, le protocole de l'état, les commandes du serveur, les actions du service en ligne, les textes de `I18n` et le journal moonshot vivent dans une extension locale de Grid Zero, pour que le cœur ne sache rien du jeu.
22. En tant qu'auteur d'une extension locale, je veux écrire une fonction `contribuer(projet)` qui rend une contribution, comme un lecteur, pour n'avoir qu'un seul contrat à apprendre.
23. En tant qu'auteur d'une extension locale, je veux lire le graphe déjà assemblé, pour relier mes nœuds à ceux des lecteurs.
24. En tant qu'auteur d'une extension locale, je veux qu'un nœud rendu avec un id existant enrichisse ce nœud, pour ajouter des attributs (des textes affichés, par exemple) sans le recréer.
25. En tant qu'auteur d'une extension locale, je veux que le schéma d'un nœud et d'un lien soit un contrat documenté, et non la structure interne de networkx, pour que mon extension survive à un changement de bibliothèque.
26. En tant qu'auteur d'un lecteur, je veux rendre des sites de couverture, pour que `graphe verifier` dise ce que mon lecteur a résolu et ce qu'il a manqué.
27. En tant que développeur, je veux que tous les fichiers Markdown suivis par git soient des documents par défaut, et que `graphe.toml` puisse les restreindre, pour que les tickets de dpe et les issues de 4cast entrent dans le graphe sans réglage.
28. En tant que développeur, je veux régler le motif d'identifiant des documents (`T-\d{4}` par défaut), pour que les tickets se citent entre eux quel que soit le format du projet.
29. En tant que développeur de dpe, je veux que les fichiers `.mjs` et `.js` soient lus, appels résolus par le nom et par les imports, pour naviguer dans le moteur de calcul.
30. En tant que développeur de 4cast, je veux que les fichiers `.ts` et le bloc `<script>` des fichiers `.svelte` soient lus, et que l'API PHP le soit par le lecteur PHP existant, pour naviguer du front au back.
31. En tant que développeur, je veux que l'outil se lise lui-même, tickets compris, pour disposer d'un troisième hôte de test sans effort.
32. En tant que développeur, je veux que `graphe installer` pose les crochets git et ajoute le dossier de sortie au `.gitignore` de l'hôte, pour qu'un nouvel hôte soit prêt en une commande.
33. En tant que développeur, je veux que `graphe installer --retirer` enlève les crochets, pour sortir proprement un hôte.
34. En tant que futur mainteneur open source, je veux une interface entièrement en anglais (commandes, clés de configuration, champs du JSON, sortes de nœuds, code, documentation), pour que d'autres puissent l'utiliser.
35. En tant que développeur, je veux que le passage à l'anglais arrive avant le deuxième hôte, pour n'avoir qu'un seul hôte (Grid Zero) et ses mémoires à migrer.
36. En tant que développeur, je veux garder `graphe.html` et `RAPPORT.md` pour mes propres explorations, même si l'agent passe en premier.

## Décisions d'implémentation

- **Forme.** Un dépôt séparé, un paquet Python qui fournit la commande `graphe`, installé avec `uv tool install -e`. Les dépendances sont networkx et tree-sitter, plus les grammaires à partir du lecteur JS/TS. Le premier commit cite le commit de Grid Zero d'où vient le code, sans reprendre l'historique.
- **La racine de l'hôte** est le dépôt git courant, et non plus l'emplacement du script. La sortie reste dans `graphe/` à la racine de l'hôte.
- **Les fichiers lus** sont ceux suivis par git, plus les fichiers non suivis et non ignorés, comme aujourd'hui (« l'arbre de travail compris »). Chaque fichier va au lecteur que désigne son extension. Les tests et build restent exclus par défaut chez Grid Zero, via son `graphe.toml`.
- **Le contrat `contribuer(projet)`.** C'est l'unique interface des lecteurs et des extensions locales. `projet` donne la racine, les fichiers de l'hôte, la configuration (la section propre à celui qui contribue) et le graphe déjà assemblé, en lecture seule. La contribution rend des nœuds, des liens et, s'il y a lieu, des sites de couverture.
- **Le schéma des nœuds et des liens** reprend les champs actuels : id, label, sorte, fichier source, ligne pour un nœud ; source, cible, relation, confiance (`EXTRACTED`/`INFERRED`), lieu, contexte pour un lien. Il est documenté comme un contrat, et networkx n'en fait pas partie.
- **La fusion.** Un nœud rendu avec un id existant fusionne ses attributs dans le nœud en place. Un lien vers un nœud absent est compté comme pendant, comme aujourd'hui.
- **L'ordre d'assemblage** : les lecteurs, puis les enrichissements du cœur, puis les extensions locales dans l'ordre où `graphe.toml` les déclare. Les nœuds et les liens sont triés avant l'insertion, pour que les communautés (Louvain, graine fixe) ne dépendent pas de l'ordre des contributions.
- **Le cœur** prend dans l'enrichissement actuel :
  - la fin de chaque corps et ses lignes source ;
  - le commentaire au-dessus d'un corps ;
  - les variables de module et les corps qui les lisent ou les écrivent ;
  - les modules Python importés sous un alias ;
  - les champs passés par mot-clé au constructeur ;
  - les valeurs écrites dans deux langages ;
  - les documents et leurs citations.

  La notion de texte affiché reste dans le cœur, mais le motif de l'appel qui affiche un texte (chez Grid Zero, `I18n.t` et `I18n.tn`) vient de la configuration de l'hôte.
- **Le lecteur GDScript** prend les constantes de `preload` et leur résolution vers le script préchargé.
- **L'extension locale de Grid Zero** prend :
  - les branches de commande du serveur (aujourd'hui lues dans le lecteur Python), les ordres que le client envoie au serveur (aujourd'hui dans le lecteur GDScript) et la vérification des ordres inconnus du serveur ;
  - les champs de l'état envoyé au client et les clés que le GDScript en lit ;
  - les `"action"` postées par le GDScript vers les actions PHP ;
  - les conseils de scénario ;
  - le journal moonshot.

  Les ids des nœuds restent ceux d'aujourd'hui (`simulation_server_cmd_…`, `conseil_…`, etc.).
- **Les programmes externes.** Chaque lecteur qui lance un programme a sa section dans `graphe.toml`, avec une clé `executable`. L'ordre de recherche est : `graphe.toml`, puis le PATH, puis rien. Sans programme, le lecteur continue avec un avertissement qui nomme la clé, et les appels qu'il aurait résolus restent non résolus.
- **Les documents.** Ce sont tous les `.md` par défaut, restreints par une liste de motifs dans `graphe.toml`. Un document cite un nœud qu'il nomme entre accents graves, et un autre document par un identifiant au motif configurable (`T-\d{4}` par défaut). Le code qui contient un identifiant de document cite ce document. Grid Zero restreint sa liste aux tickets, pour garder son graphe ; le journal moonshot passe par son extension.
- **Fraîcheur.** Le graphe est périmé si un fichier de l'hôte ou un fichier de l'outil est plus récent que lui. `installer` pose les crochets post-commit, post-merge, post-checkout et post-rewrite, et ajoute le dossier de sortie au `.gitignore`.
- **Grid Zero** garde un `tools/graphe.py` réduit, qui transmet ses arguments à la commande `graphe`. Ses crochets git, son README et ses mémoires continuent de marcher.
- **Les lecteurs JS/TS** reposent sur tree-sitter : un seul lecteur pour `.js`, `.mjs` et `.ts`, plus le bloc `<script>` des `.svelte`. Les appels sont résolus par le nom et par les imports. Le choix des grammaires (un paquet commun ou un paquet par langage) se fait au ticket du lecteur.
- **La langue.** L'extraction et les étapes 2 et 3 restent en français. Une étape dédiée passe tout en anglais (commandes, clés, champs du JSON, sortes de nœuds, code, documentation, glossaire), en même temps que Grid Zero, ses mémoires et son README.
- **Les étapes.** Chacune est vérifiable seule :
  1. extraction à comportement identique ;
  2. configuration, contrat `contribuer` et extension locale de Grid Zero ;
  3. documents généralisés ;
  4. passage à l'anglais ;
  5. lecteur JS (dpe) ;
  6. TypeScript et Svelte (4cast).
- **Le backlog et la skill.** Le fichier des manques devient le backlog unique de l'outil, et chaque entrée nomme son hôte. Une skill Claude Code, livrée dans le dépôt et installée une fois pour le compte, remplace les deux mémoires « graphe » de Grid Zero.

## Décisions de test

- **Un bon test vérifie le comportement observable** : le `graphe.json` et le texte d'une requête, ou la contribution rendue. Jamais la structure interne d'un lecteur.
- **Les trois points de test, validés par l'utilisateur :**
  1. **La commande `graphe` sur un mini-projet hôte témoin**, un par langage (Python, GDScript, PHP, JS, TS/Svelte), plus un projet sans configuration et un projet avec documents. Le test lance `construire`, puis `expliquer`, `appelants`, `chemin` et `chercher`, et vérifie le JSON et le texte. C'est le point principal.
  2. **`contribuer(projet)`**, pour tester un lecteur ou une extension isolément. `test_graphe.py` de Grid Zero y tient déjà : il appelle la lecture Python directement, sur des sources écrites dans un dossier temporaire. Il part dans le dépôt de l'outil et passe sans modification de ses assertions.
  3. **Le test de référence, dans Grid Zero.** Son `graphe.json` est comparé à un instantané, sans l'horodatage ni le commit. L'instantané est pris *après* l'introduction du tri des nœuds et des liens. On vérifie alors une fois, à la main, que la différence avec le graphe produit avant l'extraction se limite à la numérotation des communautés. Le test tient jusqu'au passage à l'anglais, qui le reprend avec les noms traduits.
- **La vérification des lecteurs** (`graphe verifier`) reste un test de couverture sur chaque hôte. Grid Zero garde son seuil.
- **Le seuil de régression sur dpe et 4cast** : aucun, au départ. Le premier passage établit une couverture de référence, notée dans le ticket du lecteur.

## Hors du périmètre

- Le compilateur TypeScript et la résolution des appels par les types (ADR 0002). On n'y passe que sur preuve d'appels manqués.
- Un lecteur XML. Le XML de dpe, ce sont des données.
- Les fichiers de traduction `.po` et les tests qui comparent un message entier : ils restent hors du graphe, comme aujourd'hui.
- La publication : nom définitif, licence, PyPI, documentation pour des inconnus, et toute plateforme autre que Windows.
- Reprendre l'historique git de Grid Zero.
- Un tracker distant pour l'outil.

## Notes

- Le motif `T-\d{4}` par défaut sert déjà trois hôtes : Grid Zero, dpe et l'outil lui-même. 4cast nomme ses issues autrement : son `graphe.toml` donnera son motif.
- **Risque de l'étape 2 :** déplacer les branches de commande hors du lecteur Python oblige l'extension à relire `server.py` par l'`ast`. Le test de référence dira si les ids et les liens `dispatches` sont restés les mêmes.
- **Risque de l'étape 4 :** le passage à l'anglais touche le JSON lu par `graphe.html` et les mémoires de Grid Zero qui citent les commandes françaises. Il faut migrer les mémoires dans la même étape.
- Les décisions de l'entretien sont dans les ADR 0001 et 0002, et le vocabulaire dans `GLOSSARY.md`.

## Comments

**2026-11-17, après T-0002.** Le test de référence compare le graphe d'un arbre figé (l'étiquette `graphe-reference` de Grid Zero), pas celui de l'arbre de travail, qui change à chaque commit et contient l'outil lui-même. Le tri a changé la partition des communautés, pas seulement leur numérotation : l'instantané pris après le tri fait foi. Les dépendances de l'outil comprennent scipy (la disposition des grands graphes).

**2026-11-18, après T-0010.** L'instantané de Grid Zero est repris une seconde fois, avant le passage à l'anglais. Un document cite un ticket par son identifiant, et Grid Zero garde ses tickets pour documents : ses tickets se citent donc entre eux, quelle que soit la restriction. Restreindre aux tickets ne garde donc pas tout le graphe. La différence, vérifiée à la main : 1902 liens `cite` d'un ticket à un autre, et les positions (x, y) des 379 tickets. Aucune communauté du code ne change. Sur décision de l'utilisateur, le nouvel instantané (Grid Zero, T-0387) fait foi.

**2026-11-18, après T-0011.** L'instantané de Grid Zero est repris une troisième fois, avec les noms anglais (Grid Zero, T-0388). L'ancien, traduit par la table de correspondance de T-0011, est identique au nouveau : 258 ids renommés (`value_`, `hint_`, `_constant`), aucune communauté ni position changée. Le test de référence vaut de nouveau, désormais pour les noms anglais.
