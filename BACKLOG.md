# What the graph could not tell

The tool's single backlog, for all its hosts. Each time `graphe` is not
enough and a search is done by hand (grep, sed, reading), an entry here: the
host, what we were looking for, what the graph answered, how we found it.
Material to improve the tool later (the user's request, 2026-11-02).

A settled entry moves to "Settled", with the commit. The entries settled
before T-0003 come from Grid Zero, and their commits are Grid Zero's.

## Open

- **The graph does not say which string values a field takes in the code.**
  (graphe, 2026-11-27, T-0074) Looking for every verdict a reader gives a
  call site (`"ambiguous"`, `"member"`, `"absent"`...), to map each to a
  cause: `graphe search ambiguous` gives the comments that name the word,
  not the `verdict = "ambiguous"` lines; grep found them in the four readers.
  The string constants a function assigns or returns, kept as its notes or
  searchable like its displayed texts, would have avoided the search.

- **The Python reader sometimes takes three times as long on Django.**
  (Django, sample host, 2026-11-27, measured for the parallel build) Of six
  builds at `9e2e5a3`, four took 36 to 42 s (the Python reader 15.9 s
  warm, 22.5 s cold), one warm build 65.9 s (the reader 45.7 s), one cold
  57.3 s (35.4 s); the cause is not found. T-0026 saw the first reads of a
  fresh cache take 16 to 29 s (the antivirus, probably). Timing the cache's
  reads apart from the ast walk on a slow run would tell; it weighs more
  than a parallel build would save on Django. T-0087 saw it again, warm:
  three builds of the same code 65.2, 73.8 and 41.9 s, then 41.5 to 45.5 s
  once alternated with the new code's.
- **The generic reader reads its files one after the other.** (protobuf,
  sample host, 2026-11-27, measured for the parallel build, T-0088)
  `read()` of protobuf's 1363 C/C++ files: 6.26 s serial, 1.92 s over 4
  processes, 1.60 s over 8 (x3.9, the results equal to the serial run's); the linking
  stays serial. T-0088 runs one process per reader, Django having nothing
  to gain from this split; to take it when a host's build is dominated by
  one generic language. Since T-0088 the readers run at once, so the
  largest one is the readers' critical path (protobuf's C/C++, gitea's Go):
  T-0092 splits its files.
- **On a large repository, a stale query still waits for the whole
  resolution.** (Django, sample host, 2026-11-25, T-0026) ~68 s per stale
  query on this machine: each Python file's definitions are cached, but the
  resolution across modules is redone in full. Only an incremental build
  (the resolution redone where a change reaches) would cut it: a large
  change, its own ticket if a host of Django's size comes. protobuf's C/C++
  has no cache of its own (the generic reader about 8 s of its build).
  graphify (compared 2026-11-27) re-extracts only the changed files
  (`--update`) and has a watch mode; whether its resolution across files is
  incremental too was not checked. `docs/research/similar-tools.md` (idea 8):
  key each file's cache on its git blob id, and re-resolve only the sites
  whose name's definitions changed (CodeQL's overlay analysis, Glean's
  ownership). Set aside on 2026-11-27 (T-0071) until such a host comes.
  The full build's serial part after the readers (T-0088 runs them at
  once): on protobuf, under load, the communities 11.6 s and the core's
  enrichment 11.1 s of 53.5 s, which T-0090 and T-0091 cut.
