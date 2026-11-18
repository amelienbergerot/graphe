Status: ready-for-agent
Type: spec
Created: 2026-11-19

# A generic reader for the most used languages

## Problem Statement

The graph reads Python, GDScript, PHP and JavaScript/TypeScript/Svelte only. An agent working in a Java, C#, Go, Rust, Ruby, C, C++, Swift or Kotlin host has grep and file reading, nothing else: no "what does this function call", no `callers --depth`, no `path`, no ticket that cites the code. The tool is meant to serve other people's repositories some day (BACKLOG.md, "Only its author can install the tool"), and most of those repositories are in a language it cannot read. Nor does anything show, to someone who discovers the tool, on which real code it has been tried and with what result.

## Solution

One **generic reader** (GLOSSARY.md) reads nine languages the same way (ADR 0003): Java, C#, Go, Rust, Ruby, C and C++ (one family), Swift and Kotlin. It draws a node per file, function, method and class, and links a call by its name alone, only when that name has a single definition in the same language; the other calls are counted as not attributed, so that `explain` tells the agent to grep them. A host in one of these languages gets a graph with no configuration, like the hosts of the existing readers. Adding a language later is data only: its grammars, its queries, the method names never linked by name.

Each language is proven on a pinned public **sample host**, preferably one that mixes languages (protobuf, libsignal, gitea, plus Django already measured). Each language's treatment is specified in a readers document, the sample hosts in their own document, and the README sums the measures up in a "Tested on" table.

## User Stories

1. As an agent in a Java host, I want `graphe explain Class.method` to list what it calls and what calls it, so that I locate code without grep.
2. As an agent in a C#, Go, Rust, Ruby, C, C++, Swift or Kotlin host, I want the same queries as in a Python host, so that one skill serves every host.
3. As an agent, I want a method to be designated `Class.method`, so that I type what the answers print.
4. As an agent in a Go host, I want `func (r *T) M()` to be the method `T.M`, though it is declared outside its type, so that Go reads like the others.
5. As an agent in a Rust host, I want a function of an `impl T` block to be the method `T.f`, so that its callers are found under its type.
6. As an agent, I want `graphe callers X --depth N` in these languages, so that I measure the reach of a change.
7. As an agent, I want `graphe path A B` in these languages, so that I see how an action leads to an effect.
8. As an agent, I want `explain` to list the tickets and documents that cite a Java or Go function, so that I find why the code exists.
9. As an agent, I want a call whose name has a single definition in the language to be linked, so that its caller and callee are one query away.
10. As an agent, I want a call whose name has several definitions not to be linked to any of them, so that `callers` never lists a false caller.
11. As an agent, I want `explain` to say "+ N calls named `f` the graph could not attribute: grep them", so that I know when the graph's answer is incomplete.
12. As an agent, I want a link made by the name alone to be marked as such (`[by name]`, `?`), so that I weigh it against a sure link.
13. As an agent, I want a call on a receiver (`x.save()`) to be linked by name too, marked `?`, so that Java and C# methods have callers at all.
14. As an agent, I want the language's most common method names (`get`, `add`, `push`, `len`...) never to be linked by name, so that a host's single `push` does not collect every `vec.push()`.
15. As an agent in a mixed host, I want a Rust call never to be linked to a Java function of the same name, so that two languages do not merge by accident.
16. As an agent in a C++ host, I want a C++ call to a C function to be linked, so that the C/C++ family reads as one language.
17. As an agent, I want a `.h` header to be read whether the host is C or C++, so that its declarations are not lost.
18. As an agent, I want `new C()` and `extends C` to be `references` to the class, so that I find who builds or derives a class.
19. As an agent, I want a call in a function to belong to that function, not to its file, so that `explain` on the function shows it.
20. As an agent, I want the nodes of a `Foo.java` and of a `Foo.kt` never to share an id, so that two files of the same name do not merge.
21. As an agent, I want a file that does not parse to be skipped and named, the build going on, so that one broken file does not cost the whole graph.
22. As an agent, I want the graph of a Python or JS host to stay exactly the same, so that the generic reader breaks nothing already read.
23. As an agent, I want `graphe check` to give the coverage of each language apart (linked, by name, not attributed, external), so that I see which language falls short.
24. As a maintainer, I want each language's coverage under its own name in `check`, so that a regression points at one language.
25. As a maintainer, I want a language to be data only (grammars, queries, common names), so that adding the tenth language touches neither the core nor the linking.
26. As a maintainer, I want one capture convention for all languages' queries, so that the linking code is written and fixed once.
27. As a maintainer, I want the queries to be ours, written from the grammars' `tags.scm` and kept in this repository, so that a grammar's upgrade does not change the graph silently.
28. As a maintainer, I want each language's queries tested on a snippet, so that a broken query fails a test and not a host.
29. As a maintainer, I want a quirk the queries cannot express to be a `shortcut:` in the readers document, so that the limits of each language are known.
30. As a maintainer, I want a language that needs code of its own to be the proof that it needs a dedicated reader (ADR 0003), so that the generic reader stays data-driven.
31. As a maintainer, I want the grammars pinned in the main dependencies, so that a host's graph does not depend on what the user chose to install.
32. As a maintainer, I want each language to have a section in the readers document (suffixes, grammar and version, what becomes a node, what becomes a link and with which confidence, quirks, limits, sample host), so that its treatment is specified in one place.
33. As a maintainer, I want the existing dedicated readers to have a short section in the readers document pointing to their module's docstring, so that the document lists every reader.
34. As a maintainer, I want the skill and the README to point to the readers document for the list of readers, so that the list is kept in one place.
35. As a maintainer, I want each sample host pinned to a commit, with its clone command, its languages, its `graphe.toml` exclusions and the tickets that measured it, so that any measure can be replayed.
36. As a maintainer, I want sample hosts that mix languages, so that one clone tests several languages and the "same language" rule is put to the test.
37. As a maintainer, I want a language to be done only when its sample host builds, with no dangling link, its `check` coverage noted and three queries compared with grep, so that "supported" means measured.
38. As a maintainer, I want what the generic reader misses on a sample host to go in BACKLOG.md naming that host, so that a dedicated reader is decided on proof.
39. As a maintainer, I want the build time of the largest sample host (protobuf) measured, so that a cache like T-0026's is added only if needed.
40. As someone discovering the tool, I want a "Tested on" table in the README (host, languages, files, build time, one query compared with grep), so that I see on what real code it works and how well.
41. As someone discovering the tool, I want the README's table to hold measures only, so that it claims nothing untested.
42. As a future packager, I want no reader to hold anything specific to the author's machine, so that publishing the tool later needs no reader change.

