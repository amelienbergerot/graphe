# The readers

A reader turns a host's files of one language into nodes, links and coverage sites, through `contribute(project)` (docs/contribution.md). Each is registered in `READERS` (`src/graphe/readers.py`) under the name of its `graphe.toml` section, the key of its configuration and of its coverage in `graphe check`, and its suffixes in `SUFFIXES`, derived from its grammars for a generic language. A build runs the readers that have files in processes of their own, one each, when those beside the largest have 200 files or more (T-0088, T-0093, ADR 0005): a reader's module imports neither networkx nor `graphe.cli`, and its contribution pickles (dictionaries, lists, strings, numbers).

| Section | Reader | Languages | Suffixes |
|---|---|---|---|
| `python` | dedicated, `graphe/python.py` | Python | `.py` |
| `godot` | dedicated, `graphe/godot.py` | GDScript | `.gd` |
| `js` | dedicated, `graphe/js.py` | JavaScript, TypeScript, JSX, TSX, Svelte, Vue | `.js`, `.mjs`, `.jsx`, `.ts`, `.tsx`, `.svelte`, `.vue` |
| `go` | generic, `graphe/generic.py` | Go | `.go` |
| `rust` | generic, `graphe/generic.py` | Rust | `.rs` |
| `java` | generic, `graphe/generic.py` | Java, Kotlin | `.java`, `.kt` |
| `c` | generic, `graphe/generic.py` | C, C++ | `.c`, `.h`, `.cpp`, `.cc`, `.cxx`, `.hpp` |
| `csharp` | generic, `graphe/generic.py` | C# | `.cs` |
| `ruby` | generic, `graphe/generic.py` | Ruby | `.rb` |
| `swift` | generic, `graphe/generic.py` | Swift | `.swift` |
| `php` | generic, `graphe/generic.py` | PHP | `.php` |

A **dedicated reader** knows its language's imports and types, and links a call for sure where it can. The **generic reader** (ADR 0003, GLOSSARY.md) reads every other language the same way, by its name alone.

## The generic reader