- **A Go generic method is no node.** (gitea, sample host, 2026-11-19,
  T-0031, T-0039) `tree-sitter-go` 0.25.0, the last on PyPI, knows neither
  `new(expr)` nor generic methods (`func (f *Flash) Error[T ...]`). Since
  T-0039 the 47 files with such syntax are read for their valid part, but
  the 7 generic methods (`Flash.Error`, `Warning`, `Info`, `Success`,
  `Context.JSONError`, `JSONErrorWithField`, `RenderWithErrDeprecated`) are
  lost in their error node: their calls are their file's, their callers
  not linked to them (`f.Error` is `common`, `Info` `ambiguous`, `Success`
  linked to gitea's other `Success`, the others `external`). A newer grammar
  would avoid it.
- **The generic reader cannot tell a Go package's function from another's.**
  (gitea, sample host, 2026-11-19, T-0031, measures of T-0039) `pkg.F()` is
  a send linked by the name alone: 29123 calls are `ambiguous` (`t.Context`
  4178, `MakeRequest` 2261, `NewRequest` 1850, `ctx.Tr` 851) and 24888
  `common` (`t.Run`, `fmt.Errorf`, `log.Error`, `filepath.Join`), against
  58121 linked by name.
  Go's imports name the package of `pkg.F()` for sure: a dedicated Go reader
  (ADR 0003) would link most of them, and would leave `strings.Join` out of
  the host's `Join` without a common name.
- **A Rust call inside a macro is not seen.** (libsignal, sample host,
  2026-11-19, T-0032) tree-sitter-rust leaves a macro's arguments as tokens:
  `assert_eq!(f(x), y)`, `vec![g()]`, `format!("{}", h())` hold no call.
  libsignal has 8604 macro invocations (`assert_eq!` 1624, `vec!` 1155,
  `assert!` 716); `Timestamp::from_epoch_millis(` has 81 grep lines, 64 calls
  the graph sees, most of the 17 others inside a macro. Parsing a token tree
  as expressions when it parses would recover them.
- **A Rust type's `impl` in another file than its `struct` is another class
  node.** (libsignal, sample host, 2026-11-19, T-0032) The classes of one
  name are merged per file only: 506 of libsignal's 2053 class names have
  nodes in several files (`Error` 26, `Redact` 16), so 605 of its 3250
  `T { .. }` are `ambiguous` and not linked. `impl<T> Tr for T` draws a class
  `T` (15 files), `impl Tr for Vec<X>` a class `Vec` (10). Swift's
  extensions (T-0037) take the same shape: merging a class's nodes across
  files, or a `@class` that only extends, is the generic reader's own ticket.
- **A Rust path's modules do not tell two types of one name apart.**
  (libsignal, sample host, 2026-11-27, T-0080) A send qualified by a class
  of the host is linked to that class's method (T-0080), but only the
  path's last name is read: `kem::KeyPair::generate` (118 calls) stays
  ambiguous between the 6 `struct KeyPair` of 6 modules, and std's
  `Duration::from_millis` goes to libsignal's own `struct Duration` (about
  42 of its 50 sites: those outside `rust/message-backup`, where its
  `from_millis` is `pub(super)`; grep found 34 of them in files importing
  `std::time::Duration`). `Self::f()` names no class, linked by `f`
  alone. Reading a file's `use` and an `impl`'s type would settle all
  three: the start of a dedicated Rust reader (ADR 0003).
- **Generated Java code repeated in a host makes its names ambiguous.**
  (protobuf, sample host, 2026-11-19, T-0033) 11 of protobuf's 293 Java
  files are one generated file, `Proto3GencodeTestProto.java`, as 9 old
  versions generated it (`compatibility/smoke/v*/`): with their 2 tests,
  13 files hold 56581 of the 117968 Java call sites. Each copy defines the
  same `TestMostTypesProto3`, `Builder`, `getDescriptor`, `parseFrom`, so
  57518 calls are `ambiguous`; without that folder, 19863. A `graphe.toml`
  `exclude` would drop them; telling a generated file (`// Generated by the
  protocol buffer compiler.  DO NOT EDIT!`) from the code would be the
  generic reader's own. T-0079 (2026-11-27) names the 11 copies, the most
  ambiguous of protobuf's 204 generated files (21786 to 26761 calls on
  their names each), and gives the `exclude` line: with it, `ambiguous`
  57624 -> 20009 of the Java sites (the sites 118387 -> 62041). Kept, they
  stay ambiguous: what is left
  is the host's choice.
- **Java's anonymous classes lose their methods to the enclosing class.**
  (protobuf, sample host, 2026-11-19, T-0033) The 325 methods of an
  anonymous class (`new Runnable() { public void run() {..} }`) are the
  enclosing class's (`A.run`). Making the anonymous body a class would keep
  them apart. Java's nested classes are `Outer.Inner` since T-0043 (Settled).
