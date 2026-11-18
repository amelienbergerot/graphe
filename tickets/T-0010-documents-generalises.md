Status: closed
Type: task
Part of: T-0001
Blocked by: T-0007
Created: 2026-11-17

# T-0010 : Documents généralisés

## Ce qu'il faut construire

Tous les fichiers Markdown de l'hôte sont des documents par défaut, et `graphe.toml` peut les restreindre par une liste de motifs. Un document cite un nœud qu'il nomme entre accents graves, et un autre document par un identifiant dont le motif est configurable (celui des tickets `T-` suivi de quatre chiffres par défaut). Le code qui contient un identifiant de document cite ce document. Grid Zero restreint sa liste à ses tickets. L'outil se lit lui-même, tickets compris : c'est son troisième hôte.

## Critères d'acceptation

- [x] `graphe expliquer` sur une fonction de ce dépôt nomme le ticket qui la cite.
- [x] Un mini-projet témoin avec un motif d'identifiant à lui relie ses documents entre eux.
- [x] Le test de référence de Grid Zero passe.

## Comments

**2026-11-18, fait.**

- Les documents : les `.md` de l'hôte (ceux que git suit, moins `exclure`), restreints par `[documents] motifs`, une liste de motifs comme `exclure`. Un document dont le nom de fichier commence par un identifiant (`[documents] identifiant`, une expression régulière, `\bT-\d{4}\b` par défaut) est un ticket, d'id `ticket_<identifiant>` (`ticket_t_0010`, comme avant). Les autres sont des nœuds `document` (`document_readme_md`), dans leur propre communauté, `documents` (`A_PART`). Une section `[documents]` invalide (motif qui ne compile pas, `motifs` qui n'est pas une liste) arrête la construction avec un message qui nomme la clé.
- Les citations :
  - le code qui contient un identifiant, dans son corps ou son commentaire, cite le ticket (`cite`, comme avant) ;
  - un document qui contient un identifiant cite le ticket (`cite`, nouveau ; pas de soi à soi) ;
  - un document nomme les fonctions qu'il écrit entre accents graves (`nomme`, comme avant pour les tickets, et désormais pour tout document).
- Grid Zero (son T-0387) restreint ses documents à `tickets/T-[0-9][0-9][0-9][0-9]*.md`, l'ancien glob.
- **Écart avec T-0001 : l'instantané de Grid Zero est repris.** Les tickets se citent maintenant entre eux, quelle que soit la restriction. La différence, vérifiée à la main avant la reprise :
  - 1902 liens `cite` en plus, chacun d'un ticket vers un autre ;
  - les positions (x, y) des 379 tickets, qui changent parce que leur communauté à part a maintenant des liens.

  Aucune communauté du code ne bouge. Le nouvel instantané fait foi, sur décision de l'utilisateur. `graphe verifier` dans Grid Zero rend 0.
- Ce dépôt est son troisième hôte, sans `graphe.toml` : `graphe expliquer _sources` montre `cite T-0009` et `nomme` par T-0006 et T-0009.
- Tests :
  - `test_un_hote_avec_son_motif_d_identifiant_relie_ses_documents` (`ISSUE-\d+`) ;
  - `test_sans_configuration_tout_markdown_est_un_document` (`chercher`, `chemin`, `expliquer`) ;
  - `test_une_section_documents_invalide_arrete_la_construction`.

  `enrichir` lit maintenant les documents par git : les tests du cœur posent un `git init` (`_enrichir`).
- Restent, avec leur `shortcut:` :
  - deux fichiers au même identifiant : le second n'est qu'un document ;
  - deux chemins qui ne diffèrent que par la ponctuation font un seul nœud.
- L'identifiant d'un document vient de son nom de fichier, pas de son en-tête (`id:`). C'était déjà la règle des tickets de Grid Zero.
