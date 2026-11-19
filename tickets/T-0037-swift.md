Status: closed
Type: task
Part of: T-0030
Created: 2026-11-19
Blocked by: T-0031

# T-0037: Swift on libsignal

## What to build

A Swift host gets a graph with no configuration: `explain`, `callers`, `path` and `search` answer on its functions, methods (`Class.method`) and types, with the tickets that cite them, through the generic reader of T-0031 (ADR 0003). The upstream `tags.scm` captures no call: the call queries are wholly ours. Proven on the sample host `signalapp/libsignal`.

## Acceptance criteria

- [x] The readers' registry has a `swift` entry; its `Language` is data only; its grammar is pinned in the main dependencies.
- [x] Its queries are ours, written from the grammar's `tags.scm` in the capture convention of T-0031, and tested at the internal seam `read(language, file, source)` on a snippet: definitions, `Class.method`, calls with their owner.
- [x] A bare call and a receiver call are both captured, tested.
- [x] `signalapp/libsignal`, at a pinned commit (added to the sample hosts document if no ticket pinned it yet), builds with no dangling link; its Swift `check` coverage, its build time and three `explain` or `callers` queries compared with grep are noted in this ticket's comments.
- [x] The common method names are tuned from `check`'s most frequent Swift names by name.
- [x] The readers document has Swift's section (suffixes, grammar and version, nodes, links and confidence, quirks, `shortcut:` limits, sample host); the README's "Tested on" table has `signalapp/libsignal`'s row, or its Swift column if the row exists, measures only.
- [x] The existing hosts checked for Swift files: noted, kept or excluded; the existing readers' nodes and links unchanged.
- [x] What the generic reader misses on `signalapp/libsignal` is in BACKLOG.md, naming the host.
- [x] The tests pass.

## Blocked by

T-0031.

## Comments

