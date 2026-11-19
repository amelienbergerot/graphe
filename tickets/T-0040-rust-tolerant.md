Status: ready-for-agent
Type: task
Created: 2026-11-19

# T-0040: Rust reads a file with an error node

## What to build

A Rust file the grammar rejects in part (`tree-sitter-rust` 0.24.2 refuses a lifetime first in a trait object, `Box<dyn 's + FnOnce(..)>`) is read for its valid part instead of being skipped whole, as C/C++ does since T-0034 (`Language.tolerant`): data only (ADR 0003). On libsignal, 1 of 612 Rust files is skipped today. BACKLOG.md: "A Rust file with `dyn 'a + Trait` is skipped whole".

## Acceptance criteria

- [ ] Rust's `Language` is `tolerant`; a test at `read(language, file, source)` on a snippet with `dyn 'a + Trait`: the definitions and calls outside the error are read, with their owner.
- [ ] The definitions under an error node checked on libsignal: no garbage name.
- [ ] libsignal, at its pinned commit, builds with no dangling link; its Rust `check` coverage before and after, and the definitions of the file once skipped found by `explain`, noted in this ticket's comments.
- [ ] Rust's section of the readers document, the README's libsignal row if a measure in it moves, and the BACKLOG.md entry updated.
- [ ] The tests pass.

## Blocked by

None (can start immediately).

## Comments
