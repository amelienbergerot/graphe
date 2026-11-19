Status: closed
Type: task
Part of: T-0030
Created: 2026-11-19
Blocked by: T-0031

# T-0035: C# on protobuf

## What to build

A C# host gets a graph with no configuration: `explain`, `callers`, `path` and `search` answer on its functions, methods (`Class.method`) and types, with the tickets that cite them, through the generic reader of T-0031 (ADR 0003). The upstream `tags.scm` captures only calls on a receiver (`reference.send`): the bare calls `F()` are ours to capture. Its wheel stores its queries outside its package, which our own queries avoid. Proven on the sample host `protocolbuffers/protobuf`.

## Acceptance criteria

- [x] The readers' registry has a `csharp` entry; its `Language` is data only; its grammar is pinned in the main dependencies.
- [x] Its queries are ours, written from the grammar's `tags.scm` in the capture convention of T-0031, and tested at the internal seam `read(language, file, source)` on a snippet: definitions, `Class.method`, calls with their owner.
- [x] A bare call `F()` and a receiver call `x.M()` are both captured, tested.
- [x] `protocolbuffers/protobuf`, at a pinned commit (added to the sample hosts document if no ticket pinned it yet), builds with no dangling link; its C# `check` coverage, its build time and three `explain` or `callers` queries compared with grep are noted in this ticket's comments.
- [x] The common method names are tuned from `check`'s most frequent C# names by name.
- [x] The readers document has C#'s section (suffixes, grammar and version, nodes, links and confidence, quirks, `shortcut:` limits, sample host); the README's "Tested on" table has `protocolbuffers/protobuf`'s row, or its C# column if the row exists, measures only.
- [x] The existing hosts checked for C# files: noted, kept or excluded; the existing readers' nodes and links unchanged.
- [x] What the generic reader misses on `protocolbuffers/protobuf` is in BACKLOG.md, naming the host.
- [x] The tests pass.

## Blocked by

T-0031.

## Comments

