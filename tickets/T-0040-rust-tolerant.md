Status: closed
Type: task
Created: 2026-11-19

# T-0040: Rust reads a file with an error node

## What to build

A Rust file the grammar rejects in part (`tree-sitter-rust` 0.24.2 refuses a lifetime first in a trait object, `Box<dyn 's + FnOnce(..)>`) is read for its valid part instead of being skipped whole, as C/C++ does since T-0034 (`Language.tolerant`): data only (ADR 0003). On libsignal, 1 of 612 Rust files is skipped today. BACKLOG.md: "A Rust file with `dyn 'a + Trait` is skipped whole".

## Acceptance criteria

- [x] Rust's `Language` is `tolerant`; a test at `read(language, file, source)` on a snippet with `dyn 'a + Trait`: the definitions and calls outside the error are read, with their owner.
- [x] The definitions under an error node checked on libsignal: no garbage name.
- [x] libsignal, at its pinned commit, builds with no dangling link; its Rust `check` coverage before and after, and the definitions of the file once skipped found by `explain`, noted in this ticket's comments.
- [x] Rust's section of the readers document, the README's libsignal row if a measure in it moves, and the BACKLOG.md entry updated.
- [x] The tests pass.

## Blocked by

None (can start immediately).

## Comments

- **The change** (2026-11-19): `RUST` is `tolerant`, data only (ADR 0003's amendment names Rust). Tested at `read()` on a snippet with `Box<dyn 's + FnOnce() -> u8>` in a method's signature: every definition is read, that method too, each call with its owner. The skip path stays tested at `contribute()` by Go with `tolerant=False` (T-0039).
- **The definitions under an error node** (libsignal, `rust/bridge/shared/types/src/net/tokio.rs`): one error node, the `'` of `dyn 's` (L161, one byte), holding no definition; the one around it, `TokioAsyncContext.run_future_boxed`, is a real name. The file's 20 definitions are all real names (`TokioAsyncContext` and 9 methods, `TokioContextCancellation.poll`, `NotifyingReporter.report_to`, `sum_task`, the tests `cancellation`, `async_tokio_runtime_reporting_does_not_block`...). One is a `function` `report_to` (L277): `impl ResultReporter for (T, Arc<..>)`, a tuple has no type name, as in any file.
- **libsignal** (`956e1ca`): 22503 -> 22524 nodes (+1 file, 4 classes, 12 methods, 4 functions; none lost), 36231 -> 36267 links (+36, none lost), 0 dangling, no file skipped.
- **Coverage** (`graphe check`, rust): 51148 -> 51264 sites; `ours?` 6736 -> 6749, `external` 20842 -> 20897, `ambiguous` 8910 -> 8922, `common` 14660 -> 14696. No other language moves.
- **`explain`** on the once-skipped file: `TokioAsyncContext.run_future_boxed` calls `handle` and `check_metrics`, is called by `run_future`; `TokioAsyncContext.run_future` and `cancel` are ambiguous by name (5 `fn run_future`, 3 `fn cancel` in libsignal: 6 and 18 calls unattributed, as by design).
- **The README's query**: `explain Timestamp.from_epoch_millis`, 57 callers by name, unchanged; 1577 -> 1585 bytes, its community's label only (Louvain, with the new nodes). The row's bytes updated. Build time not remeasured in alternation (40.9 s at HEAD, 43.2 s now, single warm runs on a slower machine than T-0032's): the README's 20.6 s left as it is, as T-0039 did.
- **The documents**: Rust's section in `docs/readers.md` (`tolerant` a quirk, the skip limit gone, the stderr `shortcut:` as Go's and Swift's; Rust in the `tolerant` lines), libsignal in `docs/sample-hosts.md`, ADR 0003's amendment, the README's row, the BACKLOG.md entry in Settled.
- **Not checked**: re-running the other hosts: protobuf's 128 `.rs` files all parse (checked one by one), so its graph is unchanged by construction; no `.rs` in the others.
- **The review** (2026-11-19, standards and spec): every criterion met, every figure re-checked against the before/after graphs and `check` outputs; the test fails with `tolerant=False`. Rust's Quirks in bullets as Go's, the measure left to this ticket. Left as they are: the `tolerant` languages listed in four places (the docstring, the field's comment, two lines of `docs/readers.md`), as each `tolerant` ticket did; the BACKLOG.md entry cites the ticket, not the commit, as T-0039's.
