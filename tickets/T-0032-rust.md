Status: closed
Type: task
Part of: T-0030
Created: 2026-11-19
Blocked by: T-0031

# T-0032: Rust on libsignal

## What to build

A Rust host gets a graph with no configuration: `explain`, `callers`, `path` and `search` answer on its functions, methods (`Class.method`) and types, with the tickets that cite them, through the generic reader of T-0031 (ADR 0003). Its queries were proven on a snippet in T-0031 (a function of `impl T` is `T.f`); this ticket gives Rust its entry and its measure. Proven on the sample host `signalapp/libsignal`.

## Acceptance criteria

- [x] The readers' registry has a `rust` entry; its `Language` is data only; its grammar is pinned in the main dependencies.
- [x] Its queries are ours, written from the grammar's `tags.scm` in the capture convention of T-0031, and tested at the internal seam `read(language, file, source)` on a snippet: definitions, `Class.method`, calls with their owner.
- [x] `signalapp/libsignal`, at a pinned commit (added to the sample hosts document if no ticket pinned it yet), builds with no dangling link; its Rust `check` coverage, its build time and three `explain` or `callers` queries compared with grep are noted in this ticket's comments.
- [x] The common method names are tuned from `check`'s most frequent Rust names by name.
- [x] The readers document has Rust's section (suffixes, grammar and version, nodes, links and confidence, quirks, `shortcut:` limits, sample host); the README's "Tested on" table has `signalapp/libsignal`'s row, or its Rust column if the row exists, measures only.
- [x] The existing hosts checked for Rust files: noted, kept or excluded; the existing readers' nodes and links unchanged.
- [x] What the generic reader misses on `signalapp/libsignal` is in BACKLOG.md, naming the host.
- [x] The tests pass.

## Blocked by

T-0031.

## Comments

- **From T-0031's review** (2026-11-19), Rust's query and `RUST.common` are in `graphe_generic.py`, proven on one snippet; probed, not yet fixed: a `struct T` and its `impl T` in two files are two class nodes (the merge is per file), so `T {}` is linked to neither; `impl Tr for &'a T` is not matched (no `reference_type`), its functions are free functions; `impl Tr for Vec<T>` draws a class `Vec`; `crate::m::f()` and `Self::f()` are `@send`, so a common name is never linked even by its path; the common names are guessed, to tune on the sample host.
- **The entry** (2026-11-19): `rust` in `READERS`, `RUST` data only in `graphe_generic.py`. One pattern added: `impl Tr for &'a T` (and `&mut T`) is a class `T` (63 such impls on libsignal, their functions were free functions), tested in the Rust snippet.
- **The JS reader** failed on libsignal's TypeScript: a comment among the names of `import { }` (`node/ts/NativeNice.ts`) is a named child of the clause, without a `name`. Skipped now, in imports and exports, tested.
- **The existing hosts** (none carries a `.rs` file): Grid Zero, dpe, 4cast and the tool itself built by HEAD's tool and by this one: `graphe.json` identical, the build's duration aside; Grid Zero's reference test (`graphe_reference.py comparer`): identical.
- **libsignal** (`956e1ca`, 1852 files, 612 `.rs`, 176 `.ts`): 14322 nodes, 21214 links, 0 dangling. Build 17.6 / 17.7 / 17.9 s (warm), the JS reader included. 1 Rust file does not parse (`dyn 's + FnOnce`, grammar 0.24.2): skipped and named (BACKLOG.md).
- **Coverage** (`graphe check`, rust, 51148 sites): before the common names `ours?` 7997, `common` 12205, `ambiguous` 10104, `external` 20842; the common names taken from the most frequent sends linked by name whose text is the standard library's or a crate's (`f.debug_struct(..).field` 192, `x.as_slice` 164, `Vec::with_capacity` 94, `std::future::ready` 90, `ok`, `decode`, `transpose`, `recv`, `mpsc::channel`, `tokio::time::timeout`... 24 names, from `field` to `builder` in `RUST.common`; the ones after, from `take` on, guessed: the std traits' and iterators' methods): `ours?` 6702, `common` 14660, `ambiguous` 8944, `external` 20842. The `ours?` left are the host's (`log_and_send`, `run_tests`, `Timestamp::from_epoch_millis`).
- **Three queries against grep** (bytes of the answer):
  - `explain Timestamp.from_epoch_millis`: 57 callers by name, 1577 bytes; grep `from_epoch_millis(`: 81 lines in 30 files, 8260 bytes. The 64 calls the graph sees, plus 17 lines it does not, most of them inside a macro's arguments (`assert_eq!`, `vec![]`), which the grammar leaves as tokens (BACKLOG.md).
  - `callers log_and_send`: 78 callers, 9660 bytes; grep `log_and_send(`: 80 lines in 16 files, 8826 bytes: all 80 are calls the graph sees (a caller may call it twice).
  - `explain rust/core/src/curve.rs::KeyPair.generate` (`KeyPair.generate` designates 6 nodes, six `struct KeyPair` of six modules: 675 bytes to choose): no caller, "+ 393 calls named `generate` the graph could not attribute: grep them", 477 bytes; grep `KeyPair::generate(`: 236 lines in 62 files, 24759 bytes, 228 of them seen by the graph as ambiguous (118 written `KeyPair::generate` exactly, the others with a path, `uid_encryption::KeyPair::generate`), the rest comments and `IdentityKeyPair::generate`. A path `T::f()` is linked by `f` alone (BACKLOG.md).
- **Probed in T-0031, measured here** (BACKLOG.md, `shortcut:` in docs/readers.md): a `struct T` and its `impl` in two files are two classes, 506 of 2053 class names have nodes in several files, 605 of 3250 `T { .. }` ambiguous; `impl Tr for Vec<X>` draws a class `Vec` (10 files), `impl<T> Tr for T` a class `T` (15); `T::new()` is never linked (`new` is common: `DeviceId::new` 183, `ProtocolAddress::new` 132).
- **The documents**: Rust's section in `docs/readers.md` (Java's "not registered yet" kept apart), libsignal in `docs/sample-hosts.md`, its README row, `docs/contribution.md`, `--help` and the skill name the `rust` reader.
- **Not checked**: Linux and macOS wheels of the grammar; the Java, Swift and Kotlin of libsignal (T-0033, T-0037, T-0038).
