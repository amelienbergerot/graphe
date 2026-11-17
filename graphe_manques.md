# Ce que le graphe n'a pas su dire

Le backlog unique de l'outil, pour tous ses hôtes. Chaque fois que `graphe`
ne suffit pas et qu'une recherche se fait à la main (grep, sed, lecture), une
entrée ici : l'hôte, ce qu'on cherchait, ce que le graphe a répondu, comment
on l'a trouvé. De quoi améliorer l'outil dans un second temps (demande de
l'utilisateur, 2026-11-02).

Une entrée réglée passe dans « Réglé », avec le commit. Les entrées réglées
avant T-0003 viennent de Grid Zero, et leurs commits sont les siens.

## Ouvert

- **Les fichiers de traduction sont hors du graphe.** (Grid Zero, 2026-11-02)
  - `godot/i18n/*.po` se lisent par grep. C'est sans doute à garder ainsi :
    `tools/i18n.py etat` dit déjà ce qui manque.
- **Une question « où marche X » demande un banc, pas une requête.**
  (Grid Zero, 2026-11-02, prévisionniste) Pour savoir dans quels scénarios l'aide
  agit, il a fallu jouer chaque scénario. Le graphe dit qui lit
  `PREVISIONNISTE`, pas quelles données le rendent actif (une fenêtre
  météo qui contient des incidents de ligne). À garder hors du graphe.
- **Les tests qui comparent un message entier** restent hors du graphe.
  (Grid Zero) Les tests en sont exclus.

## Réglé

Réglées ensemble (2026-11-05, T-0354) :

- **Une valeur échangée entre les deux langages.** (T-0351) `"coupee"`,
  écrit par `InterconnectionFleet.settle_severed` et comparé par
  `texte_d_interconnexion` ; `"reparer_liaison"`, du fil de la partie au
  débrief. Un nœud `valeur` par chaîne écrite en Python et en GDScript :
  `chercher coupee`, `expliquer '"coupee"'`. Couvre aussi les clés des
  autres messages (`"tiree"`, `"defi"` du catalogue).
- **Un champ écrit par mot-clé.** (T-0351) `EngineState(...,
  interconnection_unavailable_reason=...)` : `Engine.step` l'écrit.
- **Les conseils des scénarios.** (T-0337) Un nœud `conseil` par
  `[[hints]]`, relié aux fonctions dont il cite le texte entre « ».
- **Le journal du Moonshot.** Un nœud par itération, relié aux tickets
  qu'elle cite (« T-0350 à T-0352 » compris).

Réglées ensemble (2026-11-03, commit « graphe : champs, clés de l'état,
alias d'import, tickets ») :

- **Une classe a son étendue, et ses champs sont des nœuds.**
  `expliquer GenSpec --source` imprime la classe ; `expliquer
  EtatDeJeu.manque_prevu_tranche` dit qui l'écrit (`_prevoir_le_manque`)
  et qui le lit, côté Python quand le type du récepteur est connu.
- **Les clés de l'état mènent au client.** `state.get("demand_mw")` ou
  `state["demand_mw"]` dans un script GDScript lit le champ (par le nom) :
  le champ `manque_prevu_tranche` mène à `_manque_prevu_text`.
- **Un alias d'import Python est sûr.** `aides_de_camp.PREVISIONNISTE`
  lit la constante de `simulation/game/aides.py` en EXTRACTED.
- **Les tickets sont des nœuds.** Le code qui cite `T-0307` y mène par
  `cite` ; un ticket mène par `nomme` aux fonctions qu'il écrit entre
  accents graves. `expliquer _rafales` dit T-0307 et T-0328. Ils forment
  leur propre communauté, pour ne pas fondre celles du code.

- **Les accents sortaient en « D?fi » quand un programme lit la sortie.**
  (2026-11-02, T-0310) `expliquer envoyer_defi` affichait « D�fi du
  jour » : Python écrit en cp1252 dans un tube. La sortie passe en UTF-8
  hors d'un terminal.

- **Un `X.nom` Python lisait une variable GDScript.** (2026-11-02,
  tempête) `expliquer ecrire_le_catalogue` disait qu'il lit `graine` de
  `godot/menu/fond_menu.gd` « par le nom », pour un `examen.graine`. Le
  lien par le nom reste désormais dans son langage.

Réglées ensemble (commit « graphe : variables, source, PHP, textes et
commentaires ») :

- **Les variables et constantes de module ne sont pas des nœuds.** Nœuds
  `variable` et `constante`, liens `lit` et `ecrit` ; `expliquer _tirage`
  dit qui l'écrit et qui le lit.
- **Le graphe dit où est le code, pas ce qu'il contient.** Chaque corps a
  sa ligne de fin ; `expliquer X --source` imprime ses lignes.
- **`chercher` prend un nom, pas une ligne de code.** `def`, `func`,
  `class`, `function`, `const` et `var` en tête sont retirés.
- **Le PHP du service en ligne est hors du graphe.** `tools/graphe_php.py` :
  fonctions, actions, appels ; les `{"action": ...}` du client mènent aux
  actions par `sends`.
- **Un nom écrit par sa constante de preload n'est pas reconnu.**
  `appelants Progress.record` trouve `godot/settings/progress.gd`.
- **Un texte affiché ne mène pas à son code.** Les textes de `I18n.t`
  sont rangés sur leur fonction ; `chercher "Réseau stable"` mène à
  `_update_ui_from_state`.
- **Un concept dit en français dans les commentaires ne se trouve pas.**
  Le commentaire au-dessus de chaque fonction est rangé sur elle ;
  `chercher clarte` trouve les fonctions de la lumière du jour.