`src/graphe/generic.py`. A language is data only, a `Language`: its tree-sitter grammars by file suffix, a query of ours per grammar, its **common names**, the method names never linked from a call on a receiver, two switches for C/C++'s macros, C#'s `#if`, Swift's and Go's newer syntax and Rust's `dyn 'a + Trait`: `tolerant` (a file with error nodes is read, not skipped) and `erased` (a pattern blanked before parsing; ADR 0003's amendment), and `apart` (a bare call is linked to a function only, a send to a method only: PHP's, T-0044). The reading, the owner of a call, the `Class.method` naming and the linking are written once.

### The capture convention

Every language's query captures the same names; a query is written from the `tags.scm` its grammar ships, and kept here, so that a grammar's upgrade does not change the graph silently.

| Capture | What it marks |
|---|---|
| `@function`, `@method`, `@class` | A definition (the whole node), with its `@name`. `@class` is a class, an interface, a struct, an enum, a trait, a Rust `impl`, a Ruby `module`, a Swift `actor` or `protocol`, a Kotlin `object`. |
| `@receiver` | Inside a `@method`: its type, when the method is declared outside it (Go's `func (r *T) M()`, Swift's `extension T`, Kotlin's extension function `fun T.m()`). |
| `@call` | A bare call `f()`, with `@name` the name called. |
| `@send` | A call on a receiver `x.m()`, a package `pkg.F()` or a path `T::f()`, with `@name` the method's name. |
| `@extension` | On a `@class` that only extends a type (Rust's `impl`): the class is the host's only if another capture declares it, in any file (`struct`, `enum`, `trait`). |
| `@qualifier` | Inside a `@send`, optional: what it is sent on (`T` of `a::T::f()`, `C` of `C.f()`; Rust, Java, Kotlin). Its last name is kept when it is a path of names, generic arguments dropped (`Vec::<u8>`); `f().g()` and `new C().g()` have none. |
| `@reference` | A use of a class that is not a call (`new C()`, `extends C`, Go's `T{}`), with `@name` the class. |
| `@abstract` | A method without a body, with its `@name` (T-0081): Java's abstract or an interface's method, a Swift protocol's `func` requirement. Named `Class.method` as a method. |
| `@base` | On a `@reference`, a base list's (`extends B`, `implements I`, Swift's `: P`, Kotlin's supertypes): its heir is the `@receiver` when there is one (Swift's `extension B: P`), or else the class that holds it. |
| `@action` | An entry point's action (PHP's `case 'x':`, T-0045), with `@name` the action: a definition named as it is, in no class. |

- A use belongs to the innermost definition that contains it; outside any, to its file.
- An `@action` inside any definition is none (a function's own `switch`, one nested in an action): its uses stay that definition's. An `@action` holding nothing past its name (`case 'liste':`, then `case 'relister':`) leads to the next one.
- A `@function` inside a `@class` is a method of that class. A method's class is its `@receiver`, or else the innermost `@class` that contains it. A method is named `Class.method`.
- A `@class` inside a `@class` is named `Outer.Inner`, its methods `Outer.Inner.m` (T-0043), so that the nested classes of one name in one file (each generated message's `Builder`) stay apart; a class inside a method is named after the method's class (`A.Local`). A use still names a class by its last name: `new Outer.Inner()` and `new Inner()` reference every class `Inner`, nested or not. `explain Inner.m` designates `Outer.Inner.m`, or asks to pick among the classes `Inner` (`graphe.find`). A `@receiver` is a last name (`Inner`), so a method declared outside its nested class (C++'s `Outer::Inner::m`, Swift's `extension Outer.Inner`, Kotlin's `fun Outer.Inner.f()`) is `Inner.m`: the language's section says where.
- The definitions of one kind and name in one file are one node: Rust's `struct T` and its `impl T`, `impl Display for T`; Java's overloads `o(int)` and `o(String)`, one `A.o` (T-0033). Its line and extent are the first one's.

### Nodes

A node per file (`file`), function (`function`), method (`method`, `Class.method`), declaration (`abstract`, `Class.method`, its id `<file>_abstract_<name>`, so that a method's id never moves, T-0081), class (`class`) and action (`action`, its id `<file>_action_<name>`, its label its bare name). Modules, packages and namespaces are not nodes. The ids carry the file's extension (`models/repo/repo.go` is `models_repo_repo_go`), so that `Foo.java` and `Foo.kt` never share an id; an id already taken gets `_2`, `_3`.

A file `contains` its definitions; a class `contains` its methods when they are in its file. Elsewhere (a Go method of a type of another file), the method's file contains it.

### Links and their confidence

Every link a call, a send or a reference makes is by the name alone (`INFERRED`: `[by name]`, `?` in the answers), and made only when the name has **a single definition in the language**, but for a qualified send (below):

- `@call` and `@send` become `calls`, to the function or method of that bare name (`Save` for `T.Save`); in an `apart` language (PHP, T-0044), a `@call` to a function only, a `@send` to a method only;
- `@reference` becomes `references`, to the class of that name;
- a `@send` of a common name is never linked;
- a `@send` whose `@qualifier` names a class of the host (T-0080: `DeviceId::new()`, `Circle.create()`) has for candidates only the methods `f` of the classes of that name the host declares (not only `@extension`), in any file (a Rust `impl` apart from its `struct`), a common name too: linked when one is left, by name (`INFERRED`: the class is found by its name, no import is read), `ambiguous` when several (two classes `Line`); when none (a static method the class inherits), the name alone decides, as above. A variable named like a class (`Foo foo` is fine, `Foo Foo` takes the class) is taken for it;
- a method `overrides` the declaration (`abstract`) of its name in its class or in a class its base list names directly, by the bare names (`INFERRED`), the base lists of a class gathered from all its files (Swift's extensions); a declaration settles a tie only (T-0081): a call whose concrete candidates are several and all override one declaration of their name, or that has no concrete candidate and one declaration, is linked to that declaration, by name; a single concrete candidate is linked as before, a declaration beside it or not;
- `callers` of a method lists the callers of the declarations it `overrides` too, marked `?` (a call to `Shape.area` may run `Circle.area`); a class's bases are found by its whole name (two nested `ListenerBridge`s keep their own), a base by its bare name;
- `shortcut:` by the name, not the signature: a concrete `f()` beside an `abstract f(int)` of its class overrides it; to compare the parameters if a host's overloads are linked to their abstract sibling;
- `shortcut:` the direct bases only (`C extends A implements I`, where `A` leaves `I.m` abstract, does not override `I.m`), and declarations in Java and Swift only (C#'s, Kotlin's, Rust's trait signatures, Go's interface specs and PHP's are none); to walk the bases, or capture a language's, when a host's calls through one stay ambiguous;
- a call to its own definition (recursion) draws no link;
- no call reaches an action; an action without a body `dispatches` to the case right after it, if that is an action (not past a `default:` or another case, nor into another switch) (`EXTRACTED`: the syntax says it, no name is guessed; no coverage site);
- no call is linked to another language: each language is its own registry entry, and sees only its own definitions; a family is one entry (C and C++, `c`; Java and Kotlin, `java`), each file read by its own grammar.

A bare call and a send are marked alike: both are by name.

Every call or send is a coverage site, with its verdict:

| Verdict | Meaning | Linked |
|---|---|---|
| `ours?` | A single definition of that name in the language, or a single method of that name in the classes a send's qualifier names (T-0080), or the one declaration all its candidates override (T-0081). | yes, `INFERRED` |
| `ambiguous` | Several definitions of that name. | no: `explain` counts it ("+ N calls named `f` the graph could not attribute:", then "between K definitions", with the candidates when five at most, T-0025, T-0074) |
| `common` | A send of a common name that the host defines. | no: counted by `explain` likewise ("on a common name") |
| `external` | No definition of that name in the host (the standard library, a dependency, a builtin). | no |

A file is a generated file (T-0079) when its leading comments, before the first code (PHP's `<?php` skipped), carry a known marker: protobuf's compiler ("Generated by the protocol buffer compiler.  DO NOT EDIT!", every language it writes) or Go's convention (a whole line `// Code generated ... DO NOT EDIT.`), `GENERATED` in `generic.py`, one pattern for every language. The contribution lists it (`generated`); its links are unchanged. The leading comments are those of the tree `read` parses, the file parsed once (T-0087). The same text below the first code (protoc's own generators, which write it) marks nothing.

