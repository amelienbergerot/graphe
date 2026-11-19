Status: closed
Type: task
Created: 2026-11-19

# T-0039: Go reads a file with an error node

## What to build

A Go file the grammar does not fully understand (Go 1.26's `new(expr)`, generic methods `func (f *Flash) Error[T ...]`) is read for its valid part instead of being skipped whole, as C/C++ does since T-0034 (`Language.tolerant`): data only, no code of Go's own (ADR 0003). On gitea, 47 of 3199 Go files are skipped today, 15 outside the tests; a definition there is lost everywhere (`ctx.ServerErrorAuto` is `external` at its 1226 calls). BACKLOG.md: "A Go file in Go 1.26's syntax is skipped whole".

## Acceptance criteria

- [x] Go's `Language` is `tolerant`; a test at `read(language, file, source)` on a snippet in Go 1.26's syntax: the definitions and calls outside the error are read, with their owner.
- [x] The definitions under an error node checked on gitea: no garbage name (as T-0034 did for C/C++'s macros); a name the grammar inserts to recover is skipped.
- [x] gitea, at its pinned commit, builds with no dangling link; its Go `check` coverage before and after, its build time, and `explain ctx.ServerErrorAuto` and `DecodeJSON`'s callers compared with grep, noted in this ticket's comments.
- [x] Go's section of the readers document, the README's gitea row and the BACKLOG.md entry updated (the entry settled, or what remains).
- [x] The tests pass.

## Blocked by

None (can start immediately).

## Comments

- **The change** (2026-11-19): `GO` is `tolerant`, data only (ADR 0003's amendment names Go). Tested at `read()` on a snippet with a generic method and `new(int64(1))`: the class and the two functions around them are read, their calls with their owner; the generic method is lost in its error node, its call the file's. The skip path stays tested at `contribute()`, by Go with `tolerant=False`.
- **The definitions under an error node** (gitea, a script over the 47 files): 450 definitions, 61 of them touching an error node (7 inside an `ERROR`, the others in a definition holding one), all real names (`TestLockAndDo`, `getExpectedContentsResponseForContents`); no definition nested in another by the error, so no owner taken from a wrong extent. A name the grammar inserts to recover is skipped by the shared `is_missing` check (T-0034); none on gitea. The 7 generic methods (`Flash.Error`, `Warning`, `Info`, `Success`, `Context.JSONError`, `JSONErrorWithField`, `RenderWithErrDeprecated`) are no nodes; their calls are their file's, nothing made up in their place (`string(..)`, `f.set`, `ctx.JSON`).
- **gitea** (`c376d5d`): 23878 -> 24375 nodes (+47 files, 320 functions, 81 methods, 49 classes; none lost), 63819 -> 67195 links, 0 dangling, no file skipped.
- **Coverage** (`graphe check`, go): 155575 -> 164275 sites; `ours?` 52902 -> 58121, `external` 51542 -> 52143, `ambiguous` 27174 -> 29123, `common` 23957 -> 24888. `ctx.ServerErrorAuto` leaves `external` (1226) for `ours?` (1234). 353 links by name are gone, all to a name a once-skipped file defines a second time: `Router.NotFound` 142 (`ctx.NotFound` calls, wrongly linked to the router's), `Repository.GetCommit` 82 and `GetBranchCommit` 50 (`TemporaryUploadRepository`'s), `RenderedIconPool.RenderToHTML` 17 (`Context.RenderToHTML`), and 14 smaller.
- **Two queries against grep** (bytes of the answer; grep over the `.go` files):
  - `explain Context.ServerErrorAuto` (`ctx.ServerErrorAuto` names no node: the receiver's variable is no type): before, no node; now 562 callers by name, 1937 bytes; grep `ServerErrorAuto(`: 1245 lines in 151 files, 81718 bytes.
  - `callers DecodeJSON`: 223 then 268 callers at level 1 (77 then 90 at level 2), 18490 bytes; its sites 533 -> 688, the 155 grep found in skipped files; grep `DecodeJSON(`: 689 lines in 134 files, 74180 bytes.
- **The README's query**: `explain GetRepositoryByID`, 72 -> 76 callers by name (4 in once-skipped files), 1778 bytes; grep `GetRepositoryByID(` (`grep -rnF`, which prefixes `./`): 80 lines in 63 files, 7973 bytes. The row updated.
- **Build time** (gitea, warm, alternating HEAD's tool and this one, by a HEAD worktree first on `PYTHONPATH`): 72.9 / 58.9, 53.4 / 57.2, 58.3 / 51.8 s; medians 58.3 s and 57.2 s: no difference measured. The machine is slower than T-0031's (31.4 s then): the README's time is left as it is, not to mix two machines' states.
- **What it misses** (BACKLOG.md, the entry rewritten to what remains): the 7 generic methods. Said in Go's section: the same, as a `shortcut:`.
- **The documents**: Go's section in `docs/readers.md` (`tolerant` a quirk, the generic methods a limit; Go in the `tolerant` lines), gitea in `docs/sample-hosts.md`, ADR 0003's amendment, gitea's README row, the `read()` comment that named gitea.
- **The review** (2026-11-19, standards and spec): the limits in `shortcut:` in the code too, above `tolerant=True` as Swift's (a generic method lost, a Go file that does not parse no longer named on stderr), and the latter in Go's section; the `tolerant` quirk cut to one sentence, its measures here; "their callers `external`" corrected, checked on the graph: `f.Error` is `common`, `Info` `ambiguous`, `Success` linked to gitea's other `Success` (a wrong link), `Warning` and the three `Context` ones `external`; the settled half of the BACKLOG.md entry in Settled, the neighbouring Go entry's figures refreshed (29123 `ambiguous`, 24888 `common`, 58121 linked). Left as they are: the README's build time (see above); no Go test of a name the grammar inserts (the shared `is_missing` check, tested on C++ by T-0034; none on gitea).
- **Not checked**: re-running the other hosts (no `.go` in Grid Zero, dpe, 4cast, cadastre-poc, the tool, libsignal; protobuf's 4 `.go` files all parse, so its graph is unchanged by construction).
