Status: closed
Type: task
Part of: T-0030
Created: 2026-11-19
Blocked by: T-0031

# T-0034: C/C++ on protobuf, with its build time

## What to build

A C/C++ host gets a graph with no configuration: `explain`, `callers`, `path` and `search` answer on its functions, methods (`Class.method`) and types, with the tickets that cite them, through the generic reader of T-0031 (ADR 0003). C and C++ are one family, the single entry `c`: `.c` reads with the C grammar, `.h`, `.cpp`, `.cc`, `.cxx` and `.hpp` with the C++ one, and a C++ call to a C function is linked. The upstream `tags.scm` of both capture no call: the call queries are wholly ours. protobuf is the largest sample host: its build time decides whether the generic reader needs a cache. Proven on the sample host `protocolbuffers/protobuf`.

## Acceptance criteria

- [x] The readers' registry has a `c` entry; its `Language` is data only; its grammar is pinned in the main dependencies.
- [x] Its queries are ours, written from the grammar's `tags.scm` in the capture convention of T-0031, and tested at the internal seam `read(language, file, source)` on a snippet: definitions, `Class.method`, calls with their owner.
- [x] Both grammars pinned; a test at `contribute(project)`: a C++ call to a function defined in a `.c` file is linked, and a `.h` declaration is read.
- [x] protobuf's whole build time measured; if the generic reader weighs heavily, a BACKLOG.md entry for a per-file cache reusing T-0026's mechanism. The Python and PHP readers' result on protobuf noted as a cross-check.
- [x] `protocolbuffers/protobuf`, at a pinned commit (added to the sample hosts document if no ticket pinned it yet), builds with no dangling link; its C/C++ `check` coverage, its build time and three `explain` or `callers` queries compared with grep are noted in this ticket's comments.
- [x] The common method names are tuned from `check`'s most frequent C/C++ names by name.
- [x] The readers document has C/C++'s section (suffixes, grammar and version, nodes, links and confidence, quirks, `shortcut:` limits, sample host); the README's "Tested on" table has `protocolbuffers/protobuf`'s row, or its C/C++ column if the row exists, measures only.
- [x] The existing hosts checked for C/C++ files: noted, kept or excluded; the existing readers' nodes and links unchanged.
- [x] What the generic reader misses on `protocolbuffers/protobuf` is in BACKLOG.md, naming the host.
- [x] The tests pass.

## Blocked by

T-0031.

## Comments

- **The entry** (2026-11-19): `c` in `READERS`, `C` data only in `graphe_generic.py`, `tree-sitter-c` 0.24.2 and `tree-sitter-cpp` 0.23.4 pinned. `.c` reads with the C grammar, `.h`, `.cpp`, `.cc`, `.cxx`, `.hpp` with the C++ one. The queries are ours (the upstream `tags.scm` capture no call), built from shared pieces: a name in any declarator (`char** f()`, `T& C::m()`), qualified up to three scopes, the innermost scope the class. py-tree-sitter 0.26.1 drops a match whose alternation holds a captured alternation (`[[(identifier) (field_identifier)] @name (qualified_identifier)]` missed `int a() {}` in a class): the forms are listed flat, said in the code. Tested at `read()` on a snippet (`ns::Foo::Bar`, `Foo<T>::Get`, constructor, destructor, operator, prototype, `= default`, `PROTOBUF_EXPORT`, `ABSL_ATTRIBUTE_LIFETIME_BOUND`, `enum : int`, `typedef struct {..} T`) and at `contribute()`: a `.cc` and a `.h`'s inline method calling a function defined in a `.c` are linked to it, its `.h` prototype is no second definition.
- **Two pieces of data on `Language`**, both measured on protobuf, `False`/`None` for Go, Rust and Java (their path unchanged):
  - `tolerant`: 557 of protobuf's 1363 C/C++ files have an error node (macros); skipping them would lose 41 % of the code. Read all the same: no macro garbage in the 6023 definitions under an error node (the top names are generated code's `Clear`, `ByteSizeLong`, `SharedCtor`). A name the grammar inserts to recover is skipped (`enum : int {..}`, 69 empty names), tested.
  - `erased`: `class PROTOBUF_EXPORT Descriptor {` read as a function `Descriptor` (`Descriptor`, `CodedInputStream`, `InternalMetadata` were no classes), `f() const ABSL_ATTRIBUTE_LIFETIME_BOUND {` as no function (834). Four rules measured: two targeted ones (`class MACRO Name`, a macro after the parameters), then any upper-case name with an underscore and no arguments, then the same only before a name or a brace. The third kept: the simplest, and the most definitions (classes 2208 -> 2542, functions and methods 23811 -> 26202), no name made of a macro left; it erases a constant in an expression too (765 files with an error node instead of 557, BACKLOG.md). A first targeted regex backtracked exponentially (`[A-Z][A-Z0-9_]*` then an optional space): caught on protobuf, the kept one has no nested repeat.
