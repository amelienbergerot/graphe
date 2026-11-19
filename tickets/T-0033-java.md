Status: closed
Type: task
Part of: T-0030
Created: 2026-11-19
Blocked by: T-0031

# T-0033: Java on protobuf

## What to build

A Java host gets a graph with no configuration: `explain`, `callers`, `path` and `search` answer on its functions, methods (`Class.method`) and types, with the tickets that cite them, through the generic reader of T-0031 (ADR 0003). Its queries were proven on a snippet in T-0031; this ticket gives Java its entry and its measure. Proven on the sample host `protocolbuffers/protobuf`.

## Acceptance criteria

- [x] The readers' registry has a `java` entry; its `Language` is data only; its grammar is pinned in the main dependencies.
- [x] Its queries are ours, written from the grammar's `tags.scm` in the capture convention of T-0031, and tested at the internal seam `read(language, file, source)` on a snippet: definitions, `Class.method`, calls with their owner.
- [x] `new C()` and `extends C` are `references` to the class, tested.
- [x] `protocolbuffers/protobuf`, at a pinned commit (added to the sample hosts document if no ticket pinned it yet), builds with no dangling link; its Java `check` coverage, its build time and three `explain` or `callers` queries compared with grep are noted in this ticket's comments.
- [x] The common method names are tuned from `check`'s most frequent Java names by name.
- [x] The readers document has Java's section (suffixes, grammar and version, nodes, links and confidence, quirks, `shortcut:` limits, sample host); the README's "Tested on" table has `protocolbuffers/protobuf`'s row, or its Java column if the row exists, measures only.
- [x] The existing hosts checked for Java files: noted, kept or excluded; the existing readers' nodes and links unchanged.
- [x] What the generic reader misses on `protocolbuffers/protobuf` is in BACKLOG.md, naming the host.
- [x] The tests pass.

## Blocked by

T-0031.

## Comments

- **From T-0031's review** (2026-11-19), Java's query and `JAVA.common` are in `graphe_generic.py`, proven on one snippet; probed, not yet fixed: the overloads `o(int)` and `o(String)` are two `A.o`, so every call to an overloaded method is `ambiguous`; an anonymous class (`new Runnable() { public void run() {...} }`) is not a `@class`, its methods take the outer class's name (`A.run_2`); a nested class is named by its own name, `X.Builder` and `Y.Builder` of one file are one node; the common names are guessed, to tune on the sample host.
- **The entry** (2026-11-19): `java` in `READERS`, `JAVA` data only in `graphe_generic.py`. Two changes, tested: the definitions of one kind and name in a file are one node (as the classes already were), so the overloads `o(int)` and `o(String)` are one `A.o` (on protobuf, `ours?` 13527 -> 16532); `extends GeneratedMessage.Builder<A>`, `new com.x.D()` and `new Outer.Inner<A>()` are `references` by their last name (generated code is full of them). `contribute()` tested on `extends B` and `new B()`: `references` links.
- **The merge on the other generic languages**, HEAD's `read()` against this one: on gitea's Go, no definition merged; on libsignal's Rust, 513 in 89 files (`Redact.fmt` 66, of two `impl`s of one type; `convert_into` 34, free functions of one name in several `mod`s of one file), tested and said in Rust's section. libsignal rebuilt: Rust `ours?` 6702 -> 6736, `ambiguous` 8944 -> 8910; `explain Timestamp.from_epoch_millis` unchanged (57 callers). Its 344 Java files: 0 dangling, none skipped, 7191 sites. Build, back to back: HEAD's tool 17.3 / 17.8 / 18.0 s (T-0032's 17.7), this one 23.2 / 24.6 / 25.9 s, Java's 1780 nodes and 3789 links more; the README row now says Rust, Java, TypeScript, 24.6 s.
- **The existing hosts** (none carries a `.java`, `.rs` or `.go` file): Grid Zero, dpe, 4cast and the tool itself built by HEAD's tool (a worktree) and by this one: `graphe.json` identical, `built` and `built_s` aside; Grid Zero's reference test (`graphe_reference.py comparer`): identical.
- **protobuf** (`e08e1e7`, 3795 files, 293 `.java`): 27220 nodes, 40091 links, 0 dangling, no Java file skipped. Build 33.2 / 35.1 / 35.2 s (warm), the Python, PHP, Go and Rust readers included.
- **Coverage** (`graphe check`, java, 117968 sites): before `ambiguous` 61678, `external` 23735, `common` 19028, `ours?` 13527; the overloads merged: `ambiguous` 58673, `ours?` 16532; the common names taken from the most frequent sends linked by name whose receiver is the JDK's (`s.getBytes` 64, `clazz.getMethod` 55, JRuby's `runtime.newString` 50, `map.keySet` 37, `buffer.flip` 33, `remaining`, `startsWith`, `endsWith`, `array`, `hasArray`, `getPackage`, `replace`, `arrayOffset`, `slice`, `emptySet`, `push`, `empty`, `loadClass`: 18 names in `JAVA.common`; the others guessed, the collections', `Object`'s and `String`'s, of which only `trim` takes protobuf's own, 3 calls of `FieldMaskUtil.trim`): `ambiguous` 57518, `external` 23735, `common` 20625, `ours?` 16090. The `ours?` left are protobuf's (`MapField.getMap`, `IntArrayList.addInt`, `CodedOutputStream.computeInt32SizeNoTag`).
- **Three queries against grep** (bytes of the answer):
  - `explain copyOnWrite` (`Builder.copyOnWrite`, `GeneratedMessageLite.java`): 747 callers by name, 1513 bytes; grep `copyOnWrite(`: 779 lines in 3 files, 85954 bytes. The 778 calls the graph sees and the definition.
  - `callers ByteString.copyFromUtf8`: 124 callers, 9253 bytes; grep `copyFromUtf8(`: 172 lines in 42 files, 25208 bytes: the 171 calls the graph sees and the definition.
  - `explain ArrayDecoder.pushLimit`: no caller, "+ 420 calls named `pushLimit` the graph could not attribute: grep them", 935 bytes; grep `pushLimit(`: 427 lines in 18 files, 58051 bytes. `CodedInputStream.pushLimit` is abstract, so no node: its calls are ambiguous between `ArrayDecoder` and `StreamDecoder` (BACKLOG.md).
- **What it misses** (BACKLOG.md): 11 copies of one generated file (`compatibility/smoke/v*/`) hold, with their 2 tests, 56581 of the 117968 sites: without them `ambiguous` 19863; a call to an abstract method; nested classes named by their own name (59 declarations share a name in their file), the 325 methods of anonymous classes taken by the enclosing class.
- **The documents**: Java's section in `docs/readers.md`, protobuf in `docs/sample-hosts.md`, its README row, `docs/contribution.md`, `--help` and the skill name the `java` reader.
- **Not checked**: Linux and macOS wheels of the grammar; protobuf's C#, Ruby, C/C++ and Objective-C (T-0034 to T-0036; Objective-C has no ticket).