## Implementation Decisions

- **A new module, the generic reader.** It holds the reading, the attachment of a call to its owner, the `Class.method` naming and the linking, written once. The languages are records of data behind an internal seam: a `Language` with its grammars by file suffix, its queries, and its common method names never linked by name. No language has code of its own (ADR 0003).
- **One entry per language in the readers' registry**, under the name of its `graphe.toml` section (`java`, `csharp`, `go`, `rust`, `ruby`, `c`, `swift`, `kotlin`), each a `contribute(project)` built from its `Language`. The C/C++ family is the single entry `c`. The "same language" rule is then structural: a contribution only sees its own language's definitions. The external seam, `contribute(project)` and its contribution (docs/contribution.md), does not change.
- **Grammars by suffix.** `.c` reads with the C grammar; `.h`, `.cpp`, `.cc`, `.cxx` and `.hpp` with the C++ one. The other languages take their usual suffixes, spelled out in the readers document.
- **One capture convention** for all queries: `@function`, `@method` and `@class` (class, interface, struct, Rust's `impl`), each with its `@name`; `@call` for a bare call `f()`, `@send` for a call on a receiver `x.m()`; `@reference` for `new C()` and `extends C`; `@receiver` (Go) gives a method's type when it is declared outside it. The owner of a call is the innermost definition that contains it; a method's class is its `@receiver`, or else the innermost `@class` that contains it.
- **The queries are strings in the generic reader's module**, one per language, written from the `tags.scm` each grammar ships. Measured as shipped (py-tree-sitter 0.26.1, 2026-11-18): C, C++ and Swift capture no call, C# no bare call, Ruby takes a variable for a call, C#'s wheel stores its queries outside its package. They move to `.scm` files when packaging needs package data.
- **Nodes:** a node per file (the container), function, method (`Class.method`) and class/interface/struct. Modules and namespaces are not nodes. Ids carry the file's extension, as the JS reader's do, so that `Foo.java` and `Foo.kt` never collide.
- **Links:** `@call` and `@send` become `calls`, `@reference` becomes `references`. A link is made by the name alone (`INFERRED`) only when the name has a single definition in the language; a `@send` link is marked `?`; a name in the language's common list is never linked from a `@send`. Every call is a coverage site with its verdict (linked, by name, not attributed, external), so that `check` and `explain`'s "not attributed" count work as for the existing readers (T-0025).
- **A file that does not parse** is skipped, named on stderr, and the build goes on (T-0016).
- **Dependencies:** the nine grammars (`tree-sitter-java`, `-c-sharp`, `-go`, `-rust`, `-ruby`, `-c`, `-cpp`, `-swift`, `-kotlin`) are pinned in the main dependencies, as the JS and TS grammars are.
- **No cache at first.** The build of protobuf is measured; a per-file cache reusing T-0026's mechanism comes through BACKLOG.md if needed.
- **The existing readers do not change.** PHP's comparison with the generic reader is a BACKLOG.md entry.
- **Documents:** a readers document, one section per language (suffixes, grammar and pinned version, nodes, links and confidence, quirks, `shortcut:` limits, sample host), and a short section per dedicated reader pointing to its docstring; a sample hosts document, one entry per host (URL, pinned commit, shallow clone command, languages, `graphe.toml` exclusions, tickets that measured it), Django included; the README's "Tested on" table, filled by each language's ticket with measures only; the skill and the README point to the readers document for the list of readers.
- **Sample hosts:** `protocolbuffers/protobuf` (C, C++, Java, C#, Rust, Ruby; Python and PHP as a cross-check), `signalapp/libsignal` (Rust, Swift, Java, Kotlin; TypeScript), `go-gitea/gitea` (Go; TypeScript), and Django (Python, already measured in T-0016 and T-0026). The commits are pinned when the sample hosts document is created, in the first ticket that measures one.
- **Done, for a language:** its sample host builds, with no dangling link; its `check` coverage is noted; three `explain` or `callers` queries are compared with grep in its ticket; its README row and readers section are written; what it misses is in BACKLOG.md, naming the host.

## Testing Decisions

- A good test drives a seam with real source text and asserts on what an agent would see: the nodes, their names and the links (source, target, relation, confidence) and the sites' verdicts. Never on the internals of the matching or of the query captures' order.
- **Two seams, both approved:**
  - **The internal seam `read(language, file, source)`**, which returns a file's tags (definitions with their `Class.method` name and line, calls with their owner): one snippet test per language, which proves its queries and the capture convention (Go's `@receiver` and Rust's `impl` first).
  - **The external seam `contribute(project)`**, with a fake project (a root and `files(suffix)`) over files written in a temporary folder: the linking rules once, over two or three languages: the unique name, the ambiguous name not attributed, `?` on a receiver call, the common names, no link across languages, the C/C++ family, a file that does not parse.
- **Prior art:** the JS reader's tests write files into `tmp_path`, build the reader over them and assert on its links and names (`_js` and the tests after it in the main test file); `test_host.py` builds a host in a temporary folder.
- **Non-regression:** the nodes and links the existing readers draw in the existing hosts (Grid Zero's reference test, dpe, 4cast, the tool itself) do not change. A host that carries files in one of the nine languages (an Android folder, a C extension) gains their nodes: check each host, and note in its ticket whether it is a gain or a host to `exclude`.
- The sample hosts are measures, not automated tests: they are too large, and they are cloned outside the repository.

## Out of Scope

- **Packaging and publication** (a package, any OS, ADR 0001 revisited): a separate effort, after the readers (BACKLOG.md).
- **Frameworks** (a Django URL to its view, JSX components, Spring injection, Rails routes) and **bridges between languages** (JNI, FFI, generated code): their own session (BACKLOG.md).
- **Dedicated readers** for the nine languages: only on proof from BACKLOG.md (ADR 0003).
- **Changing the existing readers**, PHP's pattern reader included (BACKLOG.md).
- **Imports, receiver types, scopes** in the generic reader: a language that needs them needs a dedicated reader.
- **A cache** for the generic reader, until protobuf's build time asks for one.
- Objective-C, Scala, Dart, Lua, Elixir and the other languages: later, as data, when a host asks.

## Further Notes

- Decided in a grilling session (2026-11-18 and 19): GLOSSARY.md (generic reader, dedicated reader), ADR 0003, and the BACKLOG.md entries "A host in another language gets no graph", "PHP's pattern reader may be worse than the generic one", "Only its author can install the tool", "The links a framework creates are outside the graph".
- The first slice should prove the capture convention on Go, Rust and Java (the `@receiver`, the `impl`, a plain class) before the other languages come in.
- Not checked: whether the nine grammars have Linux and macOS wheels (it matters to packaging), the share of generated code in protobuf, and whether libsignal and gitea clone cleanly on Windows (long paths, symbolic links).
