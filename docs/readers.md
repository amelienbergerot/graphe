# The readers

A reader turns a host's files of one language into nodes, links and coverage sites, through `contribute(project)` (docs/contribution.md). Each is registered in `READERS` (`src/graphe.py`) under the name of its `graphe.toml` section, the key of its configuration and of its coverage in `graphe check`.

| Section | Reader | Languages | Suffixes |
|---|---|---|---|
| `python` | dedicated, `graphe_python.py` | Python | `.py` |
| `godot` | dedicated, `graphe_godot.py` | GDScript | `.gd` |
| `php` | dedicated, `graphe_php.py` | PHP | `.php` |
| `js` | dedicated, `graphe_js.py` | JavaScript, TypeScript, Svelte | `.js`, `.mjs`, `.ts`, `.svelte` |
| `go` | generic, `graphe_generic.py` | Go | `.go` |
| `rust` | generic, `graphe_generic.py` | Rust | `.rs` |
| `java` | generic, `graphe_generic.py` | Java | `.java` |
| `c` | generic, `graphe_generic.py` | C, C++ | `.c`, `.h`, `.cpp`, `.cc`, `.cxx`, `.hpp` |
| `csharp` | generic, `graphe_generic.py` | C# | `.cs` |
| `ruby` | generic, `graphe_generic.py` | Ruby | `.rb` |
| `swift` | generic, `graphe_generic.py` | Swift | `.swift` |

A **dedicated reader** knows its language's imports and types, and links a call for sure where it can. The **generic reader** (ADR 0003, GLOSSARY.md) reads every other language the same way, by its name alone.

## The generic reader

`src/graphe_generic.py`. A language is data only, a `Language`: its tree-sitter grammars by file suffix, a query of ours per grammar, its **common names**, the method names never linked from a call on a receiver, and two switches for C/C++'s macros, C#'s `#if` and Swift's newer syntax: `tolerant` (a file with error nodes is read, not skipped) and `erased` (a pattern blanked before parsing; ADR 0003's amendment). The reading, the owner of a call, the `Class.method` naming and the linking are written once.

### The capture convention

Every language's query captures the same names; a query is written from the `tags.scm` its grammar ships, and kept here, so that a grammar's upgrade does not change the graph silently.