A file that does not parse (any error node in its tree) is skipped and named on stderr; the build goes on. A `tolerant` language (C/C++, whose macros leave error nodes in valid code; C#, whose `#if` branches, both read, can; Swift and Go, whose newer syntax the grammar lacks; Rust, whose grammar rejects `dyn 'a + Trait`) reads it all the same. A host without the language's files gets no contribution at all, not even an empty coverage.

### Adding a language

1. Pin its grammar in the main dependencies (`pyproject.toml`, `uv add tree-sitter-<language>==<version>`).
2. Write its query in `graphe/generic.py` from the grammar's `tags.scm`, in the capture convention above: definitions with a body, and the methods without one as `@abstract` with the base lists as `@base` (T-0081), which settle a tie only.
3. Its `Language`: the name of its `graphe.toml` section, the grammar and query per suffix, a first list of common names; `tolerant` if valid code leaves error nodes, `erased` for what the grammar cannot read and blanks keep in place (C/C++, T-0034; C#'s `#if` lines, T-0035); `apart` if a bare call can never be a method (PHP, T-0044).
4. A snippet test at the seam `read(language, file, source)` (`tests/test_generic.py`): its definitions, its uses with their owners, and whether the file is generated.
5. Its entry in `READERS` (`functools.partial(generic.contribute, generic.<LANGUAGE>)`, `src/graphe/readers.py`); its suffixes follow from its grammars.
6. Its small host in `tests/fixtures/` and its links' snapshot (docs/contribution.md, T-0073). Its sample host (docs/sample-hosts.md): build, no dangling link, `graphe check`; tune the common names from the most frequent sends linked by name; three queries compared with grep; its README row and its section here; what it misses in BACKLOG.md, naming the host.

A quirk the query cannot express is a `shortcut:` in its section here. A language that needs code of its own is the proof that it needs a dedicated reader (ADR 0003).

## Go

- **Section**: `go`. **Suffixes**: `.go`.
- **Grammar**: `tree-sitter-go` 0.25.0 (py-tree-sitter 0.26.1).
- **Nodes**: a `function` per `func f()`; a `method` `T.M` per `func (r T) M()`, `func (r *T) M()` and their generic forms (`*T[K]`), its class the receiver's type; a `class` per type declaration (`type T struct`, `interface`, and any other `type T ...`). An interface's method specs are not nodes: each would make its implementations' name ambiguous. Go nests no type in another: a type declared in a function keeps its own name, nothing changed by T-0043 (gitea's graph identical).
- **Links**: `f()` and `f[T](x)` are `@call`; `x.M()` and `pkg.F()` are `@send`, so a package's functions follow the common names. `T{}`, `&pkg.T{}` and an embedded field (`struct { Base }`) are `references` to `T`. All `INFERRED`.
- **Common names**: the standard library's names that one function of gitea would collect from every `filepath.Join`, `strings.NewReader`, `strings.HasPrefix`, `log.Fatal`, xorm's `cond.And` and `sess.Exec` (measured from `graphe check` on gitea, T-0031), and the methods of Go's common interfaces (`String`, `Error`, `Close`, `Read`, `Write`, `Len`...). The list is `GO.common`.
- **Quirks**:
  - A type conversion `T(x)` is a call to `T`, so `external` (no function `T`). The methods of a type declared in several packages under one name are one name too (`Repository.Load...`): ambiguous unless unique.
  - `tolerant`: grammar 0.25.0 knows neither Go 1.26's `new(expr)` nor generic methods; 47 of gitea's 3199 files have an error node, read all the same: no garbage name among their definitions (T-0039).
- **Limits**:
  - `shortcut:` a generic method (`func (f *Flash) Error[T ...]`, 7 on gitea) is lost in its error node: no node, its calls its file's, its callers not linked to it; to upgrade the grammar when one knows them (BACKLOG.md).
  - `shortcut:` a Go file that does not parse is not named on stderr (`tolerant`); to name it if a host's garbage shows.
  - `shortcut:` a call through a value (`handlers[name](ctx)`, a field holding a func) and a function passed as a value are not uses; to read if a host needs it.
  - `shortcut:` no imports: `pkg.F()` links to any `F` of the host, `strings.Join` included when the host defines one `Join` and `Join` is not common.
- **Sample host**: gitea (docs/sample-hosts.md).

## Rust

- **Section**: `rust`. **Suffixes**: `.rs`.
- **Grammar**: `tree-sitter-rust` 0.24.2 (py-tree-sitter 0.26.1).
- **Nodes**: a `function` per `fn f()` with a body; a `method` `T.f` per function of an `impl T`, `impl Tr for T`, `impl Tr for &'a T` (and their generic and `path::T` forms) or of a `trait T` (a default method); a `class` per `struct`, `enum`, `union`, `trait` and `impl`. A trait's signatures without a body are not nodes: each would make its implementations' name ambiguous. A `mod` is no class: a type or an `impl` in a module keeps its own name (T-0043); only a type declared in a function of an `impl T` is nested, `T.L`.
- **Links**: `f()` is `@call`; `x.f()`, `T::f()` and `crate::m::f()` are `@send`, so a path follows the common names, unless it names a class of the host: `DeviceId::new()` goes to `DeviceId.new`, `new` common or not (T-0080; libsignal: 2330 calls more, `DeviceId::new` 184 sites). A type the host only implements a trait for, `impl From<X> for HashMap<K, V>`, is no class of the host (`@extension`): `HashMap::from([..])` is std's (libsignal: 30 sites). `T { .. }` and `path::T { .. }` are `references` to `T`. All `INFERRED`.
- **Common names**: the standard library's and the usual crates' (tokio, futures, http) names that one function of libsignal would collect from every `Vec::with_capacity`, `std::future::ready`, `f.debug_struct(..).field`, `x.ok()` (measured from `graphe check` on libsignal, T-0032), and the methods of Rust's common traits (`new`, `default`, `clone`, `from`, `into`, `fmt`...). The list is `RUST.common`.
- **Quirks**:
  - `Ok(x)`, `Some(x)`, `Err(e)` and a tuple struct `T(x)` are calls, `external` (no function of that name). The functions of one name in one file are one node: `fmt` of `impl Debug for T` and of `impl Display for T` is one `T.fmt`, the `fn f` of two `mod`s one `f` (libsignal: 513 merged in 89 files, T-0033).
  - `tolerant`: grammar 0.24.2 rejects a lifetime first in a trait object (`Box<dyn 's + FnOnce(..)>`), 1 of libsignal's 612 files; read all the same, it loses no definition (T-0040).
- **Limits**:
  - `shortcut:` a macro's arguments are tokens to the grammar: a call inside `assert_eq!`, `vec![]`, `format!` is not a use (libsignal: 8604 macro invocations, BACKLOG.md); to parse a token tree as expressions when it parses.
  - `shortcut:` the classes of one name are one node per file only: a `struct T` and its `impl` in another file are two classes, so `T { .. }` is ambiguous (libsignal: 605 of 3250); `impl<T> Tr for T` draws a class `T`, `impl Tr for Vec<X>` a class `Vec` (BACKLOG.md); to merge a class's nodes across files.
  - `shortcut:` a std type the host also declares is taken for the host's: libsignal's own `struct Duration` takes about 42 of its 50 `Duration::from_millis` sites, std's; to read the `use`s if a host's `callers` suffer.
  - `shortcut:` `Self::f()` names no class, so it is linked by `f` alone; to take the `impl`'s type if a host's `explain` needs it. `KeyPair::generate` stays ambiguous: 6 `struct KeyPair` each define it (the modules are no classes).
  - `shortcut:` a Rust file that does not parse is not named on stderr (`tolerant`); to name it if a host's garbage shows.
- **Sample host**: libsignal (docs/sample-hosts.md).

## Java

- **Section**: `java`, one family with Kotlin (T-0042): a Kotlin call to a Java method is linked, and the reverse. **Suffixes**: `.java` (and Kotlin's, below). A host's `[kotlin]` section, as its `[java]` one, has no key a generic reader reads: it was ignored and still is; `graphe check` gives Kotlin's sites under `java`.
- **Grammar**: `tree-sitter-java` 0.23.5 (py-tree-sitter 0.26.1).
- **Nodes**: a `class` per `class`, `interface`, `enum` and `record`; a `method` `C.m` per method with a body, and `C.C` per constructor; a method's class is the innermost class that contains it. A nested class is `Outer.Inner` (T-0043): each generated message's `Builder` is `TestMessage.Builder`, so a file's `Builder`s are apart (protobuf: 29 -> 74 `Builder` classes in 12 files, 692 nodes more), and their methods of one name are two (`build`, `mergeFrom`): 48 classes more: the 63 declarations that shared their name in their file (15 names: `Builder` in 12 files, `MethodInvoker`, `ReflectionInvoker`, `Converter`) now apart. A call to `build` was already ambiguous across protobuf's files: its `java` coverage is identical. An abstract method or an interface's signature is an `abstract` node `C.m` (T-0081), a `native` one none (its body is in C or Rust: libsignal's JNI); a method `overrides` the one of its class or of a class it `extends` or `implements` directly. The overloads of a class are one method, its abstract ones one declaration.
- **Links**: `m()` is `@call`; `x.m()`, `C.m()` and `com.x.C.m()` are `@send`, so a static method follows the common names, unless `C` is a class of the host: then it goes to `C.m` (T-0080; protobuf: 3003 calls more; libsignal 192). `new C()`, `extends C`, `implements I` and an interface's `extends J` are `references` to the type, in their generic (`C<T>`) and qualified (`Outer.Inner`, `com.x.C`) forms, by the last name. All `INFERRED`.
- **Common names**: the JDK's names (and JRuby's `newString`) that one method of protobuf would collect from every `s.getBytes`, `clazz.getMethod`, `buffer.flip`, `map.keySet`, `s.startsWith` (measured from `graphe check` on protobuf, T-0033), and, guessed, the methods of the collections, `Object`, `String`, `Optional`, the streams, the threads, the boxed numbers and `Arrays` (`get`, `add`, `equals`, `toString`, `substring`, `orElse`, `println`, `parseInt`...). The list is `JAVA.common`; the family's is `JVM.common`, both lists (Kotlin's below).
- **Quirks**: a call to an abstract method its implementations override goes to it (T-0081): `input.pushLimit(n)` to `CodedInputStream.pushLimit`, which `CodedInputStream.ArrayDecoder.pushLimit` and `StreamDecoder.pushLimit` override (protobuf: 3802 calls more, 420 `pushLimit`). A class named like another of the host, in any file, is ambiguous: generated code repeats its classes (`Builder`, `TestMessage`) in every file.
- **Limits**:
  - `shortcut:` an anonymous class (`new Runnable() { public void run() {..} }`) is not a class: its methods are the enclosing class's (`A.run`), 325 such methods on protobuf; to make the anonymous body a `@class` if a host needs it.
  - `shortcut:` no imports nor types: `C.m()` goes to the host's class `C`, so a library's class named like one of ours is taken for it, and a variable named like a class (`Foo Foo`) too; a static method `C` inherits is linked by `m` alone; to read the imports if a host's `callers` suffer.