- **A C amalgamation makes every name it repeats ambiguous.** (protobuf,
  sample host, 2026-11-19, T-0034) `php/ext/google/protobuf/php-upb.{c,h}`
  and `ruby/ext/google/protobuf_c/ruby-upb.{c,h}` are upb's sources
  concatenated: each upb function is defined 3 times, so
  `upb_Arena_Malloc`'s 197 calls are not attributed (grep: 212 lines).
  Without those 4 files, `ambiguous` 79088 -> 56664 and `ours?` 36523 ->
  48720 of the C/C++ sites. A `graphe.toml` `exclude` would drop them; telling a
  generated or concatenated file from the code would be the generic reader's
  own, as Java's repeated generated file. T-0079 (2026-11-27) does not name
  them: their header is `/* Amalgamated source file */`, no marker it
  knows, and protobuf marks no `linguist-generated`. With 34 of its 44
  generated `.pb.h`/`.pb.cc` dropped (the line's), `ambiguous` 79092 ->
  66005 of the C/C++ sites; a marker for upb's amalgamator would name its
  4 amalgamation files.
- **A C++ class whose declaration an `#ifdef` cuts is lost.** (protobuf,
  sample host, 2026-11-19, T-0034) `class PROTOBUF_EXPORT` / `#ifdef
  __clang__` / `ABSL_ATTRIBUTE_WARN_UNUSED` / `#endif` / `Arena final {`:
  the grammar reads neither the class nor its methods' owner, so
  `Arena::Create` (310 calls) is linked to a function `Create`, and
  `explain Arena` finds hpb's, upb's, PHP's and Ruby's `Arena` classes, not
  `src/google/protobuf/arena.h`'s. The macros are erased
  by a regex (`C.erased`, upper case with an underscore, no arguments): a
  constant so named is erased in an expression too (765 files with an error
  node, 557 without erasing), a macro with arguments is not. Erasing a
  preprocessor branch, or the preprocessor's own pass, would read them.
- **A document's name loses its link when another language defines it too.**
  (protobuf, sample host, 2026-11-19, T-0034) The C/C++ definitions made 21
  `names` links of its documents (`cmake/README.md`, `docs/design/editions/*.md`) ambiguous (`has_presence`,
  `check`, `packed`, until then Python's or Java's only): the core links a
  name a document cites only when one node bears it. Preferring the
  language a document's code block or path names would keep them. C# (T-0035)
  made 4 more ambiguous (`docs/design/editions/*.md` naming `Syntax`,
  `Edition`, `IsValid`, `Feature`). Swift (T-0037) made 3 of libsignal's
  ambiguous (`doc/src/net/chat.md` naming `connectAuthenticatedChat`,
  until then TypeScript's; `description`, `metadata`).
- **C#'s generated messages make their methods' names ambiguous.**
  (protobuf, sample host, 2026-11-19, T-0035) Every generated message
  defines `WriteTo`, `Clone`, `CalculateSize`, `MergeFrom` (about 348 each),
  and `output.WriteRawTag` (2449 calls) has 3 definitions
  (`CodedOutputStream`, `WriteContext`, `WritingPrimitives`): 19463 of the
  35466 C# sites are `ambiguous`. The copy of the tests in
  `csharp/compatibility_tests/v3.0.0/` (28 files) accounts for 756 of them
  only. Linking `output.WriteRawTag` needs the receiver's type: a dedicated
  C# reader (ADR 0003). T-0079 (2026-11-27) names its 46 generated `.cs`
  (up to 6685 ambiguous calls on their names each, the methods every
  message defines; 43 in the `exclude` line): it takes `ambiguous` 19499
  -> 2626, but the sites 35466 -> 10169, most of protobuf's C# being
  generated.
- **Ruby's message classes are built at run time.** (protobuf, sample host,
  2026-11-19, T-0036) A message's fields are read through `method_missing`
  (`m.repeated_string`, 171 sends `external`), and the message class is
  `Class.new(..) do` in `ffi/message.rb`, its 41 methods named `Descriptor`'s
  (`Descriptor.encode`): `TestMessage.encode` is ambiguous between it and
  `Google::Protobuf.encode` (90 sends `encode`, 83 `decode`). Naming a class
  built by `Class.new` after what it is assigned to would need code of its
  own: a dedicated Ruby reader (ADR 0003).
- **A Ruby bare call is missed, as a variable is.** (protobuf, sample host,
  2026-11-19, T-0036) `b` alone may be a local variable: the query captures
  `b()`, `c arg`, `x.c` only, so at least 17 bare calls to protobuf's
  methods (`inspect`, `reset_allocations`) are missing from `callers`. The
  grammar's `locals.scm` tells a variable apart, a pass the generic reader
  does not make (`docs/research/similar-tools.md`, idea 12; set aside on
  2026-11-27, T-0071, until a Ruby host needs it). A class reopened in several files is one class per file
  likewise (12 names: `Descriptor`, `RepeatedField`), a reference to it
  ambiguous.
- **Swift's FFI conformances make their methods' names ambiguous.**
  (libsignal, sample host, 2026-11-19, T-0037) Each of libsignal's 134
  `extension SignalMutPointerX` / `SignalConstPointerX` defines `toOpaque`
  and `const`, each converter `convertReturn` and `emptyFfiReturn` (about
  160 each): `nativeHandle.const()` (475 sends) and `convertReturn` (545)
  are not attributed, 2598 of the 8213 Swift sites `ambiguous`. Linking
  them needs the receiver's type, or the protocol's requirement as a node:
  a dedicated Swift reader (ADR 0003). T-0081 (2026-11-27) makes a protocol's
  `func` requirement a node its conformances override: `const` (475 sites)
  goes to `SignalMutPointer.const`, `emptyFfiReturn` (164) and `convertArg`
  (76) to `NiceReturnConverter`'s and `NiceArgConverter`'s, 1161 Swift call
  sites more, `ambiguous` 2598 -> 1477. Left: `toOpaque` (8), required by
  both `SignalMutPointer` and `SignalConstPointer`, needs the receiver's
  type; `convertReturn` (545), because the test helper `UneraseType`
  (`ChatServiceTestBase.swift`) defines one without conforming to
  `NiceReturnConverter` (its generic parameter does): leaving out a test
  file would settle it, the host's choice.
- **A Swift nested function is no definition.** (libsignal, sample host,
  2026-11-19, T-0037) A `func` inside a function (`check` in
  `ChatServiceTests.swift`) is not captured, its calls its enclosing
  method's; operators (`static func ==`) and subscripts likewise. The query
  takes a type's or an extension's direct children only, the one way to
  tell an extension's method from a type's.
- **A library's name in Kotlin or Java is linked to the other one's
  definition.** (libsignal and protobuf, sample hosts, 2026-11-19, T-0042)
  Since Java and Kotlin are one entry, Kotlin's `ByteArray(32)`, the standard
  library's, is a `references` link to libsignal's Java
  `zkgroup.internal.ByteArray` (24 links; libsignal's Kotlin imports its own
  as `SignalByteArray`), and protobuf's Java `any.unpack(X.class)`, its
  generated `Any`'s, a `calls` link to its Kotlin `inline` extension
  `ProtoAny.unpack` (3 links, 8 sites). A capitalised call is taken for a
  type of the host by its last name: a list of Kotlin's standard types
  (`ByteArray`, `IntArray`, `Pair`...) never referenced, as the common names
  are for sends, would drop the first.
- **A Kotlin extension function of one name on several types is
  ambiguous.** (libsignal, sample host, 2026-11-19, T-0038) Its 40
  `this.toFfiArgType()` (generated test code: `fun MyTestEnum.Unit.toFfiArgType()`
  and its siblings, one per type) are not attributed: linking them needs the
  receiver's type, a dedicated reader's work (ADR 0003).
- **A Kotlin file in the grammar's blind spots is skipped whole.**
  (protobuf, sample host, 2026-11-19, T-0038) `tree-sitter-kotlin` 1.1.0
  reads neither a trailing comma in type parameters (`T : Any,` then `>`,
  `ExtendableMessageExtensions.kt` and its lite twin) nor a soft keyword used
  as a name (`by = "foo"`, the "evil names" tests `Proto2Test.kt`,
  `Proto3Test.kt`, `Proto2LiteTest.kt`): 5 of protobuf's 23 Kotlin files are
  skipped and named at each build. Being `tolerant` would keep the two
  extension files' other functions but turn a test class's methods into
  functions (the error node holds the whole class); a newer grammar, when
  one is published, or erasing the trailing comma (`erased`).
- **A file's gtest tests are one function.** (protobuf, sample host,
  2026-11-19, T-0034) `TEST_F(Suite, Name) { .. }` parses as a function
  `TEST_F`: protobuf's 4824 tests are one `TEST_F`, `TEST`, `TEST_P` or
  `TYPED_TEST` per file, so `callers` says `TEST_F` where grep says the test
  name. Naming a test by its suite and name (`Suite.Name`) would take a
  query of its own for a macro call with a body.