- **The entry** (2026-11-19): `csharp` in `READERS`, `CSHARP` data only in `graphe_generic.py`, `tree-sitter-c-sharp` 0.24.0 pinned. Its `tags.scm` captures only `x.M()` (`reference.send`), and its wheel stores it outside its package (`site-packages/tree_sitter_c-sharp/queries/`): the query is ours, inline. `F()`, `F<T>()` are `@call`; `x.M()`, `x?.M()`, `this.M()`, `pb::C.M()` are `@send`; `new C()`, the base list and a record's primary-constructor base (`: B(X)`) are `references`, by the last name in their generic, qualified (`global::System.IEquatable<C>`) and aliased (`pb::IMessage<C>`) forms. Classes, interfaces, structs, enums, records; methods with a body (a block or `=> expr`), constructors `C.C`; an abstract or interface method without a body is no node, as Java's. Tested at `read()` on a snippet.
- **`#if`, both pieces of data of T-0034** (`erased`, `tolerant`, ADR 0003's amendment), measured on protobuf's 224 `.cs` files:

  | | skipped | classes | methods | functions |
  |---|---|---|---|---|
  | as is | 44 | 242 | 2021 | 0 |
  | `tolerant` | 0 | 757 | 2357 | 1285 |
  | `erased` (`#if`, `#elif`, `#else`, `#endif` lines) | 2 | 766 | 6381 | 0 |
  | both, kept | 0 | 769 | 6422 | 0 |

  Generated code cuts its base list with `#if !GOOGLE_PROTOBUF_REFSTRUCT_COMPATIBILITY_MODE` / `, pb::IBufferMessage` / `#endif`; the grammar does not parse it. The C# query has no `@function`: a function is a method whose class the recovery lost, so `tolerant` alone loses 1285. The 2 left once erased: `WritingPrimitives.cs` (`Unsafe.AddByteOffset(ref a, i) = x;`, 35 definitions) and `UnsafeCollectionOperationsTest.cs` (`var expected =` with both branches read, 9), read clean. Tested at `read()` (the base list cut by `#if`, an expression's two branches).
- **protobuf** (`e08e1e7`, 3795 files, 224 `.cs`): 64742 nodes, 103108 links, 0 dangling, no file skipped. C#: 7415 nodes (224 files, 769 classes, 6422 methods). Build 64.8 / 65.0 / 67.2 s (warm; T-0034's 70.2 s for 57327 nodes): no slower measurably, the C# reader a small share; the README's row takes 65.0 s.
- **Coverage** (`graphe check`, csharp, 35466 sites): `common` empty first: `ambiguous` 24448, `ours?` 5885, `external` 5133. The common names taken from the most frequent sends linked by name whose receiver is the BCL's: `builder.Append` (a `StringBuilder`, 31, to `BufferSegment.Append`), `enumerator.MoveNext` (19), `typeof(T).GetProperty` (16): 3 names; the others guessed (`object`'s, strings', collections', LINQ's, streams', reflection's). `Format` (`string.Format` 6 of 87) and `Parse` (`int.Parse` 5 of 61) are protobuf's own mostly (`JsonFormatter`, `JsonParser`): left out. With them: `ambiguous` 19463, `ours?` 5778, `external` 5133, `common` 5092. The guesses cut 25 links that were protobuf's (`list.RemoveAt` 11 and `list.IndexOf` 8 on a `RepeatedField`, `TypeExtensions.GetMethod` 6): the list's price. `external`: NUnit's (`Assert.AreEqual` 1834), `ReferenceEquals` 737, `partial void OnConstruction();` 364 (no body). The `ours?` left are protobuf's (`UnknownFieldSet.MergeFieldFrom` 729, `CodedOutputStream.ComputeInt32Size` 339).
- **Three queries against grep** (bytes of the answer; grep over the `.cs` files):
  - `callers ProtoPreconditions.CheckNotNull`: 138 callers by name, 102 lines, 24409 bytes; grep `CheckNotNull(`: 307 lines in 41 files, 42656 bytes. A property setter's call is its class's (`Person:56`, BACKLOG.md).
  - `explain ByteString.CopyFromUtf8`: 17 callers by name, 1834 bytes; grep `CopyFromUtf8(`: 25 lines in 8 files, 3551 bytes. The copied tests (`compatibility_tests/v3.0.0`) are linked to `src`'s `ByteString`, the copy defining none.
  - `explain CodedOutputStream.WriteRawTag`: no caller, "+ 2449 calls named `WriteRawTag` the graph could not attribute: grep them", 638 bytes; grep `WriteRawTag(`: 2459 lines in 43 files, 261228 bytes. `WriteContext` and `WritingPrimitives` define it too.
- **The existing hosts**: Grid Zero, dpe, 4cast, cadastre-poc, the tool itself, gitea, libsignal and Django carry no `.cs`: no contribution. Grid Zero's reference test (`graphe_reference.py comparer`): identical.
- **protobuf's other readers, a cross-check** (the graph before against this one): their nodes identical (57327, position and community aside), no link of theirs lost but 4 `names` links of documents (`docs/design/editions/*.md` naming `Syntax`, `Edition`, `IsValid`, `Feature`, now C# definitions too; BACKLOG.md).
- **What it misses** (BACKLOG.md): generated messages' methods of one name (`WriteTo`, `Clone`, about 348 definitions each) and `WriteRawTag` in 3 classes: 19463 sites `ambiguous`, the copied tests only 756 of them; a property is no definition; a nested `Types` is one per file. Said in C#'s section: a local function, an operator, a destructor are no definitions; both `#if` branches are read.
- **The review** (2026-11-19, standards and spec): the skip counts said alike (44 skipped as is, 2 once erased), the two `shortcut:` of `#if` apart, each with its upgrade, a record's primary-constructor base a reference (it was missed), `nameof` and the partial classes said in C#'s section. Left as they are: the guessed common names that cut 25 of protobuf's links (Java's and C/C++'s precedent); `tolerant` for 2 files (44 definitions), which stops naming a C# file that does not parse; the list of the languages taking `tolerant` and `erased` kept in the docstring, the field and `docs/readers.md`.
- **The documents**: C#'s section in `docs/readers.md` (and `tolerant`, `erased` for C# in the generic reader's part), ADR 0003's amendment, protobuf in `docs/sample-hosts.md`, protobuf's README row, `docs/contribution.md`, `--help` and the skill name the `csharp` reader.
- **Not checked**: Linux and macOS wheels of the grammar; protobuf's Ruby and Objective-C (T-0036; Objective-C has no ticket).