- **The entry** (2026-11-19): `swift` in `READERS`, `SWIFT` data only in `graphe_generic.py`, `tree-sitter-swift` 0.7.4 pinned. Its `tags.scm` captures no call: the query is ours. A class, struct, enum and actor are one `class_declaration`, a class; a protocol is one too. An `extension T` is no class: its methods are `T`'s by `@receiver`, as Go's, so that a type extended in several files stays one class and its references are linked; a method is captured as a direct child of a type's or an extension's body, the one way to tell them apart. `init` is `C.init`, a computed property `C.p`. `b()` is a `@call`; `x.c()`, `y?.c()`, `.c()` are `@send`; `C(..)`, `Foo.Bar(..)`, `Array<Int>()` and an inherited type are `references` by the last name (Swift's capitalised types). Tested at `read()` on three snippets: a type, its methods and calls; an extension; `defer { }` and the standard `withUnsafePointer(to:)`, no call.
- **libsignal** (`956e1ca`, 1852 files, 218 `.swift`): 20576 nodes, 32758 links, 0 dangling. Swift: 3928 nodes (218 files, 772 classes, 2862 methods, 76 functions), 8109 links (2043 `references`). The grammar does not parse 10 files (parameter packs `repeat (each T)`, `case .self`, `catch E.c(_:)`, `() = try x`): skipped first, then read `tolerant`, they keep every definition (the one `func` missing, `check`, is nested). Build, after the review, alternated with a build without Swift (`READERS` less `swift`) the machine being slower than at T-0034: 27.6 / 27.7 / 28.1 s against 24.0 / 23.5 / 22.9 s, about 4 s for Swift; the README's row takes 27.7 s.
- **The computed properties**: 670 of the 8213 calls (8 %) were their class's, mostly in its 464 computed properties (`var name: String { .. }`), so `callers ServiceId.parseFrom` said `ProtocolAddress:8`. Captured as methods `C.p` (577 nodes), they say `ProtocolAddress.serviceId:64`; 26 sites became ambiguous (`body` 16, a closure parameter; `accessKey` 6).
- **Coverage** (`graphe check`, swift, 8213 sites): the guessed list first: `ambiguous` 2572, `external` 2568, `ours?` 2449, `common` 693. The grammar reads `defer { }` as a call `defer` (40 `external`): dropped. The 24 bare `withUnsafePointer(to:)` are the standard's, linked to libsignal's `BackupKey.withUnsafePointer`: dropped (with `withUnsafeMutablePointer`), the query's `#not-match?` (`#not-any-of?` is not applied by py-tree-sitter). The most frequent sends linked by name, checked one by one: libsignal's own (`withNativeHandle` 124, `parseFrom` 33, `bytes`, `slice`, `compare`, `log`, `build`, `process`) but `withCString` (24, `String`'s, which libsignal wraps on `Optional`) and `combine` (3 of its 4 sends `Hasher.combine`, linked to `GroupSendEndorsement.combine`): taken. Of the guessed names libsignal defines, `remove` is left out (its one send `svrB.remove()` is its own), `append` (71, `Data`'s), `encode`, `index`, `count`, `next`, `hash` kept. With them: `ambiguous` 2598, `external` 2496, `ours?` 2399, `common` 720 (`init` 611). `ambiguous`: the FFI conformances (`convertReturn` 545, `const` 475, `convertArgBorrowed` 376, `emptyFfiReturn` 164), defined about 160 times each. `external`: `Result.get` 439, `map` 87, `SignalError.internalError` 73, the C functions of `SignalFfi` (`signal_free_string`), XCTest's.
- **Three queries against grep** (bytes of the answer; grep by word over the `.swift` files, without the `func`):
  - `explain failOnError`: 245 callers by name (264 sites), 1661 bytes; grep `-w failOnError`: 265 lines in 71 files, 24257 bytes.
  - `explain NativeHandleOwner.withNativeHandle`: 265 callers by name, 1970 bytes; grep `-w withNativeHandle`: 294 lines in 64 files, 34017 bytes.
  - `callers ServiceId.parseFrom`: 18 callers, 1882 bytes (its three overloads one method); grep `-w parseFrom`: 33 lines in 12 files, 4399 bytes.
- **The existing hosts**: Grid Zero, dpe, 4cast, cadastre-poc, the tool itself, gitea and Django carry no `.swift`: no contribution. Grid Zero's reference test (`graphe_reference.py comparer`): identical. protobuf has 3 (`objectivec/*.swift`): kept, 22 nodes, its other nodes identical, no link lost.
- **libsignal's other readers, a cross-check** (the graph before Swift against this one): their nodes identical (16648), 3 `names` links lost to a name Swift defines too (`doc/src/net/chat.md` naming `connectAuthenticatedChat`, until then TypeScript's; `description`, `metadata`), 4 `names` links gained to Swift.
- **What it misses** (BACKLOG.md): the FFI conformances' names ambiguous (2598 of 8213 sites, a receiver's type needed), a nested function, an operator or a subscript no definition. Said in Swift's section: a capitalised call is a type by convention, an enum case `.c(x)` a send, a stored property's initial value its class's.
- **The review** (2026-11-19, standards and spec): a generic base (`class PinHash: NativeHandleOwner<P>`) was no reference, the type's name not being the last child: `_SW_TYPE` takes `Base<T>` as `_SW_EXTENDED` did, so `explain NativeHandleOwner` lists 60 subclasses (`references` 1941 -> 2043), tested; `Foo.Bar<Int>()` referenced `Foo` too, now `Bar` only, tested. The computed properties are 577 (464 was a grep's estimate). The limits each a `shortcut:` in the code too (the capitalised calls, the three names dropped, a stored property's value and observers, `tolerant` naming no file); ADR 0003's amendment names Swift's `tolerant`. Left as they are: the computed properties as methods (measured above), the guessed common names (as C#'s and Ruby's).
- **The documents**: Swift's section in `docs/readers.md` (and Swift in the `@class` and `@receiver` rows, among the `tolerant`), libsignal's and protobuf's Swift in `docs/sample-hosts.md`, libsignal's README row, `docs/contribution.md`, `--help` and the skill name the `swift` reader.
- **Not checked**: Linux and macOS wheels of the grammar.