- **Only its author can install the tool.** (All hosts, 2026-11-18, the
  user's request) The install depends on a local clone, an editable
  `uv tool install` and PowerShell (README); ADR 0001 says "for a single
  user". The direction is other people's repositories: a published package,
  any OS, and ADR 0001 revisited. A separate effort, after the readers; until
  then a reader holds nothing specific to this machine.
- **The links a framework creates are outside the graph.** [T-0047] (All
  hosts, 2026-11-18, the user's request) A Django URL to its view, a JSX
  `<Component/>`, a Spring injection, a Rails route: no call carries them.
  Neither the core, nor a reader (one language), nor a local extension (one
  host): a notion to name. Named (2026-11-25): a keyed link (GLOSSARY.md).
  T-0047: the core makes it from the host's `[keys]` patterns (4cast's front
  to its PHP routes: 22 of its 25 front calls linked, not the 3 to
  `session`, answered at `api/index.php`'s top). Left: the frameworks, whose
  key is no string on one line (a decorator, a JSX tag, an injection), with
  the install effort; a route's HTTP method, no part of the key.
  `docs/research/similar-tools.md` (idea 10): `[keys]` presets per framework
  (Flask, Express, Gin, Django's `path()`), as CodeGraph's route table. Set
  aside on 2026-11-27 (T-0071) until a host needs one.
- **A call across languages by a translated name is not linked.** (libsignal,
  protobuf, sample hosts, 2026-11-25) JNI (`Java_pkg_Class_method` in C),
  FFI (a C function called from Swift), protobuf's generated code: the
  generic reader never links a call by name across languages (ADR 0003).
  Not a keyed link (the name is translated, not shared as a string); split
  from the entry above, none of the user's hosts has one.

- **PHP's generic reader misses a few uses.** [T-0044, T-0045] (4cast,
  protobuf, 2026-11-20) PHP's names are case-insensitive, the links by the exact name. protobuf's
  `php/tests/generated_previous/Previous/readonly.php` (`class readonly`, a
  keyword since PHP 8.1) does not parse: skipped. A router's `case "x":` in
  double quotes is no action. The `shortcut:`s of docs/readers.md's PHP.
- **The skill reaches Claude Code alone, and only for the questions it names.**
  [T-0077] (graphe, the user's request, 2026-11-27) Widen when the skill is used, and
  ship it to the other agents (Codex, Cursor, Copilot, Gemini CLI): today a
  Claude Code plugin, the others a README line to copy `skills/graphe/`
  (T-0053). Preset's plugin carries Codex and Cursor manifests beside Claude
  Code's (T-0049): the same, one manifest per agent, the skill's text kept
  neutral (T-0048).
  graphify (compared 2026-11-27) does both: `graphify install` detects the
  assistant (20+), and on Claude Code its hooks fire before Grep, Read, Glob
  and Bash's `cat`/`head`/`sed -n` to nudge toward the graph (a `--strict`
  mode, `GRAPHIFY_HOOK_NUDGE_CAP` nudges, reset by a `SessionStart` hook on
  `compact`). A PreToolUse hook of ours would reach the questions the
  description does not name: done by T-0077 (`graphe hook`, Grep and
  `grep`/`rg` only, no cap). The other agents: settled by T-0078 on paper, a
  root `plugin.json` (Agent Plugins: Codex, Copilot CLI, Cursor), Codex's
  `.agents/plugins/marketplace.json`, Gemini CLI's `gemini-extension.json`,
  one skill text, each manifest at the package's version (check_release.py).
  Waits on users' reports: whether each installs and triggers the skill
  (README: untested), whether Codex accepts a marketplace entry at its own
  root (`./`, no example in its docs), and Cursor's GitHub import, which wants
  a `.cursor-plugin/marketplace.json` whose root source is undocumented (left
  out: Cursor takes a local clone or `~/.cursor/skills/`). The hook stays
  Claude Code's. The entry stays open until those reports come.
- **A query needs a Bash permission, or it falls back to grep.** (graphe,
  comparison with graphify, 2026-11-27) Without `Bash(graphe *)` and
  `PowerShell(graphe *)` in `permissions.allow`, each query asks for approval
  and a headless `claude -p` greps instead (README). graphify serves its
  graph over MCP (`query_graph`, `shortest_path`, `get_neighbors`,
  `get_node`): an MCP server of ours (explain, callers, path, search) would
  reach the agents that speak MCP. It would still need a rule
  (`mcp__graphe__*`, as CodeGraph's README suggests), one for every OS rather
  than a Bash/PowerShell pair (`docs/research/similar-tools.md`, idea 4). Set
  aside on 2026-11-27 (T-0071) until an agent without a shell needs it.
- **A receiver's type, which a compiler-based indexer knows, is not used.**
  (graphe, comparison with similar tools, 2026-11-27) Most open entries on
  receivers (Java's abstract methods, C#, Go's packages, Kotlin's
  extensions) would be settled by a SCIP index (scip-java, scip-go,
  rust-analyzer, scip-dotnet), mapped onto graphe's nodes by file and range
  (`docs/research/similar-tools.md`, idea 9). The indexers need the host's
  build environment, which ADR 0002 set aside for the TypeScript compiler,
  and an index goes stale between runs. A local extension (ADR 0001) first,
  if a host has an index; set aside on 2026-11-27 (T-0071).

## Settled

Settled by tickets (2026-11-27):

- **A Java call to an abstract method is linked to none of its
  implementations.** [T-0081] (protobuf, sample host, 2026-11-19, T-0033) An abstract
  method has no node, so `input.pushLimit(n)` (407 calls) is `ambiguous`
  between `ArrayDecoder.pushLimit` and `StreamDecoder.pushLimit`, the nested
  implementations of `CodedInputStream.pushLimit`. Linking the call to the
  abstract method needs its node and the receiver's type: a dedicated Java
  reader (ADR 0003).
  T-0081: an abstract method is a node, which a method of its class or of a
  direct base overrides (`overrides`, by name); a call whose candidates all
  override one declaration goes to it, by name (ADR 0003's amendment), the
  receiver's type unread: `pushLimit` 420 sites, `writeUInt32NoTag` 688,
  `getBytesUntilLimit` 608. On protobuf, 3802 Java call sites linked more
  (20214 -> 24016), none lost or moved, 0 dangling; `ambiguous` 54023 ->
  50237.

- **A Rust `Type::f()` path is not linked when `f` is a common name.** [T-0080]
  (libsignal, sample host, 2026-11-19, T-0032) `T::f()` is a send, like
  `x.f()`: `DeviceId::new` (183 calls), `ProtocolAddress::new` (132),
  `TestStoreBuilder::new` (64) are `common`, never linked, though the path
  names the type; 14660 sends are `common`, 8944 calls `ambiguous`
  (`KeyPair::generate` 118, defined in 6 `struct KeyPair`), against 6702 linked by
  name. Linking `T::f` to the method `T.f` when `T` is a class of the host
  would link most of them, and Java's `C.f()` too: outside "by the name
  alone" (ADR 0003), to decide.
  T-0080: a send qualified by a class of the host has that class's methods
  for candidates, a common name too, linked by name when one is left
  (ADR 0003's amendment): `DeviceId::new` 184 sites, `ProtocolAddress::new`
  132, `TestStoreBuilder::new` 64; Java's and Kotlin's `C.f()` too. On
  libsignal, 2629 `calls` links more; on protobuf, 3112; none lost, 0 dangling. What is left is open below (a Rust
  path's modules).

- **Vue is not read.** [T-0082] (graphe, the user's request, 2026-11-27) README's
  "Not read" row: a Vue host gets no graph of its components, nor of the
  calls in their template. `.jsx` and `.tsx` are read since T-0076 (the
  JavaScript grammar, the TSX one); what is left is Vue (T-0082): a `.vue`
  file's `<script>` and template would take Svelte's path. A JSX
  `<Component/>` as a link is the framework entry's (T-0047).
  T-0082: a `.vue` file's script and template take Svelte's path, the
  script in the grammar its `lang` names.

- **A module variable holding a multi-line string runs to the end of its
  file.** [T-0083] (graphe, 2026-11-27, T-0075) `graphe affected` listed
  `tests/test_host.py::GRID_ZERO_TOML` as touched by lines added at the end of
  the file: its extent ran to the end. The cause: `core.extent` counted the
  parentheses of the regex on its first line as a signature never closed.
  T-0083: the parentheses inside a string do not count, the lines of a string
  over several lines are the block's; GRID_ZERO_TOML reads 405-419, and the
  other extents it changed on this repository end where their statement does.

- **What a diff reaches takes one `callers` per function.** [T-0075]
  (graphe, comparison with graphify, 2026-11-27) `graphe affected [REV]`
  maps `git diff REV` to the nodes it touches, the definitions it removes,
  then their callers to `--depth`.

Settled by tickets (2026-11-25):

- **On a large repository, a stale query waits for a whole build.** [T-0026,
  T-0046] (Django, sample host, 2026-11-18, T-0016) 48 s per build. T-0026:
  each Python file's parse and definitions cached (about 4.6 s less), the
  graph identical; T-0046: the layout out of `build`, made by `graphe view`
  on demand: a stale query 81.0 -> 67.7 s (medians, cache warm), the graph
  identical but for `x`/`y`. What remains is in Open.

Settled by tickets (2026-11-19):

- **PHP's pattern reader reads no class nor method.** [T-0044, T-0045]
  (4cast, Grid Zero, protobuf, 2026-11-19) `graphe_php.py` read 5 functions
  of protobuf's PHP, the generic entry 156 classes and 1723 methods; on 4cast
  both link the same 81 calls. Since T-0045 the generic entry is the `php`
  reader, with the PHP reader's `case 'x':` actions (`@action`): Grid Zero's
  8 actions, 2 `dispatches` and its extension's 6 `sends` kept, its graph the
  same but for the ids (`_php`), the calls' lines and confidence (`INFERRED`).
- **Java's nested classes lose their outer name.** [T-0043] (protobuf,
  sample host, 2026-11-19, T-0033) A nested class was named by its own name:
  each generated message's `Builder` of one file was one class, their
  methods of one name one method; C#'s `Types` likewise (T-0035). A class in
  a class is `Outer.Inner` since T-0043, in every language of the generic
  reader: protobuf's Java `Builder` 29 -> 74 classes, C#'s `Types` apart in
  10 files, Kotlin's sealed `Success` in libsignal (34). The price: longer
  names in the answers (`callers ByteString.copyFromUtf8` 9569 -> 11526
  bytes, `Proto3GencodeTestProto.TestMessage.Builder.getXBytes`), and a
  method declared outside its nested class is `Inner.m` (C++'s
  `Outer::Inner::m`, 108 on protobuf; Kotlin's extensions, 29 on libsignal;
  `shortcut:`).
- **Kotlin's calls to its host's Java are not linked.** [T-0042] (libsignal,
  sample host, 2026-11-19, T-0038) 488 of the 1822 Kotlin sites `external`
  named a definition of libsignal's Java (`nativeHandle` 71, `makeCancelable`
  69, `fakeConnect` 58, `guardedMap` 48). Java and Kotlin are one entry,
  `java`, since T-0042: 401 Kotlin sites linked (`fakeConnect` is ambiguous,
  three Java classes define it), `callers NativeHandleGuard.nativeHandle` 30
  -> 99. A name both define is ambiguous where each language's was linked
  (`filterExceptions`, 246 sites, a Kotlin twin of the Java one).
- **A C# property is no definition.** [T-0041] (protobuf, sample host,
  2026-11-19, T-0035) The calls of a property's `get`, `set` and `=> expr`
  belonged to its class: `callers ProtoPreconditions.CheckNotNull` listed
  generated classes (`Person:56`, 98 of its 138 callers). A property is the method
  `C.P` since T-0041: 270 callers, the setters (`Person.Name:109`). Its name
  among the definitions makes `JsonToken.Name` ambiguous (27 sites, a
  `shortcut:`).
- **A Rust file with `dyn 'a + Trait` is skipped whole.** [T-0040] (libsignal,
  sample host, 2026-11-19, T-0032) `tree-sitter-rust` 0.24.2 rejects a
  lifetime first in a trait object (`Box<dyn 's + FnOnce(..)>`):
  `rust/bridge/shared/types/src/net/tokio.rs`, 1 of 612 files. Rust is
  `tolerant` since T-0040: the error is the one `'`, the file's 20
  definitions are read, `TokioAsyncContext.run_future_boxed` among them.
- **A Go file in Go 1.26's syntax is skipped whole.** [T-0039] (gitea, 2026-11-19,
  T-0031) 47 of gitea's 3199 Go files were skipped (`new(expr)`, generic
  methods), their definitions lost everywhere (`ctx.ServerErrorAuto`
  `external` at its 1226 calls). Go is `tolerant` since T-0039: the files are
  read for their valid part, `ctx.ServerErrorAuto` linked at its 1234 calls.
  What remains, the generic methods, is open above.
- **A host in another language gets no graph.** [T-0030] (All hosts, 2026-11-18,
  the user's request) Only Python, GDScript, PHP and JS/TS/Svelte have a
  reader: a Java, C#, Go, Rust... host is grep only. Decided in a grilling
  session: a generic reader first, every link by name, for many languages
  at once; a dedicated reader for one language only when this backlog shows
  the generic one falls short on a real host (as ADR 0002 does for the
  TypeScript compiler). First languages: Java, C#, Go, Rust, Ruby, C, C++,
  Swift, Kotlin, by queries of ours, specified per language in
  `docs/readers.md`; their grammars pinned in the main dependencies. A call is
  linked only when its name has a single definition, the others counted as
  not attributed. A language is done on a public sample host: builds, 0
  dangling, `check` coverage, 3 queries compared with grep (ADR 0003). The
  sample hosts, pinned, in `docs/sample-hosts.md`, summed up in the README:
  protobuf, libsignal, gitea (and Django). T-0030; Go is read since T-0031
  (gitea), Rust since T-0032 (libsignal), Java since T-0033 (protobuf), C and
  C++ since T-0034 (protobuf), C# since T-0035 (protobuf), Ruby since
  T-0036 (protobuf), Swift since T-0037 (libsignal), Kotlin since T-0038
  (libsignal).

Settled by tickets (2026-11-18):

- **The tests that compare a whole message** stay outside the graph. [T-0029, wontfix]
  (Grid Zero) The tests are excluded from it.
- **A "where does X work" question needs a bench, not a query.** [T-0028, wontfix]
  (Grid Zero, 2026-11-02, prévisionniste) To know in which scenarios the aid
  acts, every scenario had to be played. The graph says who reads
  `PREVISIONNISTE`, not which data make it active (a weather window that
  contains line incidents). To be kept outside the graph.
- **The translation files are outside the graph.** [T-0027, wontfix] (Grid Zero, 2026-11-02)
  - `godot/i18n/*.po` are read by grep. Probably to be kept that way:
    `tools/i18n.py etat` already says what is missing.
- **`explain` does not say what it misses.** [T-0025] (Django, sample host,
  2026-11-18, T-0016) `explain query.py::QuerySet.filter` gives 3 callers,
  but grep finds hundreds of `.filter(` calls: a manager
  (`Model.objects.filter`) is a receiver whose type the reader does not
  know. The graph could count the unresolved calls by name in each body
  (the `check` sites have them) and show "plus N `.filter()` not
  attributed" so that the agent knows when to grep.
- **A function named with its arguments is not linked.** [T-0024] (4cast,
  2026-11-18, T-0015) Issue 48 writes `` `ndviRecent(geometrie, aujourdhui)` ``:
  the core's backticks take `name` and `name()` only, so `explain
  ndviRecent` names no issue. 4 such citations in 4cast. Taking any
  `(...)` would change Grid Zero's links (its snapshot).
- **A PHP file's top-level calls belong to nothing.** [T-0023] (4cast, 2026-11-18,
  T-0015) `api/index.php` routes at the top of the file (`route_zones($db,
  ...)`, `match` on `$chemin`): the PHP reader reads calls only in bodies, so
  `explain route_zones` shows no caller. The JS reader gives them to the
  file node; the PHP reader could do the same.
- **The calls in a Svelte component's markup are not read.** [T-0022] (4cast,
  2026-11-18, T-0015) Only the `<script>` goes to the grammar; the markup is
  blanked out. About 213 calls in the markup of 17 components
  (`onclick={() => rafraichir(1)}`, `{jourCourt(j.date)}`) are missed: 36 of
  the 77 component functions have no caller. The reader could parse each
  `{...}` of the markup as an expression, its calls belonging to the file.
  A component used as `<Mini />` is only an `imports` link, never a call.
- **A call in a test's callback belongs to the file.** [T-0021] (dpe, 2026-11-18, T-0014)
  `test('...', () => { compute(...) })`: the caller is `compute.test.mjs`,
  not the test, which is not a node. `explain compute` lists 20-odd test
  files rather than the tests.
- **The test harness's methods are linked by the name.** [T-0020] (4cast,
  2026-11-18, T-0015) `faux.de()`, `faux.vider()`... in `tests/api` (31
  sites, `ours?`): the right method, but INFERRED. Same cause as the methods
  of an object literal (dpe, above).
- **The methods of an object literal are not nodes.** [T-0020] (dpe, 2026-11-18, T-0014)
  dpe's UI tests build a page object (`return { async saisir(id, v) {...} }`)
  and call `p.saisir()`, `p.clic()`, `p.ep()`, `p.stocke()`: about 150 member
  calls classified `member`, linked to nothing. The imports would not catch
  them (the object is returned, not exported); the types would (ADR 0002).
  The JS reader could make a node of such a method, then link `x.m()` by the
  name as it does for class methods.
- **A Svelte prop called is `unknown`.** [T-0019] (4cast, 2026-11-18, T-0015)
  `let { onouvrir } = $props()` declares it at the top of the component,
  which `_declared` does not see (functions only): `onfini()`, `onouvrir()`,
  `onchoix()`, about ten sites. Nothing missed, the verdict only.
- **A re-exported npm name is `absent`, not `external`.** [T-0018] (dpe, 2026-11-18,
  T-0014) `ui_helpers.mjs` re-exports `VirtualConsole` from `jsdom`;
  `new VirtualConsole()` in `ui.test.mjs` follows the import to a name of
  ours that is not defined. One site; nothing missed.

Settled together (2026-11-05, T-0354):

- **A value exchanged between the two languages.** (T-0351) `"coupee"`,
  written by `InterconnectionFleet.settle_severed` and compared by
  `texte_d_interconnexion`; `"reparer_liaison"`, from the game's thread to
  the debrief. A `value` node per string written in Python and in GDScript:
  `search coupee`, `explain '"coupee"'`. Also covers the keys of the other
  messages (`"tiree"`, `"defi"` of the catalogue).
- **A field written by keyword.** (T-0351) `EngineState(...,
  interconnection_unavailable_reason=...)`: `Engine.step` writes it.
- **The scenarios' hints.** (T-0337) A `hint` node per `[[hints]]`, linked
  to the functions whose text it cites between « ».
- **The Moonshot journal.** A node per iteration, linked to the tickets it
  cites (« T-0350 à T-0352 » included).

Settled together (2026-11-03, commit « graphe : champs, clés de l'état,
alias d'import, tickets »):

- **A class has its extent, and its fields are nodes.**
  `explain GenSpec --source` prints the class; `explain
  EtatDeJeu.manque_prevu_tranche` says who writes it (`_prevoir_le_manque`)
  and who reads it, on the Python side when the receiver's type is known.
- **The keys of the state lead to the client.** `state.get("demand_mw")` or
  `state["demand_mw"]` in a GDScript script reads the field (by the name):
  the field `manque_prevu_tranche` leads to `_manque_prevu_text`.
- **A Python import alias is sure.** `aides_de_camp.PREVISIONNISTE`
  reads the constant of `simulation/game/aides.py` as EXTRACTED.
- **Tickets are nodes.** The code that cites `T-0307` leads to it by
  `cites`; a ticket leads by `names` to the functions it writes between
  backticks. `explain _rafales` says T-0307 and T-0328. They form their own
  community, so as not to merge those of the code.

- **Accents came out as « D?fi » when a program reads the output.**
  (2026-11-02, T-0310) `explain envoyer_defi` printed « D�fi du
  jour »: Python writes cp1252 into a pipe. The output switches to UTF-8
  outside a terminal.

- **A Python `X.name` read a GDScript variable.** (2026-11-02,
  tempête) `explain ecrire_le_catalogue` said it reads `graine` of
  `godot/menu/fond_menu.gd` "by name", for an `examen.graine`. The link by
  name now stays within its language.

Settled together (commit « graphe : variables, source, PHP, textes et
commentaires »):

- **Module variables and constants are not nodes.** `variable` and
  `constant` nodes, `reads` and `writes` links; `explain _tirage` says who
  writes it and who reads it.
- **The graph says where the code is, not what it contains.** Each body has
  its end line; `explain X --source` prints its lines.
- **`search` takes a name, not a line of code.** `def`, `func`, `class`,
  `function`, `const` and `var` at the head are removed.
- **The online service's PHP is outside the graph.** `tools/graphe_php.py`:
  functions, actions, calls; the client's `{"action": ...}` lead to the
  actions by `sends`.
- **A name written through its preload constant is not recognised.**
  `callers Progress.record` finds `godot/settings/progress.gd`.
- **A displayed text does not lead to its code.** The texts of `I18n.t`
  are stored on their function; `search "Réseau stable"` leads to
  `_update_ui_from_state`.
- **A concept said in French in the comments cannot be found.** The
  comment above each function is stored on it; `search clarte` finds the
  functions of daylight.
