Status: closed
Type: task
Part of: T-0001
Blocked by: T-0011
Created: 2026-11-17

# T-0012: Code and documentation in English

## What to build

The internal identifiers, the docstrings, the comments, the ADRs, the glossary and the open tickets switch to English. No change of behaviour.

## Acceptance criteria

- [x] Grid Zero's graph is identical to T-0011's snapshot.
- [x] The glossary and the ADRs are in English, with the same decisions.
- [x] The tests pass.

## Comments

**2026-11-18, done.** The correspondence table, for whoever reads the tool's internals (Grid Zero's extension, the closed tickets):

| What changes | Before → after |
|---|---|
| Modules | `graphe_enrichir` → `graphe_core`, `graphe_racine` → `graphe_root` (`graphe`, `graphe_python`, `graphe_godot`, `graphe_php` stay) |
| Files | `graphe_manques.md` → `BACKLOG.md`; the ADRs `0001-one-tool-local-extensions.md`, `0002-tree-sitter-for-new-readers.md`; the open tickets T-0001, T-0012, T-0013, T-0014; `tests/test_hote.py` → `test_host.py`, `test_racine.py` → `test_root.py` |
| `graphe_root` | `RACINE`, `SORTIE` → `ROOT`, `OUTPUT`; `racine()`, `fichiers()`, `designe()` → `root()`, `files()`, `designates()` |
| `graphe_core` | `CORPS` → `BODIES`, `_commentaire` → `_comment`, `enrichir` → `enrich`, `etendue` → `extent`, `lignes_sans_commentaires` → `lines_without_comments`, `motif_des_textes` → `displayed_text_pattern` |
| `graphe_godot.Script` | `chemin`, `texte`, `masque`, `lignes`, `englobante`, `fonctions`, `signaux`, `anonymes` → `path`, `text`, `masked`, `lines`, `enclosing`, `functions`, `signals`, `anonymous`; `ligne_de`, `chaine_a` → `line_of`, `string_at`; `masquer` → `mask` |
| Readers | `graphe_python.Lecture`, `graphe_php.Lecture`, `graphe_godot.Extraction` → `Reader` (`noeuds`, `liens` → `nodes`, `links`); `Fonction`, `Classe` → `Function`, `Class`; `graphe_php.id_d_action` → `action_id` |
| `graphe` | `Projet` → `Project`, `assembler` → `assemble`, `construire` → `build`, `verifier` → `check`, `installer` → `install`, `charger` → `load`, `trouver` → `find`, `recherche` → `search_nodes`, `chercher` → `search`, `chemin` → `path` (`sans_sens` → `undirected`), `expliquer` → `explain`, `appelants` → `callers`, `communautes` → `communities`, `disposer` → `layout`, `rapport` → `report` |

- The check: each translated Python file has the same AST as before, docstrings aside, up to the renamed identifiers (one old name, one new name in each scope); the only strings that change are internal tags (`graphe_python`'s type tags, the keys of a reader's own sites, `__DONNEES__` of the page) and the page's CSS and JavaScript names (`node --check`). The fixtures' host code stays as it was.
- Grid Zero's graph: `graphe_reference.py comparer` says « identique a l'instantane »; `graphe check` exits 0; `simulation/tests/test_graphe.py` passes. Grid Zero's extension follows the renamed imports (`BODIES`, `_comment`, the `Script` attributes), its `tools/README.md` and its memory cite `BACKLOG.md` (Grid Zero, T-0389).
- Stay as they were: the host data (labels, comments, displayed texts, the fixtures' sources), the `# >>> graphe du code` block that `install` recognises, the closed tickets.
