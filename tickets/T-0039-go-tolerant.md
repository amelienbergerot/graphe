Status: ready-for-agent
Type: task
Created: 2026-11-19

# T-0039: Go reads a file with an error node

## What to build

A Go file the grammar does not fully understand (Go 1.26's `new(expr)`, generic methods `func (f *Flash) Error[T ...]`) is read for its valid part instead of being skipped whole, as C/C++ does since T-0034 (`Language.tolerant`): data only, no code of Go's own (ADR 0003). On gitea, 47 of 3199 Go files are skipped today, 15 outside the tests; a definition there is lost everywhere (`ctx.ServerErrorAuto` is `external` at its 1226 calls). BACKLOG.md: "A Go file in Go 1.26's syntax is skipped whole".

## Acceptance criteria

- [ ] Go's `Language` is `tolerant`; a test at `read(language, file, source)` on a snippet in Go 1.26's syntax: the definitions and calls outside the error are read, with their owner.
- [ ] The definitions under an error node checked on gitea: no garbage name (as T-0034 did for C/C++'s macros); a name the grammar inserts to recover is skipped.
- [ ] gitea, at its pinned commit, builds with no dangling link; its Go `check` coverage before and after, its build time, and `explain ctx.ServerErrorAuto` and `DecodeJSON`'s callers compared with grep, noted in this ticket's comments.
- [ ] Go's section of the readers document, the README's gitea row and the BACKLOG.md entry updated (the entry settled, or what remains).
- [ ] The tests pass.

## Blocked by

None (can start immediately).

## Comments
