# Issue tracker: GitHub Issues, in the graphe Project

This repository's tickets are the issues of `amelienbergerot/graphe`, each in the Project [graphe](https://github.com/users/amelienbergerot/projects/1). Use `gh` (`-R amelienbergerot/graphe` outside a clone).

`tickets/` holds T-0001 to T-0093 as they were migrated (2026-11-27), issue #N for T-000N. It is an archive: never edit it, never add to it. The graph still reads it as documents until it reads the issues themselves; until then a new ticket is not in the graph.

## Conventions

- The identifier is `T-NNNN` (pattern `T-\d{4}`, the one the graph's documents recognise), first in the title: `T-0094: The graph reads the GitHub issues`. To cite a ticket, in code, a commit or another ticket, write its identifier, for example `T-0012`.
- `T-NNNN` is not the issue number: pull requests share GitHub's numbering, so from T-0094 on they drift apart. Find a ticket by its identifier: `gh issue list --state all --search "T-0094 in:title"`.
- Next number: the largest `T-NNNN` among the issue titles, plus one: `gh issue list --state all --limit 1000 --json title --jq '.[].title'`.
- Every ticket is assigned to `amelienbergerot`, has an issue type (`Task`, `Bug` or `Feature`: a spec or a ticket on its own is a `Feature`, a child of a spec a `Task`) and one theme label: `architecture`, `readers`, `core`, `cli`, `performance`, `agents`, `distribution`, `tests`, `documentation`.
- The triage state is a label (values in `triage-labels.md`); a closed ticket has none, but `wontfix`.
- A spec is a ticket like any other. Its implementation tickets are its sub-issues (`gh issue edit N --parent M`).
- Blocking is GitHub's own relation: `gh issue edit N --add-blocked-by M,P`.
- Exchanges are issue comments: `gh issue comment N --body-file f`.
- Closing: `gh issue close N --comment "..." --reason completed` (or `--reason "not planned"` with the `wontfix` label). The work itself goes through a pull request whose body says `Closes #N`: the merge closes the issue.

The Project's Status (Todo, In Progress, Done): an item is set by hand when added, `gh project item-edit --project-id PVT_kwHOAMyx6s4Bthxc --field-id PVTSSF_lAHOAMyx6s4Bthxczhrq130 --id <item> --single-select-option-id <option>`, with Todo `f75ad846`, In Progress `47fc9ee4`, Done `98236657`; the item id is what `gh project item-add` returns (`--format json`).

## When a skill says "publish to the issue tracker"

Write the body to a file (the title is not repeated in it), then:

```
gh issue create --title "T-NNNN: <title>" --body-file <file> --assignee amelienbergerot --type <type> --label <theme> --label <triage> --project graphe
```

then the parent and the blockers if any, and the Project's Status to Todo.

## When a skill says "fetch the relevant ticket"

`gh issue view N --comments`, N found from the identifier as above. The user normally gives the identifier, the number or the URL. T-0001 to T-0093: `tickets/T-NNNN-*.md` holds the same text.

## Wayfinding operations

Used by `/wayfinder`. The map and its children are all issues.

- **Map**: a `Feature` with the label `map`, with the sections Notes / Decisions-so-far / Fog.
- **Child ticket**: a sub-issue of the map, a `Task` with the label of its kind (`research`/`prototype`/`grilling`, none for a task), the question in the body.
- **Blocking**: GitHub's "blocked by". The ticket is unblocked when each blocker is closed.
- **Frontier**: the map's sub-issues still open, unblocked and not In Progress. The smallest identifier goes first.
- **Claim**: the Project's Status to In Progress, before any work.
- **Resolve**: the answer as a comment headed `## Answer`, the issue closed, then a pointer (summary + identifier) in the map's Decisions-so-far.
