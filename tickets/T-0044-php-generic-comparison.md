Status: ready-for-agent
Type: task
Created: 2026-11-19

# T-0044: PHP read by the generic reader, compared with the PHP reader on 4cast

## What to build

A PHP entry of the generic reader, data only (its grammar, our queries in the capture convention, its common names), is built and compared on 4cast with the existing PHP reader, which reads by patterns. The entry is not put in the readers' registry: the PHP reader stays the one hosts get. The ticket ends on the user's decision: replace the PHP reader by the generic entry only if the generic one does at least as well, or keep it. BACKLOG.md: "PHP's pattern reader may be worse than the generic one".

## Acceptance criteria

- [ ] The PHP `Language` is data only; its grammar pinned; a test at `read(language, file, source)` on a snippet: functions, methods `Class.method`, a top-level call owned by its file (as the PHP reader does since T-0023).
- [ ] Both readers run on 4cast's PHP: nodes, links by confidence, `check` coverage (linked, by name, not attributed, external), and three `explain` or `callers` queries compared with grep, side by side in this ticket's comments. protobuf's PHP as a second measure.
- [ ] What each reader finds that the other misses, named with examples.
- [ ] The user's decision noted in this ticket, and the BACKLOG.md entry settled or updated; if the generic entry replaces the PHP reader, that change is its own ticket.
- [ ] The existing hosts' graphs unchanged; the tests pass.

## Blocked by

None (can start immediately).

## Comments