| Capture | What it marks |
|---|---|
| `@function`, `@method`, `@class` | A definition (the whole node), with its `@name`. `@class` is a class, an interface, a struct, an enum, a trait, a Rust `impl`, a Ruby `module`, a Swift `actor` or `protocol`. |
| `@receiver` | Inside a `@method`: its type, when the method is declared outside it (Go's `func (r *T) M()`, Swift's `extension T`). |
| `@call` | A bare call `f()`, with `@name` the name called. |
| `@send` | A call on a receiver `x.m()`, a package `pkg.F()` or a path `T::f()`, with `@name` the method's name. |
| `@reference` | A use of a class that is not a call (`new C()`, `extends C`, Go's `T{}`), with `@name` the class. |

- A use belongs to the innermost definition that contains it; outside any, to its file.
- A `@function` inside a `@class` is a method of that class. A method's class is its `@receiver`, or else the innermost `@class` that contains it. A method is named `Class.method`.
- The definitions of one kind and name in one file are one node: Rust's `struct T` and its `impl T`, `impl Display for T`; Java's overloads `o(int)` and `o(String)`, one `A.o` (T-0033). Its line and extent are the first one's.

### Nodes

A node per file (`file`), function (`function`), method (`method`, `Class.method`) and class (`class`). Modules, packages and namespaces are not nodes. The ids carry the file's extension (`models/repo/repo.go` is `models_repo_repo_go`), so that `Foo.java` and `Foo.kt` never share an id; an id already taken gets `_2`, `_3`.

A file `contains` its definitions; a class `contains` its methods when they are in its file. Elsewhere (a Go method of a type of another file), the method's file contains it.

### Links and their confidence

Every link a use makes is by the name alone (`INFERRED`: `[by name]`, `?` in the answers), and made only when the name has **a single definition in the language**:

- `@call` and `@send` become `calls`, to the function or method of that bare name (`Save` for `T.Save`);
- `@reference` becomes `references`, to the class of that name;
- a `@send` of a common name is never linked;
- a call to its own definition (recursion) draws no link;
- no call is linked to another language: each language is its own registry entry, and sees only its own definitions.

A bare call and a send are marked alike: both are by name.

Every call or send is a coverage site, with its verdict:

| Verdict | Meaning | Linked |
|---|---|---|
| `ours?` | A single definition of that name in the language. | yes, `INFERRED` |
| `ambiguous` | Several definitions of that name. | no: `explain` counts it ("+ N calls named `f` the graph could not attribute: grep them", T-0025) |
| `common` | A send of a common name that the host defines. | no: counted by `explain` likewise |
| `external` | No definition of that name in the host (the standard library, a dependency, a builtin). | no |

A file that does not parse (any error node in its tree) is skipped and named on stderr; the build goes on. A `tolerant` language (C/C++, whose macros leave error nodes in valid code; C#, whose `#if` branches, both read, can; Swift, whose newer syntax the grammar lacks) reads it all the same. A host without the language's files gets no contribution at all, not even an empty coverage.

### Adding a language

1. Pin its grammar in the main dependencies (`pyproject.toml`, `uv add tree-sitter-<language>==<version>`).
2. Write its query in `graphe_generic.py` from the grammar's `tags.scm`, in the capture convention above: definitions with a body only (an abstract method or a signature would make each name ambiguous with its implementation).
3. Its `Language`: the name of its `graphe.toml` section, the grammar and query per suffix, a first list of common names; `tolerant` if valid code leaves error nodes, `erased` for what the grammar cannot read and blanks keep in place (C/C++, T-0034; C#'s `#if` lines, T-0035).
4. A snippet test at the seam `read(language, file, source)` (`tests/test_generic.py`): its definitions and its uses with their owners.
5. Its entry in `READERS` (`functools.partial(graphe_generic.contribute, graphe_generic.<LANGUAGE>)`).
6. Its sample host (docs/sample-hosts.md): build, no dangling link, `graphe check`; tune the common names from the most frequent sends linked by name; three queries compared with grep; its README row and its section here; what it misses in BACKLOG.md, naming the host.

A quirk the query cannot express is a `shortcut:` in its section here. A language that needs code of its own is the proof that it needs a dedicated reader (ADR 0003).

## Go

- **Section**: `go`. **Suffixes**: `.go`.
- **Grammar**: `tree-sitter-go` 0.25.0 (py-tree-sitter 0.26.1).
- **Nodes**: a `function` per `func f()`; a `method` `T.M` per `func (r T) M()`, `func (r *T) M()` and their generic forms (`*T[K]`), its class the receiver's type; a `class` per type declaration (`type T struct`, `interface`, and any other `type T ...`). An interface's method specs are not nodes: each would make its implementations' name ambiguous.
- **Links**: `f()` and `f[T](x)` are `@call`; `x.M()` and `pkg.F()` are `@send`, so a package's functions follow the common names. `T{}`, `&pkg.T{}` and an embedded field (`struct { Base }`) are `references` to `T`. All `INFERRED`.
- **Common names**: the standard library's names that one function of gitea would collect from every `filepath.Join`, `strings.NewReader`, `strings.HasPrefix`, `log.Fatal`, xorm's `cond.And` and `sess.Exec` (measured from `graphe check` on gitea, T-0031), and the methods of Go's common interfaces (`String`, `Error`, `Close`, `Read`, `Write`, `Len`...). The list is `GO.common`.
- **Quirks**: a type conversion `T(x)` is a call to `T`, so `external` (no function `T`). The methods of a type declared in several packages under one name are one name too (`Repository.Load...`): ambiguous unless unique.
- **Limits**:
  - `shortcut:` a file with one error node is skipped whole: grammar 0.25.0 knows neither Go 1.26's `new(expr)` nor generic methods, 47 of gitea's 3199 files (BACKLOG.md); to upgrade the grammar when one does, or to read the valid part of a tree.
  - `shortcut:` a call through a value (`handlers[name](ctx)`, a field holding a func) and a function passed as a value are not uses; to read if a host needs it.
  - `shortcut:` no imports: `pkg.F()` links to any `F` of the host, `strings.Join` included when the host defines one `Join` and `Join` is not common.
- **Sample host**: gitea (docs/sample-hosts.md).

## Rust

- **Section**: `rust`. **Suffixes**: `.rs`.
- **Grammar**: `tree-sitter-rust` 0.24.2 (py-tree-sitter 0.26.1).
- **Nodes**: a `function` per `fn f()` with a body; a `method` `T.f` per function of an `impl T`, `impl Tr for T`, `impl Tr for &'a T` (and their generic and `path::T` forms) or of a `trait T` (a default method); a `class` per `struct`, `enum`, `union`, `trait` and `impl`. A trait's signatures without a body are not nodes: each would make its implementations' name ambiguous.
- **Links**: `f()` is `@call`; `x.f()`, `T::f()` and `crate::m::f()` are `@send`, so a path follows the common names. `T { .. }` and `path::T { .. }` are `references` to `T`. All `INFERRED`.
- **Common names**: the standard library's and the usual crates' (tokio, futures, http) names that one function of libsignal would collect from every `Vec::with_capacity`, `std::future::ready`, `f.debug_struct(..).field`, `x.ok()` (measured from `graphe check` on libsignal, T-0032), and the methods of Rust's common traits (`new`, `default`, `clone`, `from`, `into`, `fmt`...). The list is `RUST.common`.
- **Quirks**: `Ok(x)`, `Some(x)`, `Err(e)` and a tuple struct `T(x)` are calls, `external` (no function of that name). The functions of one name in one file are one node: `fmt` of `impl Debug for T` and of `impl Display for T` is one `T.fmt`, the `fn f` of two `mod`s one `f` (libsignal: 513 merged in 89 files, T-0033).
- **Limits**:
  - `shortcut:` a macro's arguments are tokens to the grammar: a call inside `assert_eq!`, `vec![]`, `format!` is not a use (libsignal: 8604 macro invocations, BACKLOG.md); to parse a token tree as expressions when it parses.
  - `shortcut:` the classes of one name are one node per file only: a `struct T` and its `impl` in another file are two classes, so `T { .. }` is ambiguous (libsignal: 605 of 3250); `impl<T> Tr for T` draws a class `T`, `impl Tr for Vec<X>` a class `Vec` (BACKLOG.md); to merge a class's nodes across files.
  - `shortcut:` `T::f()` is linked by `f` alone, so `T::new()` is never linked (`new` is common) and `KeyPair::generate` is ambiguous between 6 types (BACKLOG.md); to link a path to its type's method if ADR 0003 allows it.
  - `shortcut:` a file with one error node is skipped whole: grammar 0.24.2 rejects `dyn 'a + Trait`, 1 of libsignal's 612 files (BACKLOG.md); to upgrade the grammar when one does, or to read the valid part of a tree.
- **Sample host**: libsignal (docs/sample-hosts.md).

## Java

- **Section**: `java`. **Suffixes**: `.java`.
- **Grammar**: `tree-sitter-java` 0.23.5 (py-tree-sitter 0.26.1).
- **Nodes**: a `class` per `class`, `interface`, `enum` and `record`; a `method` `C.m` per method with a body, and `C.C` per constructor; a method's class is the innermost class that contains it. An abstract method or an interface's signature is not a node: each would make its implementations' name ambiguous. The overloads of a class are one method.
- **Links**: `m()` is `@call`; `x.m()`, `C.m()` and `com.x.C.m()` are `@send`, so a static method follows the common names. `new C()`, `extends C`, `implements I` and an interface's `extends J` are `references` to the type, in their generic (`C<T>`) and qualified (`Outer.Inner`, `com.x.C`) forms, by the last name. All `INFERRED`.
- **Common names**: the JDK's names (and JRuby's `newString`) that one method of protobuf would collect from every `s.getBytes`, `clazz.getMethod`, `buffer.flip`, `map.keySet`, `s.startsWith` (measured from `graphe check` on protobuf, T-0033), and, guessed, the methods of the collections, `Object`, `String`, `Optional`, the streams, the threads, the boxed numbers and `Arrays` (`get`, `add`, `equals`, `toString`, `substring`, `orElse`, `println`, `parseInt`...). The list is `JAVA.common`.
- **Quirks**: an abstract method has no node, so `explain CodedInputStream.pushLimit` finds none: its implementations do (`ArrayDecoder.pushLimit`). A class named like another of the host, in any file, is ambiguous: generated code repeats its classes (`Builder`, `TestMessage`) in every file.
- **Limits**:
  - `shortcut:` a nested class is named by its own name: `X.Builder` and `Y.Builder` of one file are one class, their methods of one name one method; to name a nested class by its outer one if a host needs them apart.
  - `shortcut:` an anonymous class (`new Runnable() { public void run() {..} }`) is not a class: its methods are the enclosing class's (`A.run`), 325 such methods on protobuf; to make the anonymous body a `@class` if a host needs it.
  - `shortcut:` no imports nor types: `C.m()` is linked by `m` alone, so a static method named like another class's is ambiguous (BACKLOG.md, the item on Rust's `Type::f()`, which names Java's `C.f()` too); to link `C.m()` to the method `C.m` when `C` is a class of the host, if ADR 0003 allows it.
- **Sample host**: protobuf (docs/sample-hosts.md).

## C and C++

- **Section**: `c`, one family: a C++ call to a C function is linked. **Suffixes**: `.c` (the C grammar); `.h`, `.cpp`, `.cc`, `.cxx`, `.hpp` (the C++ grammar, which reads C headers too).
- **Grammars**: `tree-sitter-c` 0.24.2 and `tree-sitter-cpp` 0.23.4 (py-tree-sitter 0.26.1). Their `tags.scm` capture no call: the queries (`C_QUERY`, `CPP_QUERY`) are ours.
- **Nodes**: a `function` per function definition with a body, its name in any declarator (`char** f()`, `T& f()`); a `method` `C.m` per function defined in a class's body, and per `C::m`, `ns::C::m`, `C<T>::m` defined outside it (the innermost scope is the class), constructors (`C.C`), destructors (`C.~C`) and operators (`C.operator==`) included; a `class` per `class`, `struct`, `union` and `enum` with a body, and per `typedef struct { .. } T`. A prototype (`int f(int);`, a method declared in its class), a forward declaration (`class C;`) and `= default` are not nodes: each would make a name ambiguous between the `.h` and the file that defines it.
- **Links**: `f()` and `f<T>()` are `@call`; `x.m()`, `p->m()`, `C::m()` and `ns::f()` are `@send`, so a qualified call follows the common names. `new C()` and a base class (`class A : public B`) are `references` to the class, in their template (`C<T>`) and qualified (`ns::C`) forms, by the last name. All `INFERRED`.
- **Common names**: the standard library's names (and absl's `Status::message`) that one function of protobuf would collect from every `std::string(..)`, `v.emplace_back`, `s.append`, `v.reserve` (measured from `graphe check` on protobuf, T-0034), and, guessed, the methods of the containers, the strings, the smart pointers, `optional` and `std::`'s functions (`size`, `push_back`, `c_str`, `reset`, `move`, `make_unique`...). The list is `C.common`.
- **Quirks**:
  - A file that does not parse is read all the same (`Language.tolerant`): macros the grammar does not know leave an error node in 557 of protobuf's 1363 C/C++ files (765 once the macros below are erased: a constant erased in an expression leaves one), and a function still parses around most of them. A name the grammar inserts to recover (`enum : int {..}` reads as an enum with a missing name) is not a definition.
  - The attribute macros, upper case with an underscore and no arguments (`PROTOBUF_EXPORT`, `UPB_INLINE`, `ABSL_ATTRIBUTE_LIFETIME_BOUND`, `PROTOBUF_NONNULL`), are blanked before the parse (`Language.erased`, lines and columns kept): the grammar would read `class PROTOBUF_EXPORT Descriptor {` as a function `Descriptor`, `f() const ABSL_ATTRIBUTE_LIFETIME_BOUND {` as no function (834 on protobuf). On protobuf: 2542 classes and 26202 functions and methods, against 2208 and 23811 unerased.
  - A gtest test (`TEST_F(Suite, Name) { .. }`) parses as a function `TEST_F`: a file's tests are one function `TEST_F` (or `TEST`, `TEST_P`), which calls what they call.
  - A `.h` is C++ whatever its language: protobuf's Objective-C headers (`objectivec/*.h`, 41 files) are read, 49 definitions.
  - Calls to macros are calls: `EXPECT_EQ`, `UPB_SIZE`, `static_assert_64bit` are `external`.
- **Limits**:
  - `shortcut:` a scope is taken for a class: `void internal::Helper() {}` is the method `internal.Helper`; to tell a namespace from a class if a host needs it.
  - `shortcut:` a constant (`INT_MAX`) or a class (`struct MY_POINT {`) named like a macro is erased too, and a macro with arguments (`PROTOBUF_ALIGNAS(8)`) is not; a class whose declaration an `#ifdef` cuts (`class PROTOBUF_EXPORT` / `#ifdef` / `ABSL_ATTRIBUTE_WARN_UNUSED` / `#endif` / `Arena final {`, protobuf's `Arena`) is lost (BACKLOG.md); to tell them apart if a host loses code to one.
  - `shortcut:` the classes and functions of one name are one node per file only: an amalgamation (`php-upb.c`, `ruby-upb.c`, which repeat upb) makes each name it repeats ambiguous (BACKLOG.md).
  - `shortcut:` no imports nor types: `C::m()` is linked by `m` alone, as Java's `C.m()`.
- **Sample host**: protobuf (docs/sample-hosts.md).

## C#

- **Section**: `csharp`. **Suffixes**: `.cs`.
- **Grammar**: `tree-sitter-c-sharp` 0.24.0 (py-tree-sitter 0.26.1). Its `tags.scm` captures only the calls on a receiver (`reference.send`); its wheel stores its queries outside its package (`site-packages/tree_sitter_c-sharp/queries/`), which nothing reads: the query (`CSHARP_QUERY`) is ours.
- **Nodes**: a `class` per `class`, `interface`, `struct`, `enum` and `record`; a `method` `C.M` per method with a body (a block or `=> expr`), and `C.C` per constructor; a method's class is the innermost class that contains it. An abstract method or an interface's signature is not a node, as Java's. The overloads of a class are one method. Namespaces are not nodes.
- **Links**: `F()` and `F<T>()` are `@call`; `x.M()`, `x?.M()`, `this.M()`, `C.M()` and `pb::C.M()` are `@send`, so a static method follows the common names. `new C()` and a base or interface (`class A : B, I`) and a record's primary-constructor base (`record R(int X) : B(X)`) are `references` to the type, in their generic (`C<T>`), qualified (`A.B.C`, `global::System.C`) and aliased (`pb::C`) forms, by the last name. All `INFERRED`.
- **Common names**: the BCL's names that one method of protobuf would collect from every `builder.Append` (a `StringBuilder`, linked to `BufferSegment.Append`), `enumerator.MoveNext`, `typeof(T).GetProperty` (measured from `graphe check` on protobuf, T-0035), and, guessed, the methods of `object`, the strings, the collections, LINQ, the streams and reflection (`ToString`, `Add`, `TryGetValue`, `Select`, `WriteLine`, `GetMethod`...). The list is `CSHARP.common`.
- **Quirks**:
  - The preprocessor lines `#if`, `#elif`, `#else` and `#endif` are blanked before the parse (`Language.erased`): protobuf's generated code cuts its base list with one (`: pb::IMessage<T>` / `#if !GOOGLE_PROTOBUF_REFSTRUCT_COMPATIBILITY_MODE` / `, pb::IBufferMessage` / `#endif`), which the grammar does not parse: 44 of its 224 files skipped, 2 once the lines are erased. Both branches are read.
  - A file that does not parse is read all the same (`Language.tolerant`): the 2 left on protobuf (`Unsafe.AddByteOffset(ref a, i) = x;`, and `var e =` whose two erased branches then follow each other) lose no method to their class. On protobuf: skipped 44 / 0, classes 242 / 769, methods 2021 / 6422, as is / erased and tolerant; tolerant alone reads 1285 methods as functions, their class lost in the base list.
  - A property's accessors are no definitions: the calls of `get`, `set` and `=> expr` belong to the class, so `callers ProtoPreconditions.CheckNotNull` lists generated classes (`Person:56`) for their setters.
  - A `partial void OnConstruction();` has no body: its 364 calls in generated code are `external`. `nameof(X)` is a call, `external` (102 on protobuf).
- **Limits**:
  - `shortcut:` a property's accessors, a local function, an operator and a destructor are no definitions, their calls belong to the class (or the method); to capture them if a host's `explain` needs them.
  - `shortcut:` both branches of an `#if` are read: their calls are counted twice, their definitions of one name are one; to keep one branch if a host's definitions differ between them.
  - `shortcut:` a C# file that does not parse is read, no longer named on stderr; to name it if a host's garbage shows.
  - `shortcut:` a nested class is named by its own name (generated code's `Types.PhoneType`, every `Types`), and `C.M()` is linked by `M` alone, as Java's; to name a nested class by its outer one, and link `C.M()` to `C.M`, if a host needs it (BACKLOG.md).
  - `shortcut:` a `partial class` is one class per file it spans: `Any` (`Any.pb.cs`, `AnyPartial.cs`) is two classes, so a reference to it is ambiguous (125 class names in several of protobuf's `.cs` files, partials and the copied tests); to merge a partial class's files if a host's references to it matter.
- **Sample host**: protobuf (docs/sample-hosts.md).

## Ruby

- **Section**: `ruby`. **Suffixes**: `.rb`.
- **Grammar**: `tree-sitter-ruby` 0.23.1 (py-tree-sitter 0.26.1). Its `tags.scm` takes a bare identifier for a call (`#is-not? local`, which py-tree-sitter does not apply): a local variable would be a call. The query (`RUBY_QUERY`) is ours.
- **Nodes**: a `class` per `class` and `module` (a module holds its `def self.m`, and names a namespace), and per `X.class_eval do` block, which reopens `X` (protobuf's `well_known_types.rb`: `Any.pack`, `Timestamp.to_time`); a `method` `C.m` per `def m` and `def self.m` in it, the two one method if both exist; a `function` per `def` outside any. A method's class is the innermost one: `module Google::Protobuf` `def self.encode` is `Protobuf.encode`. A `class << self` is no class, its methods its enclosing class's. Operators and setters are methods too (`C.==`, `C.x=`); `def obj.m` on another object than `self` is a method of the class around it, or a function `m`.
- **Links**: `b()` and `c arg` (a `call` without receiver) are `@call`; `x.c`, `self.c`, `x&.c` and `A::B.c` are `@send`. `C.new` and a superclass (`class A < B`) are `references` to the class, bare or scoped (`Google::Protobuf::B`), by the last name; `C.new` is a send `new` too, a common name. All `INFERRED`.
- **Common names**: `new` (892 sends `C.new`, 9 `def self.new` in protobuf's ffi), `each` (38) and `pack` (6 of its 9 sends are `Array#pack`, linked to `Any.pack`), measured on protobuf (T-0036), and, guessed, the methods of `Object`, the conversions, `Enumerable`, `Array`, `Hash`, `String` and `IO` (`to_s`, `inspect`, `dup`, `map`, `empty?`, `join`, `puts`...). A name whose sends on protobuf are mostly its own is left out: `push`, `pop`, `first`, `delete`, `keys` (its `RepeatedField` and `Map` mirror `Array` and `Hash`), `eql?` (its messages'). The list is `RUBY.common`.
- **Quirks**:
  - Every protobuf `.rb` parses: neither `tolerant` nor `erased`.
  - A message's fields are read through `method_missing` (`m.repeated_string`, 171 sends): `external`, no definition.
- **Limits**:
  - `shortcut:` a bare `b` is no call: it may be a local variable, which only the grammar's `locals.scm` tells; at least 17 bare calls to protobuf's methods are missed (`inspect`, `reset_allocations`); to tell a variable from a call if a host's `explain` misses them.
  - `shortcut:` an `attr_reader`, `attr_accessor`, `alias`, `define_method` is no definition, its readers' sends `external` (4 `attr_*` on protobuf); to capture them if a host's `explain` needs them.
  - `shortcut:` a class reopened in several files is one class per file (12 names on protobuf: `Descriptor`, `RepeatedField`, `Google`, `Protobuf`), so a reference to it is ambiguous; to merge them if a host's references matter.
  - `shortcut:` the methods of a class built by `Class.new(..) do` belong to the enclosing class: the 41 methods of the message class `ffi/message.rb` builds are `Descriptor`'s (`Descriptor.encode`); to name such a class after what it is assigned to, code of its own: a dedicated reader (BACKLOG.md).
  - `shortcut:` a setter call `x.y = v` (339 on protobuf) is a send `y`, not `y=`: a hand-written `def y=` gets no caller, a getter `y` its callers (protobuf has none, its fields go through `method_missing`); to name the send `y=` if a host's setters need callers.
  - `shortcut:` `C.m` is linked by `m` alone, as Java's `C.m()`; `include M` and `extend M` are calls, not references to `M`; to link `C.m` to `C`'s `m`, and `include M` to `M`, if a host needs them.
- **Sample host**: protobuf (docs/sample-hosts.md).

## Swift

- **Section**: `swift`. **Suffixes**: `.swift`.
- **Grammar**: `tree-sitter-swift` 0.7.4 (py-tree-sitter 0.26.1). Its `tags.scm` captures no call. The query (`SWIFT_QUERY`) is ours.
- **Nodes**: a `class` per `class`, `struct`, `enum`, `actor` (one `class_declaration` in the grammar) and `protocol`. An `extension T` is no class: its methods are `T`'s by `@receiver`, as Go's, so that a type extended in several files stays one class and its references are linked (`extension Foo.Bar` and `extension Array<T>` extend `Bar` and `Array`). A type is named by its last name, generic or not. A `method` `C.m` per `func`, `init` (`C.init`) and computed property (`var p: T { .. }`, `C.p`) directly in a type's or an extension's body; a `function` per `func` at the top of a file. A protocol's requirements (no body) are not captured.
- **Links**: `b()` is a `@call`; `x.c()`, `self.c()`, `y?.c()`, `C.s()` and an implicit member `.c()` (`.init()`, `.success(x)`) are `@send`. A call to a capitalised name, `C(..)`, `Foo.Bar(..)`, `Array<Int>()`, is a `references` to the type by its last name (Swift's naming convention), as is an inherited type or protocol (`class C: B, P`, `class PinHash: NativeHandleOwner<P>`: 60 subclasses reference libsignal's `NativeHandleOwner`). All `INFERRED`.
- **Common names**: `init` (611 sends: `self.init`, `.init`, `super.init`), `append` (71, `Data`'s), `combine` (3 of its 4 sends `Hasher.combine`, linked to `GroupSendEndorsement.combine`) and `withCString` (`String`'s, which libsignal wraps on `Optional`), measured on libsignal (T-0037), and, guessed, the standard library's collections, sequences, `Codable`, `Hashable` and unsafe pointers (`map`, `contains`, `encode`, `hash`, `withUnsafeBytes`...). `remove` is left out: its one send on libsignal is its own `svrB.remove()`. The list is `SWIFT.common`.
- **Quirks**:
  - `tolerant`: the grammar does not parse 10 of libsignal's 218 files (parameter packs `repeat (each T)`, `case .self`, `catch E.c(_:)`, `() = try x`); read all the same, they lose no definition (ADR 0003's amendment).
  - A computed property is a method so that its calls have their owner (577 on libsignal, 670 calls that would be their class's); reading `x.p` is no call, so it has no caller. It made 26 sites ambiguous (`accessKey`, a closure parameter `body`).
- **Limits**:
  - `shortcut:` a nested function, an operator (`static func ==`) and a subscript are no definitions, their calls their enclosing definition's; a stored property's initial value (`let x = f()`) and observers (`didSet`) call from the class; to capture them if a host's `explain` needs them.
  - `shortcut:` a capitalised call is taken for a type, a lower-case one for a function; an enum case with a payload `.c(x)` is a send `c`; to tell them apart by their definitions if a host breaks the convention.
  - `shortcut:` the grammar reads `defer { }` as a call `defer`, and the standard `withUnsafePointer(to:)` and `withUnsafeMutablePointer(to:)` would be linked to a host's method of that name (libsignal's, 24 bare calls, all the standard's): the query drops these three names, so a host's own bare function so named gets no caller; to drop them by their `to:` label if a host defines one.
  - `shortcut:` a Swift file that does not parse is not named on stderr (`tolerant`); to name it if a host's garbage shows.
- **Sample host**: libsignal (docs/sample-hosts.md).

## The dedicated readers

Each is specified in its module's docstring.

- **Python**, `graphe_python.py`: the `ast`, a call resolved by its receiver's type (annotations, constructions, returns), by the name alone otherwise; a cache of each file's definitions (T-0026).
- **GDScript**, `graphe_godot.py`: by patterns, a `preload` constant designates its script, a variable typed by it or made by `X.new()` sends its calls there; `check` recounts the calls.
- **PHP**, `graphe_php.py`: by patterns, its functions, the actions of a `switch ($action)`, the calls of the file's top (T-0023).
- **JavaScript, TypeScript, Svelte**, `graphe_js.py`: tree-sitter, ES imports and re-exports followed, `new C()` and `f()` assigned typed, by the name otherwise; a Svelte component's script and markup (T-0014, T-0015, T-0022).
