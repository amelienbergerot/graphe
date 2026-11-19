Status: closed
Type: task
Part of: T-0030
Created: 2026-11-19
Blocked by: T-0031

# T-0038: Kotlin on libsignal

## What to build

A Kotlin host gets a graph with no configuration: `explain`, `callers`, `path` and `search` answer on its functions, methods (`Class.method`) and types, with the tickets that cite them, through the generic reader of T-0031 (ADR 0003). Its grammar ships no `tags.scm`: all its queries are written from scratch in the convention. Proven on the sample host `signalapp/libsignal`.

## Acceptance criteria

- [x] The readers' registry has a `kotlin` entry; its `Language` is data only; its grammar is pinned in the main dependencies.
- [x] Its queries are ours, written from the grammar's `tags.scm` in the capture convention of T-0031, and tested at the internal seam `read(language, file, source)` on a snippet: definitions, `Class.method`, calls with their owner.
- [x] `signalapp/libsignal`, at a pinned commit (added to the sample hosts document if no ticket pinned it yet), builds with no dangling link; its Kotlin `check` coverage, its build time and three `explain` or `callers` queries compared with grep are noted in this ticket's comments.
- [x] The common method names are tuned from `check`'s most frequent Kotlin names by name.
- [x] The readers document has Kotlin's section (suffixes, grammar and version, nodes, links and confidence, quirks, `shortcut:` limits, sample host); the README's "Tested on" table has `signalapp/libsignal`'s row, or its Kotlin column if the row exists, measures only.
- [x] The existing hosts checked for Kotlin files: noted, kept or excluded; the existing readers' nodes and links unchanged.
- [x] What the generic reader misses on `signalapp/libsignal` is in BACKLOG.md, naming the host.
- [x] The tests pass.

## Blocked by

T-0031.

## Comments