- **Sample host**: protobuf (docs/sample-hosts.md).

## C and C++

- **Section**: `c`, one family: a C++ call to a C function is linked. **Suffixes**: `.c` (the C grammar); `.h`, `.cpp`, `.cc`, `.cxx`, `.hpp` (the C++ grammar, which reads C headers too).
- **Grammars**: `tree-sitter-c` 0.24.2 and `tree-sitter-cpp` 0.23.4 (py-tree-sitter 0.26.1). Their `tags.scm` capture no call: the queries (`C_QUERY`, `CPP_QUERY`) are ours.
- **Nodes**: a `function` per function definition with a body, its name in any declarator (`char** f()`, `T& f()`); a `method` `C.m` per function defined in a class's body, and per `C::m`, `ns::C::m`, `C<T>::m` defined outside it (the innermost scope is the class), constructors (`C.C`), destructors (`C.~C`) and operators (`C.operator==`) included; a `class` per `class`, `struct`, `union` and `enum` with a body, and per `typedef struct { .. } T`; a class defined in a class's body is `Outer.Inner`, its inline methods `Outer.Inner.m` (T-0043; protobuf: 362 nested classes, 66 more, `Impl_` 51 of them; its `AddOffset` of two nested classes became ambiguous, 4 sites). A namespace is no class: `namespace ns { class X }` is `X`. A prototype (`int f(int);`, a method declared in its class), a forward declaration (`class C;`) and `= default` are not nodes: each would make a name ambiguous between the `.h` and the file that defines it.
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
  - `shortcut:` a method defined outside its nested class, `void Outer::Inner::m() {}`, is `Inner.m` (its innermost scope), where one defined in the class's body is `Outer.Inner.m`: 108 on protobuf (103 in `.cc`, `ConformanceRequestSetting.GetTestName`), contained by their file; and a C struct in a struct is `A.B` though C gives its tag the file's scope (none in protobuf's `.c`); to name the scope's whole path if a host's `explain` needs them together.
  - `shortcut:` a constant (`INT_MAX`) or a class (`struct MY_POINT {`) named like a macro is erased too, and a macro with arguments (`PROTOBUF_ALIGNAS(8)`) is not; a class whose declaration an `#ifdef` cuts (`class PROTOBUF_EXPORT` / `#ifdef` / `ABSL_ATTRIBUTE_WARN_UNUSED` / `#endif` / `Arena final {`, protobuf's `Arena`) is lost (BACKLOG.md); to tell them apart if a host loses code to one.
  - `shortcut:` the classes and functions of one name are one node per file only: an amalgamation (`php-upb.c`, `ruby-upb.c`, which repeat upb) makes each name it repeats ambiguous, and no marker names it a generated file (its header is `/* Amalgamated source file */`, T-0079) (BACKLOG.md).
  - `shortcut:` no imports nor types: `C::m()` is linked by `m` alone, where Java's `C.m()` goes to `C.m` (T-0080); to capture its `@qualifier` if a host needs it.
- **Sample host**: protobuf (docs/sample-hosts.md).

## C#

- **Section**: `csharp`. **Suffixes**: `.cs`.
- **Grammar**: `tree-sitter-c-sharp` 0.24.0 (py-tree-sitter 0.26.1). Its `tags.scm` captures only the calls on a receiver (`reference.send`); its wheel stores its queries outside its package (`site-packages/tree_sitter_c-sharp/queries/`), which nothing reads: the query (`CSHARP_QUERY`) is ours.
- **Nodes**: a `class` per `class`, `interface`, `struct`, `enum` and `record`; a `method` `C.M` per method with a body (a block or `=> expr`), `C.C` per constructor, and `C.P` per property (`get`/`set`, `=> expr`, an auto-property `{ get; set; }` too); a method's class is the innermost class that contains it. A nested class is `Outer.Inner` (T-0043): each generated message's `Types` is `Person.Types`, its enum `Person.Types.PhoneType` (protobuf: 10 of the 18 files with a `Types` held several, 101 classes and 390 methods more). An abstract method or an interface's signature is not a node, where Java's is one (T-0081); nor an abstract or interface property, written as an auto-property but without a body (8 of protobuf's 4210 properties). The overloads of a class are one method. Namespaces are not nodes.
- **Links**: `F()` and `F<T>()` are `@call`; `x.M()`, `x?.M()`, `this.M()`, `C.M()` and `pb::C.M()` are `@send`, so a static method follows the common names. `new C()` and a base or interface (`class A : B, I`) and a record's primary-constructor base (`record R(int X) : B(X)`) are `references` to the type, in their generic (`C<T>`), qualified (`A.B.C`, `global::System.C`) and aliased (`pb::C`) forms, by the last name. A property read is no call: it has no caller, but as a delegate invoked (`codec.ValueWriter(..)`). All `INFERRED`.
- **Common names**: the BCL's names that one method of protobuf would collect from every `builder.Append` (a `StringBuilder`, linked to `BufferSegment.Append`), `enumerator.MoveNext`, `typeof(T).GetProperty` (measured from `graphe check` on protobuf, T-0035), and, guessed, the methods of `object`, the strings, the collections, LINQ, the streams and reflection (`ToString`, `Add`, `TryGetValue`, `Select`, `WriteLine`, `GetMethod`...), and NUnit's `Assert.False`, `True`, `Null`, `IsEmpty` (138 sends on protobuf that its properties `JsonToken.False`, `ByteString.IsEmpty`... would take once a property is a method, T-0041). The list is `CSHARP.common`.
- **Quirks**:
  - The preprocessor lines `#if`, `#elif`, `#else` and `#endif` are blanked before the parse (`Language.erased`): protobuf's generated code cuts its base list with one (`: pb::IMessage<T>` / `#if !GOOGLE_PROTOBUF_REFSTRUCT_COMPATIBILITY_MODE` / `, pb::IBufferMessage` / `#endif`), which the grammar does not parse: 44 of its 224 files skipped, 2 once the lines are erased. Both branches are read.
  - A file that does not parse is read all the same (`Language.tolerant`): the 2 left on protobuf (`Unsafe.AddByteOffset(ref a, i) = x;`, and `var e =` whose two erased branches then follow each other) lose no method to their class. On protobuf: skipped 44 / 0, classes 242 / 769, methods 2021 / 6422, as is / erased and tolerant; tolerant alone reads 1285 methods as functions, their class lost in the base list.
  - A property is the method `C.P` (T-0041): the calls of its `get`, `set` and `=> expr` are its own, so `callers ProtoPreconditions.CheckNotNull` lists the setters (`Person.Name:109`), 270 callers where it listed 138, 98 of them generated classes (`Person:56`). Those left on a class are an operator's or an indexer's.
  - A `partial void OnConstruction();` has no body: its 364 calls in generated code are `external`. `nameof(X)` is a call, `external` (102 on protobuf).
- **Limits**:
  - `shortcut:` an indexer, an event's accessors, a local function, an operator and a destructor are no definitions, their calls belong to the class (or the method); to capture them if a host's `explain` needs them.
  - `shortcut:` a property's name counts among the definitions of that name, so a method so named is ambiguous: `JsonToken.Name` (27 sites) and `SegmentedBufferHelper.IsAtEnd` (4) lose their link on protobuf; to keep properties out of a call's targets, the delegates' calls lost, if a host's methods suffer.
  - `shortcut:` both branches of an `#if` are read: their calls are counted twice, their definitions of one name are one; to keep one branch if a host's definitions differ between them.
  - `shortcut:` a C# file that does not parse is read, no longer named on stderr; to name it if a host's garbage shows.
  - `shortcut:` `C.M()` is linked by `M` alone, where Java's goes to `C.M` (T-0080); to link `C.M()` to `C.M` if a host needs it (BACKLOG.md).
  - `shortcut:` a `partial class` is one class per file it spans: `Any` (`Any.pb.cs`, `AnyPartial.cs`) is two classes, so a reference to it is ambiguous (125 class names in several of protobuf's `.cs` files, partials and the copied tests); to merge a partial class's files if a host's references to it matter.
- **Sample host**: protobuf (docs/sample-hosts.md).

## Ruby

- **Section**: `ruby`. **Suffixes**: `.rb`.
- **Grammar**: `tree-sitter-ruby` 0.23.1 (py-tree-sitter 0.26.1). Its `tags.scm` takes a bare identifier for a call (`#is-not? local`, which py-tree-sitter does not apply): a local variable would be a call. The query (`RUBY_QUERY`) is ours.
- **Nodes**: a `class` per `class` and `module` (a module holds its `def self.m`, and names a namespace), and per `X.class_eval do` block, which reopens `X` (protobuf's `well_known_types.rb`: `Any.pack`, `Timestamp.to_time`); a `method` `C.m` per `def m` and `def self.m` in it, the two one method if both exist; a `function` per `def` outside any. A method's class is the innermost one: `module Google::Protobuf` `def self.encode` is `Protobuf.encode`. A class in a module is `Module.Class` (T-0043): `module Google` `module Protobuf` `class Descriptor` is `Google.Protobuf.Descriptor`, its methods `Google.Protobuf.Descriptor.m` (`explain Descriptor.m` still designates them); a scoped module by its last name, so `module Google::Protobuf` `class Descriptor` is `Protobuf.Descriptor` (protobuf: 94 nested classes, 1 split, `StressTest`). A `class << self` is no class, its methods its enclosing class's. Operators and setters are methods too (`C.==`, `C.x=`); `def obj.m` on another object than `self` is a method of the class around it, or a function `m`.
- **Links**: `b()` and `c arg` (a `call` without receiver) are `@call`; `x.c`, `self.c`, `x&.c` and `A::B.c` are `@send`. `C.new` and a superclass (`class A < B`) are `references` to the class, bare or scoped (`Google::Protobuf::B`), by the last name; `C.new` is a send `new` too, a common name. All `INFERRED`.
- **Common names**: `new` (892 sends `C.new`, 9 `def self.new` in protobuf's ffi), `each` (38) and `pack` (6 of its 9 sends are `Array#pack`, linked to `Any.pack`), measured on protobuf (T-0036), and, guessed, the methods of `Object`, the conversions, `Enumerable`, `Array`, `Hash`, `String` and `IO` (`to_s`, `inspect`, `dup`, `map`, `empty?`, `join`, `puts`...). A name whose sends on protobuf are mostly its own is left out: `push`, `pop`, `first`, `delete`, `keys` (its `RepeatedField` and `Map` mirror `Array` and `Hash`), `eql?` (its messages'). The list is `RUBY.common`.
- **Quirks**:
  - Every protobuf `.rb` parses: neither `tolerant` nor `erased`.
  - A message's fields are read through `method_missing` (`m.repeated_string`, 171 sends): `external`, no definition.
- **Limits**:
  - `shortcut:` a bare `b` is no call: it may be a local variable, which only the grammar's `locals.scm` tells; at least 17 bare calls to protobuf's methods are missed (`inspect`, `reset_allocations`); to tell a variable from a call if a host's `explain` misses them.
  - `shortcut:` an `attr_reader`, `attr_accessor`, `alias`, `define_method` is no definition, its readers' sends `external` (4 `attr_*` on protobuf); to capture them if a host's `explain` needs them.
  - `shortcut:` a module counts as an outer class (T-0043, the rule written once; a namespace in C++, C# or Rust does not, being no `@class`), and a scoped module is named by its last name: one class is `Protobuf.X` under `module Google::Protobuf` and `Google.Protobuf.X` under `module Google` `module Protobuf` (protobuf's `.rb` use the nested form only, `Google.Protobuf.X`); `explain X.m` designates both; to name a module by its whole path if a host's `explain` needs them together.
  - `shortcut:` a class reopened in several files is one class per file (12 names on protobuf: `Descriptor`, `RepeatedField`, `Google`, `Protobuf`), so a reference to it is ambiguous; to merge them if a host's references matter.
  - `shortcut:` the methods of a class built by `Class.new(..) do` belong to the enclosing class: the 41 methods of the message class `ffi/message.rb` builds are `Descriptor`'s (`Descriptor.encode`); to name such a class after what it is assigned to, code of its own: a dedicated reader (BACKLOG.md).
  - `shortcut:` a setter call `x.y = v` (339 on protobuf) is a send `y`, not `y=`: a hand-written `def y=` gets no caller, a getter `y` its callers (protobuf has none, its fields go through `method_missing`); to name the send `y=` if a host's setters need callers.
  - `shortcut:` `C.m` is linked by `m` alone, where Java's `C.m()` goes to `C.m` (T-0080); `include M` and `extend M` are calls, not references to `M`; to link `C.m` to `C`'s `m`, and `include M` to `M`, if a host needs them.
- **Sample host**: protobuf (docs/sample-hosts.md).

## Swift

- **Section**: `swift`. **Suffixes**: `.swift`.
- **Grammar**: `tree-sitter-swift` 0.7.4 (py-tree-sitter 0.26.1). Its `tags.scm` captures no call. The query (`SWIFT_QUERY`) is ours.
- **Nodes**: a `class` per `class`, `struct`, `enum`, `actor` (one `class_declaration` in the grammar) and `protocol`. An `extension T` is no class: its methods are `T`'s by `@receiver`, as Go's, so that a type extended in several files stays one class and its references are linked (`extension Foo.Bar` and `extension Array<T>` extend `Bar` and `Array`). A type is named by its last name, generic or not; a type in a type is `Outer.Inner`, its methods `Outer.Inner.m` (T-0043; libsignal: 41 nested types, its test `Error`s of one file apart). A `method` `C.m` per `func`, `init` (`C.init`) and computed property (`var p: T { .. }`, `C.p`) directly in a type's or an extension's body; a `function` per `func` at the top of a file. A protocol's `func` requirement is an `abstract` node `P.f` (T-0081), which a method of a type or extension that names `P` in its base list overrides (`struct C: P`, `extension C: P`): `nativeHandle.const()` goes to `SignalMutPointer.const` (libsignal: 1161 calls more, 475 `const`). An `init` and a property requirement are none (`init` is a common name, a property often stored).
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
  - `shortcut:` a protocol's `init` and property requirements are no declarations (`init` a common name, a property often stored), so a call through one is linked as before; to capture them if a host's calls through a protocol's property stay ambiguous (T-0081).
  - `shortcut:` an `extension Outer.Inner`'s methods are `Inner.m` (its last name), where the type's own are `Outer.Inner.m`, and a type nested in an `extension Outer` is `Inner` (none on libsignal); to take the extension's whole path if a host's `explain` needs them together.
- **Sample host**: libsignal (docs/sample-hosts.md).

## Kotlin

- **Section**: `java`, one family with Java (T-0042, above). **Suffixes**: `.kt` (a Gradle script `.kts` is not read).
- **Grammar**: `tree-sitter-kotlin` 1.1.0 (py-tree-sitter 0.26.1). It ships no `tags.scm`: the query (`KOTLIN_QUERY`) is ours.
- **Nodes**: a `class` per `class`, `interface`, `enum class`, `data class` (one `class_declaration` in the grammar) and `object`; a companion object is none, its functions its class's (`C.s`). A `method` `C.m` per `fun` with a body directly in a type's body (an `object`'s, a companion's, an enum's); a `function` per `fun` at the top of a file. A secondary constructor is the method `C.constructor`. An extension function `fun Foo.Bar.f()` is the method `Bar.f` by `@receiver`, as Go's, wherever it is declared (libsignal's 73: its `toFfiArgType` of each type apart); one on a function type (`fun (() -> Unit).f()`) is not captured. An abstract function (no body), an anonymous object's (`object : Runnable { override fun run() }`) and a local one are not captured: their calls are their enclosing definition's. A type is named by its last name, generic or not; a class in a class is `Outer.Inner` (T-0043), so a sealed class's `Success` of each result is apart (libsignal: 213 nested, 72 classes more, `Success` 34; 13 `references` to them became ambiguous, `UnexpectedError` 5).
- **Links**: `b()` is a `@call`; `x.c()`, `this.c()`, `y?.c()`, `C.s()` are `@send`. A call to a capitalised name, `C(..)`, `Foo.Bar(..)`, `Array<Int>(..) { }`, is a `references` to the type by its last name (Kotlin's naming convention, and Kotlin has no `new`), as is a supertype (`class C : B(), P`, `object O : P by d`, `object : Runnable`). `C.s()` on a class of the host goes to `C.s`, a companion's function too (T-0080, Java's rule; libsignal: 107 calls more). All `INFERRED`. A call to libsignal's Java from its Kotlin is linked by name (T-0042: 401 sites `external` before, `nativeHandle` 71, `makeCancelable` 69, `guardedMap` 48), and the reverse (65, `checkCalledMethod` 16). A name both define is ambiguous: `filterExceptions` (`FilterExceptions.java` and `FilterExceptionsKt.kt`, 246 sites), `fakeConnect` (three Java classes, 58).
- **Common names**: `get` (78 sends, `CompletableFuture.get`, linked to `TestingIntBox.get`), `toString` (32), `map` (31, mostly a collection's, linked to `RequestResult.map`) and `hashCode`, measured on libsignal (T-0038), and, guessed, `Any`'s, the scope functions (`let`, `apply`, `also`, `run`, `use`), the collections', the arrays' and `Result`'s (`getOrNull`, `onSuccess`). Left out, their sends mostly libsignal's: `await` (its own `CompletableFuture.await`), `start`, `of`, `remove` and `invoke` (one send each, libsignal's `svrB.remove()` and `SetProfileHelpers.invoke`); `start`, `of` and `remove` apply all the same, Java's (below). Out since Java is read with Kotlin (T-0042): `thenApply`, `thenCompose`, `complete`, `completeExceptionally`, the methods of libsignal's own Java `CompletableFuture` (56 of its Java sends were linked to them, 41 Kotlin ones are), and `toByteArray`, protobuf's (306 Java sends). The list is `KOTLIN.common`; Java's applies too (`JVM.common`).
- **Quirks**:
  - Not `tolerant`: every libsignal file parses. 5 of protobuf's 23 do not (a trailing comma in type parameters, `T : Any,` then `>`; a soft keyword used as a name, `by = "foo"`, in its "evil names" tests): skipped and named on stderr (BACKLOG.md).
- **Limits**:
  - `shortcut:` Java's `start`, `of` and `remove` silence 16 of libsignal's Kotlin sends to its own (`BackupJsonExporter.start`, `BadgeVisibility.of`); out of the list, Java's `List.of` would be linked to `BadgeVisibility.of` (35 sends) and 501 of protobuf's Java sends become ambiguous; to give each grammar its own list if a host's Kotlin loses more.
  - `shortcut:` a capitalised call to a standard type, `ByteArray(32)`, is a `references` to a Java class of the host so named (libsignal's `zkgroup.internal.ByteArray`: 24 links, BACKLOG.md), and a Java send to a library is linked to a Kotlin definition so named (protobuf's generated `Any.unpack(X.class)` to its Kotlin `inline` extension `ProtoAny.unpack`: 3 links, 8 sites); Kotlin's `"s".toByteArray()` would be linked to a host's single Java `toByteArray`. To never reference Kotlin's standard types if a host's `callers` of a class suffer.
  - `shortcut:` a property's getter or setter (32 on libsignal) and an `init { }` block are no definitions, their calls their class's; to capture them as Swift's computed properties if a host's `explain` needs them.
  - `shortcut:` an abstract function or an interface's is no declaration, where Java's is (T-0081); a Kotlin class's supertypes are its base list (not an anonymous object's), so its method overrides a Java declaration; to capture Kotlin's if a host's Kotlin calls through an interface stay ambiguous.
  - `shortcut:` a capitalised call is taken for a type, a lower-case one for a function; to tell them apart by their definitions if a host breaks the convention.
  - `shortcut:` an extension function on a nested class, `fun Outer.Inner.f()`, is `Inner.f` (the receiver's last name), where the class's own methods are `Outer.Inner.m`: 29 on libsignal (`Captcha.toFfiArgType`); to take the receiver's whole path if a host's `explain` needs them together.
  - `shortcut:` the grammar does not read a class body on one line (`class C { fun f() {} }`, an error node: the tests' snippets are on several lines; none on libsignal), and reads `Array<Int>(1)` without a trailing lambda, or after a `+`, as comparisons (no reference); to take a newer grammar when one is published, if a host loses code to them.
- **Sample host**: libsignal (docs/sample-hosts.md).

## PHP

- **Section**: `php`, in place of the dedicated reader by patterns (`graphe_php.py`), compared with it in T-0044 and replaced in T-0045. **Suffixes**: `.php`.
- **Grammar**: `tree-sitter-php` 0.25.2 (py-tree-sitter 0.26.1), its grammar with the HTML (`language_php`): a page's text outside `<?php ?>` holds no call (`<p>aide(x)</p>`). The query (`PHP_QUERY`) is ours.
- **Nodes**: a `class` per `class`, `interface`, `trait` and `enum`; a namespace is none. A `method` `C.m` per method with a body (`C.__construct` the constructor); an interface's or abstract method is none, where Java's is one (T-0081). A `function` per `function f()`, indented or not (the PHP reader read `^function` only). An `action` per `case 'x':` outside any function or method: an entry point's `switch ($action)` (Grid Zero's `web/api/scenarios.php`, 8 actions). A `case` in a function, or in a switch nested in an action, is none, its calls that definition's: protobuf's 9 (`Message.__debugInfo`, conformance's `doTest`) would have taken 7 calls from their methods.
- **Links**: `f()` and `\A\f()` are `@call`; `$x->m()`, `$x?->m()`, `X::m()`, `self::m()`, `parent::m()` are `@send`. `apart`: a call is linked to a function only, a send to a method only (protobuf: 219 bare calls to built-ins, `count()` 185, went to its methods of that name; T-0044). `new C`, `extends`, `implements`, a trait's `use` and a caught type (`catch (A | B $e)`, 4cast's `ErreurAmont`) are `references` by the last name. A call outside any definition is its file's (a router at a page's top, 4cast's `api/index.php`, T-0023). An action owns its body's calls; one without a body (`case 'signaler':` then `case 'noter':`) `dispatches` to the next, `EXTRACTED`. The others are `INFERRED`, where the PHP reader said `EXTRACTED` for the same links by name. A host's extension finds an action by its kind and name (Grid Zero's GDScript `{"action": "x"}` `sends` to it, T-0009).
- **Common names**: none (`PHP.common` is empty): every send linked by a standard name on protobuf is to one of its own methods (`$any->pack`, `getFile`), PHP's library being functions (T-0044).
- **Quirks**:
  - Not `tolerant`: protobuf's `php/tests/generated_previous/Previous/readonly.php` (`class readonly`, a keyword since PHP 8.1) does not parse, skipped and named on stderr; the PHP reader read it (no function in it).
  - The ids carry the extension, as every generic language's: 4cast's `api_lib_cache_par_cache` is `api_lib_cache_php_par_cache`, Grid Zero's actions `web_api_scenarios_php_action_liste`. Grid Zero's graph is otherwise the PHP reader's, its call links on the call's line where they were on the body's first (T-0045).
- **Limits**:
  - `shortcut:` PHP's function and method names are case-insensitive, the links by the exact name; to fold the case if a host calls `Foo()` for `foo()`.
  - `shortcut:` a call through a variable (`$f()`, `$x->$m()`) is none, and an anonymous class at a file's top is no class, its methods functions; to capture them if a host's `explain` needs them.
  - `shortcut:` a caught type (`catch (ErreurAmont $e)`) is no reference, as Java's: 4cast's 3; to capture it if a host's `explain` of an exception needs them.
  - `shortcut:` an action is a `case` of a single-quoted word, as the PHP reader's: `case "x":`, a constant and `default:` are none; to take them if a host's router uses them. Beyond the PHP reader, which read `case 'x':` alone on its line: one on a line with its body, an `endswitch` form's and one in a closure at a file's top are actions too.
  - `shortcut:` the actions of one name in one file are one node, on the first one's line, owning both bodies' calls; to tell them apart if a host's file has two routers.
- **Sample hosts**: protobuf (docs/sample-hosts.md); 4cast and Grid Zero, the user's (T-0044, T-0045).

## The dedicated readers

Each is specified in its module's docstring.

- **Python**, `graphe/python.py`: the `ast`, a call resolved by its receiver's type (annotations, constructions, returns), by the name alone otherwise; a cache of each file's definitions (T-0026). A module is imported by its import name, its path without its leading folders that are no package (no `__init__.py`): `src/graphe/core.py` is `graphe.core`, `tests/admin_views/models.py` `admin_views.models`, a folder without `__init__.py` inside a package kept (`gis_tests/data/invalid/`); a file node keeps its path's name. `import a.b.c` binds `a` and imports `a.b` and `a.b.c` too; `a.b.f()`, and `from a import b`, go to the submodule `b`, unless the package binds `b` otherwise (a def, a class, a variable, an import of something else: `from .x import g as b`), its own import of it (`from . import b`, `import a.b`) winning over a fallback beside it (`except ImportError: b = None`) (T-0096).
  - `shortcut:` `import a.b as c` links `a.b`, not `a`; to give the import links their own list if a host's `imports` suffer.
  - `shortcut:` the package's statements are not read in order: its own import of `b` wins over any other binding of `b`, a later `b = b.f` too; to follow the order if a host rebinds a submodule's name so.
  - `shortcut:` a name two modules bear resolves to neither (none in Django); a leading namespace package (PEP 420, a folder without `__init__.py` imported through) is left out, so an import through it resolves to nothing (Django: 1 import, `tests.sphinx_tests...`); to resolve a shared name by the importer's nearest, and to keep such folders, when a host's `callers` suffer.
- **GDScript**, `graphe/godot.py`: by patterns, a `preload` constant designates its script, a variable typed by it or made by `X.new()` sends its calls there; `check` recounts the calls.
- **JavaScript, TypeScript, Svelte, Vue**, `graphe/js.py`: tree-sitter, ES imports and re-exports followed, `new C()` and `f()` assigned typed, by the name otherwise; a Svelte component's script and markup (T-0014, T-0015, T-0022); `.jsx` by the JavaScript grammar, `.tsx` by the TSX one, a JSX `<Component/>` no call (T-0076); a Vue component's `<script>` in the grammar its `lang` names, its template's `{{ }}` and directives (`@click`, `:prop`, `v-if`, `v-for`) read for their calls, the component's, an expression the grammar cannot parse left out (T-0082).
