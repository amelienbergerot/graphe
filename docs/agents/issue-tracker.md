# Issue tracker : tickets Markdown locaux

Les tickets de ce dépôt sont des fichiers Markdown dans `tickets/` à la racine. Pas de tracker distant, pas de GitHub Issues. Le graphe lit ces fichiers comme des documents : un ticket en cite un autre par son identifiant.

## Conventions

- Un fichier par ticket : `tickets/T-NNNN-titre-court.md` (quatre chiffres, puis le titre en kebab-case, comme dans Grid Zero).
- L'identifiant est `T-NNNN` (motif `T-\d{4}`, celui que les documents du graphe reconnaissent). Pour citer un ticket, écrire son identifiant, par exemple `T-0012`.
- Numéro suivant : le plus grand numéro présent dans `tickets/`, plus un. Créer le dossier s'il n'existe pas.
- Une spec est un ticket comme un autre. Ses tickets d'implémentation la citent par une ligne `Part of: T-NNNN` en tête.
- L'état de triage est une ligne `Status:` en tête du fichier (valeurs dans `triage-labels.md`).
- Les échanges s'ajoutent en bas du fichier, sous un titre `## Comments`.
- Fermer : ajouter un dernier commentaire, puis passer `Status:` à `closed`.

## When a skill says "publish to the issue tracker"

Créer `tickets/T-NNNN-titre-court.md` avec le numéro suivant.

## When a skill says "fetch the relevant ticket"

Lire `tickets/T-NNNN-*.md`. L'utilisateur donne normalement l'identifiant ou le chemin.

## Wayfinding operations

Used by `/wayfinder`. La carte et ses enfants sont tous des tickets de `tickets/`.

- **Map** : un ticket `Type: map`, avec les sections Notes / Decisions-so-far / Fog.
- **Child ticket** : un ticket avec `Part of: T-<carte>` et `Type:` (`research`/`prototype`/`grilling`/`task`), la question dans le corps. `Status:` passe à `claimed`, puis `resolved`.
- **Blocking** : une ligne `Blocked by: T-NNNN, T-NNNN` en tête. Le ticket est débloqué quand chaque ticket listé est `resolved`.
- **Frontier** : les enfants de la carte encore ouverts, débloqués et non réclamés. Le plus petit numéro passe en premier.
- **Claim** : `Status: claimed`, enregistré avant tout travail.
- **Resolve** : la réponse sous `## Answer`, `Status: resolved`, puis un renvoi (résumé + identifiant) dans le Decisions-so-far de la carte.
