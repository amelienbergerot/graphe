Status: closed
Part of: T-0071
Created: 2026-11-27

# T-0074: The cause of an unattributed call

## What to build

`explain` and `callers` say "+ N calls named `f` the graph could not attribute: grep them", a count only. The agent cannot tell a name two classes share, where a grep settles it, from a common name, where a grep returns hundreds of lines.

The answer groups the unattributed calls of the name by cause (GLOSSARY.md, Unattributed call): several definitions bear the name, with the candidates when they are five at most, each designated as the agent would type it; a common name; a receiver of unknown type; a definition outside the host. The build already gives each call site a verdict: the stored counts become counts per cause. This changes the graph's shape (CHANGELOG.md, **Contract**).

## Acceptance criteria

- [x] On a host where a name has two definitions, `explain` names the cause and both candidates.
- [x] Above five candidates, their count only.
- [x] A common name, a receiver of unknown type and a definition outside the host each give their own cause.
- [x] A name without unattributed calls prints no line, as today.
- [x] The skill's text says what each cause means for the next step (grep, or query a candidate).
- [x] CHANGELOG.md notes the stored counts' new shape under **Contract** for the next release.

## Blocked by

None (can start immediately).

## Comments

- 2026-11-27: done. `graphe.json`'s `unattributed` is `{name: {cause: count}}`, the causes `several`, `common`, `receiver`, `outside`, from each site's verdict (`cli.CAUSES`). `_missed` prints a count per cause; the candidates are worked out at query time (the function and method nodes of that bare name), by `_designation`, five at most. Two shortcuts noted in the code: Python's unresolved bare `f()` counts as a receiver of unknown type; the candidates cross languages. Tests in `tests/test_host.py` (Python for several, receiver, outside and above five; Ruby's `each` for a common name).