- **The entry** (2026-11-19): `kotlin` in `READERS`, `KOTLIN` data only in `graphe_generic.py`, `tree-sitter-kotlin` 1.1.0 pinned. The grammar ships no `tags.scm`: the query is ours. A class, interface, enum and `object` are classes; a companion object is none, its functions its class's. A function is captured as a direct child of a file or of a type's body, so an anonymous object's and a local one are none. An extension function `fun Foo.Bar.f()` is the method `Bar.f` by `@receiver`, as Go's (libsignal's 73: its `toFfiArgType` of each type apart); the query tells it from a plain function by what comes right before the name (modifiers, type parameters or nothing). A secondary constructor is `C.constructor`. `b()` is a `@call`; `x.c()`, `y?.c()`, `this.c()` are `@send`; `C(..)`, `Foo.Bar(..)` and a supertype are `references` by the last name. Tested at `read()` on two snippets: the types, their methods and calls; the extension functions (nullable, generic, qualified, inside a class).
- **The grammar's quirks**: a class body on one line does not parse (`class C { fun f() {} }`), and `Array<Int>(1)` without a trailing lambda, or after a `+`, reads as comparisons.
- **libsignal** (`956e1ca`, 1852 files, 125 `.kt`): 22503 nodes, 36231 links, 0 dangling. Kotlin: 1927 nodes (125 files, 759 classes, 1035 methods, 8 functions), 3844 links (1802 `contains`, 1403 `calls`, 639 `references`; 1544 `calls` before the common names); every file parses, not `tolerant`. Build, after the review, alternated with a build without Kotlin (`READERS` less `kotlin`) on a quiet machine: 20.6 / 20.4 / 20.6 s against 21.5 / 21.6 / 21.7 s, Kotlin's share within the noise; the Kotlin contribution timed alone: 0.9 to 1.0 s, against Swift's 4.4 s in the same run. The README's row takes 20.6 s (an earlier alternation, the machine noisy, gave 42.8 to 67.0 s either way).
- **Coverage** (`graphe check`, kotlin, 3498 sites): without common names `external` 1822, `ours?` 1550, `ambiguous` 126. The most frequent sends linked by name, checked one by one: `get` (78, `CompletableFuture.get`, linked to `TestingIntBox.get`), `toString` (32, linked to `PendingTotpKey.toString`), `map` (31, mostly a collection's `.map { }`, linked to `RequestResult.map`), `hashCode`: taken. `await` (23, libsignal's own `CompletableFuture.await`), `start` (10, mostly `BackupJsonExporter.start`), `of` (4 of its 5 `BadgeVisibility.of`): left out. With them and the guessed ones: `external` 1822, `ours?` 1408, `common` 160, `ambiguous` 108. Of the guessed names libsignal defines, `remove` and `invoke` are left out after the review (one send each, its own `svrB.remove()` and `SetProfileHelpers.invoke`), `close` kept (`handleOwner.close`, an `AutoCloseable`), `equals` and `hashCode` kept (no send linked); the others guessed are not measured, most with no send on libsignal. `ours?`: `identity` 566 (`NativeNiceHelpers.identity`, libsignal's), `toRequestResult` 78, `mapWithCancellation` 77. `external`: kotlin.test (by name: `assertEquals` 158, `assertIs` 129, `runTest` 83), the standard library (`use`, `arrayOf`, `let`, `listOf`), and libsignal's Java: 488 of the 1822 sites name a Java definition (`nativeHandle` 71, `makeCancelable` 69). `ambiguous`: `toFfiArgType` 40 (one per type, generated test code), `serialize` 27.
- **Three queries against grep** (bytes of the answer; grep by word over the `.kt` files, without the `fun` line):
  - `explain Throwable.toRequestResult`: 77 callers by name, 2077 bytes; grep `-w toRequestResult`: 80 lines in 23 files, 11543 bytes.
  - `callers CompletableFuture.mapWithCancellation`: 77 callers by name, 10863 bytes (every caller listed); grep `-w mapWithCancellation`: 101 lines in 23 files, 11447 bytes.
  - `explain GrpcTestCase.runTests`: 65 callers by name, 2416 bytes; grep `-w runTests`: 65 lines in 20 files, 7220 bytes.
- **The existing hosts**: Grid Zero, dpe, 4cast, cadastre-poc, the tool itself, gitea and Django carry no `.kt`: no contribution. Grid Zero's reference test (`graphe_reference.py comparer`): identical. protobuf has 23 (`java/kotlin*/`): kept, 18 read (144 nodes), its other nodes identical, no link lost. 5 do not parse (a trailing comma in type parameters, `ExtendableMessageExtensions.kt` and its lite twin; a soft keyword used as a name, `by = "foo"`, in `Proto2Test.kt`, `Proto3Test.kt`, `Proto2LiteTest.kt`): skipped and named. Not `tolerant`: the error node of a test file holds its whole class, its methods would become functions.
- **libsignal's other readers, a cross-check** (the graph before Kotlin against this one): their 20576 nodes identical, no link lost, 3 `names` links gained (`doc/src/net/chat.md` naming `RequestResult`, `NonSuccess`, `Failure`).
- **What it misses** (BACKLOG.md): the calls to libsignal's Java (`external`, one JVM entry would link them), an extension function of one name on several types (`toFfiArgType`, ambiguous), protobuf's 5 files in the grammar's blind spots. Said in Kotlin's section: a getter, a setter and an `init { }` call from their class, a capitalised call is a type by convention.
- **The documents**: Kotlin's section in `docs/readers.md` (and Kotlin in the `@class` and `@receiver` rows), libsignal's and protobuf's Kotlin in `docs/sample-hosts.md`, libsignal's README row, `docs/contribution.md`, `--help` and the skill name the `kotlin` reader.
- **The review** (2026-11-19, standards and spec): `remove` and `invoke` dropped from the guessed common names (libsignal's own, measured above: `ours?` 1406 -> 1408); a code span of `docs/readers.md` cut by a newline mended; the grammar's two quirks (a class body on one line, `Array<Int>(1)`) a `shortcut:` in the code and the section; the four class-body patterns of the query merged into two alternations (libsignal's Kotlin nodes and sites identical); ADR 0003 says Kotlin's grammar ships no `tags.scm`; an extension on a function type (`fun (() -> Unit).f()`), not captured, said in the section; the link count after the common names (3844, not 3985). Left as they are: a member extension `class K { fun String.f() }` is `String.f` (its receiver), `TODO()` a reference (the capitalised-call `shortcut:`, `external`).
- **Not checked**: Linux and macOS wheels of the grammar.