- **protobuf** (`e08e1e7`, 3795 files, 1363 C/C++): 57327 nodes, 89975 links, 0 dangling, no file skipped. Build 68.0 / 70.2 / 71.9 s (warm; T-0033's 35.1 s): the graph doubles (27220 -> 57327 nodes). Under the profiler (82 s): the layout 44 s, `assemble` 27 s of which the generic readers 13 s (C/C++ about 8 s, parsing 4.9 s), the communities 8 s. The generic reader does not weigh heavily: no per-file cache entry; the layout's share is noted in the large-repository item of BACKLOG.md. Without the amalgamations (`php-upb`, `ruby-upb`, 4 files): `ambiguous` 79088 -> 56664, `ours?` 36523 -> 48720.
- **The existing hosts**: Grid Zero, dpe, 4cast, the tool itself, gitea and Django carry no `.c`, `.h`, `.cc`, `.cpp`, `.cxx` nor `.hpp`: no contribution. Grid Zero built by HEAD's tool (a worktree) and by this one: `graphe.json` identical, `built` and `built_s` aside; its reference test (`graphe_reference.py comparer`): identical. libsignal has 2 C headers (`swift/Sources/SignalFfi/signal_ffi.h`, `signal_ffi_testing.h`, its Swift FFI): 546 nodes more (544 structs, 2 files), 0 lost, 0 link lost; 3071 sites, all `external` (`static_assert_64bit`, a macro); its row in the README unchanged.
- **protobuf's other readers, a cross-check** (HEAD's graph against this one): their nodes identical (27220, none changed), no link of theirs lost but 21 `names` links of documents (`docs/design/editions/*.md` naming `has_presence`, `check`, `packed`): those names now have a C++ definition too, so the core finds them ambiguous. Python's coverage unchanged (16018 sites, `ours` 1702, `ambiguous` 1034); the PHP reader reports no sites (its 158 `.php` files read as before).
- **Coverage** (`graphe check`, c, 209148 sites): `common` empty first: `external` 82398, `ambiguous` 89051, `ours?` 38379; the common names taken from the most frequent sends linked by name whose receiver is the standard library's (`std::string` 628 to a generated `JsonEnumValueOptions.string`, `s.append` 185, `v.emplace_back` 178, `v.reserve` 114, absl's `status.message` 80, `pop_back` 74, `ss.str` 42, `p.release` 26, `m.count` 18: 9 names in `C.common`; the others guessed, the containers', strings', smart pointers', `optional`'s and `std::`'s, most already `ambiguous`). With the macros erased: `external` 82289 (`EXPECT_EQ` 9384, `UPB_SIZE` 4815: macros), `ambiguous` 79088, `ours?` 36523, `common` 11248. The `ours?` left are protobuf's (`FieldDescriptor.is_repeated` 347, `Arena::Create` 324, `Printer.WithVars` 160).
- **Three queries against grep** (bytes of the answer; grep over the C/C++ files):
  - `callers src/google/protobuf/descriptor.h::FieldDescriptor.is_repeated` (`FieldDescriptor.is_repeated` alone also names Python's): 224 callers by name, 154 lines, 22094 bytes; grep `is_repeated(`: 377 lines in 80 files, 33868 bytes. The pyext `.cc` callers included, Python's `is_repeated` apart.
  - `explain CodedInputStream.ReadVarint32`: no caller, "+ 22 calls named `ReadVarint32` the graph could not attribute: grep them", 560 bytes; grep `ReadVarint32(`: 32 lines in 10 files, 3263 bytes. A free `ReadVarint32` in `parse_context.h` makes the name ambiguous.
  - `explain upb/mem/internal/arena.h::upb_Arena_Malloc`: "+ 197 calls ... could not attribute", 323 bytes; grep `upb_Arena_Malloc(`: 212 lines in 62 files, 19734 bytes. The PHP and Ruby amalgamations define it twice more (BACKLOG.md).
- **What it misses** (BACKLOG.md): the amalgamations, a class an `#ifdef` cuts (protobuf's `Arena`), a constant erased like a macro, a file's gtest tests as one `TEST_F`. Said in C/C++'s section: a namespace scope taken for a class (`internal.Helper`), the Objective-C headers read as C++ (41, 49 definitions).
- **The documents**: C/C++'s section in `docs/readers.md` (and `tolerant`, `erased` in "Adding a language"), protobuf and libsignal in `docs/sample-hosts.md`, protobuf's README row, `docs/contribution.md`, `--help` and the skill name the `c` reader.
- **Not checked**: Linux and macOS wheels of the two grammars; protobuf's C#, Ruby and Objective-C (T-0035, T-0036; Objective-C has no ticket).
