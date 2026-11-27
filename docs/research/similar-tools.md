# Tools similar to graphe, and what graphe could take from them

Research note, 2026-11-27.

The question: which existing tools are close to graphe, and which of their features would close a gap in `BACKLOG.md` ("Open") or add something graphe lacks? graphify was compared earlier and is left out.

Method: every claim below comes from the project's own README, docs, source or spec, and the URL is given inline. Repository status (archived flag, last push, licence, stars) comes from the GitHub REST API (`https://api.github.com/repos/<owner>/<repo>`), read on 2026-11-27. Where a primary source did not answer a cell of the grid, the cell says **not verified**.

Each tool is described on the same grid:

- **Reads**: the languages and inputs.
- **Resolves**: how a call or reference is linked to its definition.
- **Offered as**: how an agent or a person uses it.
- **Freshness**: how it stays up to date.
- **Unknowns**: how it reports what it does not know.
- **Status**: maintained or archived, and the licence.

---

## Agent-facing tools

### Serena (oraios)

- **Reads:** "over 40 programming languages" through language servers, among them Go, Rust, Java, Kotlin, C#, C/C++, Ruby, Swift, PHP, Python, TypeScript, Svelte, Vue and GDScript. A paid JetBrains plugin backend covers what JetBrains IDEs cover ([README](https://github.com/oraios/serena)).
- **Resolves:** by the language server (LSP), so with the compiler's or analyser's own types: "Language servers implementing the language server protocol (LSP) — the free/open-source alternative which is used by default" ([README](https://github.com/oraios/serena)). Some features depend on the server. "find implementations" is "Only available for some languages, limited by the language server functionality", and "type hierarchy" exists only in the JetBrains backend ([README](https://github.com/oraios/serena)).
- **Offered as:** an MCP server. Its tools include `find_symbol`, `find_referencing_symbols`, `get_symbols_overview`, `find_declaration` and `replace_symbol_body`. Serena v2 adds a single `serena_repl` tool that runs Python against facades (`s.lsp.find_symbol(...)`), so several operations compose in one call and "Only the result the agent actually needs enters the conversation" ([tools](https://oraios.github.io/serena/01-about/035_tools.html)). It also edits code (rename, replace symbol body, safe delete) and keeps a memory system ([README](https://github.com/oraios/serena)).
- **Freshness:** `serena project index` pre-caches the language server's symbols. "Indexing has to be called only once." "During regular usage, Serena will automatically update the index whenever files change" ([workflow](https://oraios.github.io/serena/02-usage/040_workflow.html)). The change detection itself is **not verified**: the page does not describe it.
- **Unknowns:** **not verified**. No page read describes how a reference the language server cannot resolve is reported.
- **Status:** maintained. Last push 2026-11-24, latest release v2.1.0 (2026-10-19). Licence: SolidLSP under MIT, the rest under GPL-3.0-or-later, "Distributions combining both are as a whole subject to the GPL" ([README](https://github.com/oraios/serena)).

### Aider's repo map

- **Reads:** every file of the git repository that has a tree-sitter grammar and a tags query. `get_tags_raw` loads the file's language, parser and `.scm` query, and skips the file when there is none ([repomap.py](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py)). The docs call it "a concise map of your whole git repository" ([repo map docs](https://aider.chat/docs/repomap.html)).
- **Resolves:** by name only, and it links every candidate with a weight. A reference to identifier `x` adds an edge from the referencing file to every file that defines `x`. The weight is multiplied by 10 if the identifier was mentioned in the chat, by 10 if it is a long snake/camel/kebab name, by 0.1 if it starts with `_`, by 0.1 `if len(defines[ident]) > 5`, and by 50 if the referencer is a chat file. Reference counts are square-rooted. The ranking is `nx.pagerank(G, weight="weight", personalization=...)` ([repomap.py](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py)). The docs page names neither tree-sitter nor PageRank; it says "a graph ranking algorithm" on a graph "where each source file is a node and edges connect files which have dependencies" ([repo map docs](https://aider.chat/docs/repomap.html)). This is the opposite of ADR 0003, which refuses to link an ambiguous name: aider spreads the rank over all candidates and lowers it when a name has many definers.
- **Offered as:** text inside aider's prompt to the LLM, within a token budget (`--map-tokens`, "defaults to 1k tokens"). It shows the "most important classes and functions along with their types and call signatures" ([repo map docs](https://aider.chat/docs/repomap.html)). It has no query interface of its own.
- **Freshness:** a disk cache of tags per file (`.aider.tags.cache.v{N}`), reused while the file's mtime is unchanged ([repomap.py](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py)). The graph and the PageRank are recomputed.
- **Unknowns:** none reported. The map is a ranked selection by design, not a claim of completeness ([repo map docs](https://aider.chat/docs/repomap.html)).
- **Status:** not archived. Last push to `Aider-AI/aider` 2026-05-22, latest GitHub release v0.86.0 (2025-08-09). Apache-2.0 (GitHub API).

### Code-graph MCP servers

A search turned up many tree-sitter code-graph MCP servers. Most have few stars. The three below are clearly established by adoption (GitHub API, 2026-11-27): colbymchenry/codegraph (78,785 stars), DeusData/codebase-memory-mcp (49,215) and abhigyanpatwari/GitNexus (48,923). The smaller ones seen only in search snippets (sdsrss/code-graph-mcp, crowbett/codegraph and others) were not opened and are not described here. The counts below (benchmarks, coverage) are **self-reported** by each project.

#### CodeGraph (colbymchenry/codegraph)

- **Reads:** 20 languages parsed by a Rust kernel with tree-sitter (TypeScript, JavaScript, Java, Python, Go, C, C++, Rust, C#, Ruby, PHP, Swift, Kotlin, Scala, Dart, R, Lua, Luau), plus others on a portable engine, Vue, Svelte, Astro and Terraform among them ([README](https://github.com/colbymchenry/codegraph)).
- **Resolves:** "After extraction, references are resolved: function calls → definitions, imports → source files, class inheritance, and framework-specific patterns" ([README](https://github.com/colbymchenry/codegraph)). Whether a call is linked through the receiver's type or by name is **not verified**: the README does not say. It adds framework links. It emits `route` nodes "linked by `references` edges to their handler classes or functions" for more than 20 web frameworks (Flask, FastAPI, Express, Gin, Axum...), and `navigates` edges for routers (Next.js, React Router, Vue Router, SvelteKit, Angular). It also bridges languages: Swift to Objective-C, React Native and Expo modules ([README](https://github.com/colbymchenry/codegraph)).
- **Offered as:** an MCP server whose main tool is `codegraph_explore` ("one call → verbatim source + call flow + blast radius"). The CLI mirrors it: `explore`, `node`, `impact <symbol>` and `affected [files...]` ([README](https://github.com/colbymchenry/codegraph)). Usage guidance goes to the agent "automatically, in the MCP `initialize` response". The Claude Code config sets `"alwaysLoad": true`, because "Claude Code otherwise defers every MCP tool behind a tool-search step". An allow rule `mcp__codegraph__*` is still suggested "for auto-allow" ([README](https://github.com/colbymchenry/codegraph)).
- **Freshness:** an OS file watcher (FSEvents/inotify/ReadDirectoryChangesW) with a debounce, "default `2000ms`", "incrementally synced". It reports "a one-file edit re-syncs in ~4" seconds on the Swift compiler repository. It admits one limit: the repo-wide synthesized callback and event edges are rebuilt at most every `CODEGRAPH_SYNTH_MIN_INTERVAL_MS`, and "Until then those edges can be that far behind the code, and tool output doesn't say so" ([README](https://github.com/colbymchenry/codegraph)).
- **Unknowns:** provenance on edges. A bridge hop carries `metadata.resolvedBy: 'framework'`, and a synthesized one carries `provenance:'heuristic'`. A navigation to a computed destination "is left unresolved rather than guessed — and a link written in markup is marked as inferred". A "Fair coverage" metric per language is published: "the share of symbol-bearing source files that have at least one *resolved cross-file dependent*" ([README](https://github.com/colbymchenry/codegraph)).
- **Status:** maintained, last push 2026-11-23. MIT.

#### codebase-memory-mcp (DeusData)

- **Reads:** "164 vendored tree-sitter grammars", plus documents, infrastructure files (Dockerfile, Helm, Terraform, compose) and config files ([README](https://github.com/DeusData/codebase-memory-mcp)).
- **Resolves:** a call graph "import-aware, type-inferred". "Generic package / module resolution: bare specifiers like `@myorg/pkg`, `github.com/foo/bar`, `use my_crate::foo` resolved via manifest scanning (`package.json`, `go.mod`, `Cargo.toml`, ...)". "Hybrid LSP semantic type resolution" for Python, TS/JS/JSX/TSX, PHP, C#, Go, C, C++, Java, Kotlin, Rust and Perl is "a lightweight C implementation of language type-resolution algorithms, structurally inspired by and compatible with major language servers" ([README](https://github.com/DeusData/codebase-memory-mcp)). Cross-service links cover "HTTP route ↔ call-site matching with confidence scoring", gRPC, GraphQL and tRPC.
- **Offered as:** 17 MCP tools, among them `detect_changes` ("maps uncommitted changes to affected symbols with risk classification"), `compare_graphs`, `trace_path` and `get_architecture`. Also a CLI mode and a web UI ([README](https://github.com/DeusData/codebase-memory-mcp)). `install` sets up "46 automatic or conditional client integrations". Its hooks add graph context to searches and reads; they are "context-only and fail-open: it does not replace or block the requested tool call" ([README](https://github.com/DeusData/codebase-memory-mcp)).
- **Freshness:** a background watcher re-indexes git projects registered by MCP sessions. An opt-in, team-shared snapshot `.codebase-memory/graph.db.zst` can be imported, with local changes then applied "incrementally" ([README](https://github.com/DeusData/codebase-memory-mcp)).
- **Unknowns:** confidence values on some edges (an `.env` key "links by substring (confidence 0.75)"). The Lens UI keeps "unresolved registrations" visible. An "Auditor" agent profile has "explicit unresolved limitations" ([README](https://github.com/DeusData/codebase-memory-mcp)).
- **Conflicts with graphe's choices:** semantic search uses "bundled Nomic `nomic-embed-code` embeddings", and the UI has a local chat model ([README](https://github.com/DeusData/codebase-memory-mcp)). That is a neural model, which graphe's no-LLM choice excludes. The rest of the index is deterministic as far as the README says.
- **Status:** maintained, last push 2026-11-26. MIT.

#### GitNexus (one line)

It is a tree-sitter index whose CLI "indexes code locally without an LLM". It has `impact`, `detect_changes` ("Review the impact of a Git diff"), `analyze --watch`, and Claude Code hooks registered by `analyze` ([README](https://github.com/abhigyanpatwari/GitNexus)). It is maintained (last push 2026-11-26). Its licence, PolyForm Noncommercial 1.0.0, keeps it from being a building block. Its resolution and unknowns were not examined.

---

## Code indexes

### SCIP and the scip-* indexers

- **Reads:** SCIP itself reads nothing: it is "a language-agnostic protocol for indexing source code" defined as a Protobuf schema ([README](https://github.com/scip-code/scip)). Each indexer reads one language. scip-java (Java, Scala, Kotlin), scip-typescript, rust-analyzer, scip-clang (C/C++), scip-ruby, scip-python, scip-dotnet (C#, VB), scip-dart and scip-php are listed in the README ([README](https://github.com/scip-code/scip)), and scip-go has its own repository ([scip-go](https://github.com/scip-code/scip-go)). The README lists no Swift indexer.
- **Resolves:** by the compiler or type checker of each language. scip-python is a "Sourcegraph fork of pyright" and needs the project's environment ("make sure to activate your virtual environment") ([scip-python](https://github.com/sourcegraph/scip-python)). scip-go shells out to the `go` command by default ([scip-go](https://github.com/scip-code/scip-go)). A symbol is a global string, `<scheme> ' ' <package> ' ' (<descriptor>)+` or `'local ' <local-id>`, with descriptors for namespaces (`/`), types (`#`), terms (`.`), methods (`().`) and macros (`!`). Occurrences carry roles (`Definition`, `Import`, `WriteAccess`, `ReadAccess`, `Generated`, `Test`, `ForwardDefinition`). Relationships carry `is_reference`, `is_implementation`, `is_type_definition` and `is_definition`, for example `Dog#sound()` with `{symbol: "Animal#sound()", is_implementation:true, is_reference: true}` ([scip.proto](https://github.com/scip-code/scip/blob/main/scip.proto)).
- **Offered as:** an `index.scip` file consumed by Sourcegraph, Glean, Mozilla Searchfox and others ([scip-code.org](https://scip-code.org/)). The `scip` CLI has `lint`, `print`, `snapshot` ("Generate snapshot files for golden testing"), `stats`, `test` and `expt-convert` (to SQLite) ([CLI.md](https://github.com/scip-code/scip/blob/main/docs/CLI.md)). Bindings exist for Go and Rust ("Rich"), and auto-generated ones for TypeScript and Haskell ([README](https://github.com/scip-code/scip)). The README lists no Python binding.
- **Freshness:** batch. The indexer is rerun, typically in CI ("Indexing in CI" in [scip-go](https://github.com/scip-code/scip-go)).
- **Unknowns:** a grep of `scip.proto` for "unresolved", "confidence", "unknown", "approximate" and "heuristic" found nothing. The schema has no field for an unresolved reference or for confidence. Beyond that, nothing was checked.
- **Status:** maintained. The repositories moved: `sourcegraph/scip`, `scip-java` and `scip-go` answer "Moved Permanently" and now live under `scip-code`. scip-python, scip-typescript and scip-clang are still under `sourcegraph`, all pushed on 2026-11-26. scip latest release v0.10.0 (2026-09-03). Apache-2.0 (GitHub API; [README](https://github.com/scip-code/scip)).

### GitHub stack-graphs

- **Reads:** a language's tree-sitter grammar plus rules written for it in a graph DSL (`stack-graphs.tsg`; see [the Python definition](https://github.com/github/stack-graphs/tree/main/languages/tree-sitter-stack-graphs-python/src)). Definitions exist only for Java, JavaScript, Python and TypeScript ([languages/](https://github.com/github/stack-graphs/tree/main/languages)).
- **Resolves:** by the scoping rules of the language, written as data. Stack graphs "allow you to define the name resolution rules for an arbitrary programming language in a way that is efficient, incremental, and does not need to tap into existing build or program analysis tools" ([README](https://github.com/github/stack-graphs)). A reference resolves along a path that keeps a symbol stack and a scope stack. Resolving `A.foo` "pause[s]" the resolution of `foo` to resolve `A` first, and "each 'chunk' of the overall graph only depends on 'local' information from the original source file" ([lib.rs](https://github.com/github/stack-graphs/blob/main/stack-graphs/src/lib.rs)). It is based on TU Delft's scope graphs.
- **Offered as:** Rust crates, and a CLI: `tree-sitter-stack-graphs index SOURCE_DIR`, `status`, `clean`, `query definition SOURCE_PATH:LINE:COLUMN` ([tree-sitter-stack-graphs README](https://github.com/github/stack-graphs/blob/main/tree-sitter-stack-graphs/README.md)).
- **Freshness:** incremental by file. "An incremental analysis is one where we can reuse analysis results for source code files that haven't changed" ([lib.rs](https://github.com/github/stack-graphs/blob/main/stack-graphs/src/lib.rs)). "Indexing will skip any files that have already be indexed" ([CLI README](https://github.com/github/stack-graphs/blob/main/tree-sitter-stack-graphs/README.md)).
- **Unknowns:** **not verified**. One related rule: a definition's MAJOR version must rise when "some of these resolutions are missing" compared with the previous version ([languages README](https://github.com/github/stack-graphs/blob/main/languages/README.md)), which treats lost resolutions as a breaking change.
- **Status:** **archived**. "This repository was archived by the owner on Sep 9, 2025", "no longer supported or updated by GitHub" ([README](https://github.com/github/stack-graphs)). Apache-2.0 or MIT. It is the closest in spirit to graphe's generic reader, tree-sitter plus per-language data, but it is a concept to borrow, not a dependency to adopt.

### Kythe

- **Reads:** compilations. "Indexer implementations for C++, Go, and Java" and "Compilation extractors for javac, Maven, cmake, Go, and Bazel" ([README](https://github.com/kythe/kythe)). The overview page lists indexers for C++ and Java, with Go as coming soon ([overview](https://kythe.io/docs/kythe-overview.html)); the README is the newer statement.
- **Resolves:** by the compiler. A language plugs in through a compiler "that can be instrumented to produce an indexer that emits Kythe data" ([overview](https://kythe.io/docs/kythe-overview.html)). The schema has `ref/call` ("A ref/call F if A is an anchor that calls F"), `ref/imports`, `overrides` and `overrides/transitive`, and for macros `ref/expands` and `ref/expands/transitive` ([schema](https://kythe.io/docs/schema/)). Generated code is linked to its source through `generates` edges. Protobuf's `protoc` writes a `.meta` file (`GeneratedCodeInfo`), and the C++ indexer uses it to "append `generates` edges". Other generators embed a mapping that yields `imputes`, then `generates` ([indexing generated code](https://kythe.io/docs/schema/indexing-generated-code.html)).
- **Offered as:** a graph of facts, with "a self-contained server that can use Kythe data to answer cross-reference queries" ([overview](https://kythe.io/docs/kythe-overview.html)).
- **Freshness:** batch, per build. Incremental behaviour is **not verified**.
- **Unknowns:** **not verified**.
- **Status:** maintained but slow. Latest release v0.0.76 (2026-07-16), last commit 2026-09-18. Apache-2.0 (GitHub API).

### Meta's Glean

- **Reads:** "full support" for C++/C, Hack, Haskell, JavaScript/Flow and Python. Rust, Go, TypeScript, Java, Python and .NET come in through SCIP or LSIF ([README](https://github.com/facebookincubator/Glean)).
- **Resolves:** by the indexers (compilers or SCIP producers). Glean stores and derives facts: Angle is "a logic language with similarities to Datalog", "currently limited to non-recursive queries only" ([introduction](https://glean.software/docs/introduction)).
- **Offered as:** a server over Thrift; Glass, "a language-agnostic symbol server", which powers Glean's LSP server ([introduction](https://glean.software/docs/introduction)).
- **Freshness:** incremental databases by ownership. Each fact has an owner (a "unit", usually a file or module), and a slice hides the units that changed. A fact of owner A that refers to a fact of owner B gets the owner A || B, and a derived fact's owner is the conjunction of its sources' owners. Incremental derivation on stacked databases "isn't implemented yet" ([incrementality](https://glean.software/docs/implementation/incrementality)).
- **Unknowns:** **not verified**.
- **Status:** maintained, last push 2026-11-26. "Glean is licensed under a BSD LICENSE" ([README](https://github.com/facebookincubator/Glean)).

---

## Static analysis

### CodeQL

- **Reads:** "a single relational representation of each source file", imported into a database that "contains a full, hierarchical representation of the code, including a representation of the abstract syntax tree, the data flow graph, and the control flow graph" ([about CodeQL](https://codeql.github.com/docs/codeql-overview/about-codeql/)). Compiled languages normally need a build. "for C/C++, C#, Java and Rust, there is an option to generate a database without building the code", and Python and JS/TS need none ([preparing code](https://docs.github.com/en/code-security/codeql-cli/getting-started-with-the-codeql-cli/preparing-your-code-for-codeql-analysis)).
- **Resolves:** by types, with dispatch modelled. In Java, "`getCallee` returns the `Callable` that this call (statically) resolves to", and `polyCalls(Callable target)` "succeeds if this callable may call `target` at runtime", which includes overriding methods ([navigating the call graph](https://codeql.github.com/docs/codeql-language-guides/navigating-the-call-graph/)). Frameworks are modelled per language: Django, Flask, FastAPI, Spring MVC, express, nest.js, ASP.NET Core, Rails, Gin, axum... ([supported frameworks](https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks/)).
- **Offered as:** the QL query language, "a specially-designed object-oriented query language" ([about CodeQL](https://codeql.github.com/docs/codeql-overview/about-codeql/)), run by the CLI or by GitHub code scanning.
- **Freshness:** two modes for pull requests. **Diff-informed analysis** "reports only alerts in lines that were added or modified in the pull request diff". **Overlay analysis** "reuses a cached database from your default branch". Changed files are found by comparing `git ls-files --recurse-submodules --format='%(objectname)_%(path)'` against the stored OID map; a file is changed when it was added or removed, or its OID differs ([incremental analysis](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/scan-from-the-command-line/incremental-analysis)).
- **Unknowns:** builds "create databases that include generated code", so a database made without a build lacks it ([preparing code](https://docs.github.com/en/code-security/codeql-cli/getting-started-with-the-codeql-cli/preparing-your-code-for-codeql-analysis)). How unresolved calls are reported is **not verified**.
- **Status:** maintained (`github/codeql` pushed 2026-11-27). Two licences, kept apart. The queries and libraries in `github/codeql` are MIT (GitHub API). The CLI binaries may be used only for stated purposes (academic research, demos, open-source codebases, CI on open-source code hosted on GitHub), and "may not be used for any purpose not expressly set forth above" ([CLI licence](https://github.com/github/codeql-cli-binaries/blob/main/LICENSE.md)).

### Joern

- **Reads:** source, bytecode and binaries, through frontends: `c2cpg`, `csharp2cpg`, `gosrc2cpg`, `javasrc2cpg`, `jimple2cpg`, `jssrc2cpg`, `kotlin2cpg`, `php2cpg`, `pysrc2cpg`, `rubysrc2cpg`, `swiftsrc2cpg`, `ghidra2cpg` ([frontends](https://docs.joern.io/frontends/)).
- **Resolves:** each frontend builds a code property graph (CPG). For dynamic languages, a type-recovery pass runs a set number of `iterations` and can use "placeholder dummy values for partially resolved types during the final iteration" ([XTypeRecovery.scala](https://github.com/joernio/joern/blob/master/joern-cli/frontends/x2cpg/src/main/scala/io/joern/x2cpg/passes/frontend/XTypeRecovery.scala)).
- **Offered as:** "a Scala-based domain-specific query language" in a REPL, and `joern --server` ([README](https://github.com/joernio/joern)). The CPG spec is at cpg.joern.io.
- **Freshness:** **not verified**. The README describes building a CPG, not updating one.
- **Unknowns:** an unresolved call keeps what is known in its full name. "The METHOD_FULL_NAME should be given as `<unresolvedNamespace>.foo:<unresolvedSignature>(1)`. If the namespace is known the METHOD_FULL_NAME should be given as `some.namespace.foo:<unresolvedSignature>(1)`". A dynamic call with no static information is `<unknownFullName>` ([Defines.scala](https://github.com/joernio/joern/blob/master/joern-cli/frontends/x2cpg/src/main/scala/io/joern/x2cpg/Defines.scala)).
- **Status:** maintained. A release is made daily; the latest is v4.0.693 (2026-11-26). Apache-2.0 (GitHub API; [README](https://github.com/joernio/joern)).

### pyan (Technologicat/pyan, "pyan3")

- **Reads:** Python 3.10 to 3.14, through `ast` ([README](https://github.com/Technologicat/pyan)).
- **Resolves:** by tracked bindings with lexical scoping. "if `self.a = MyFancyClass()`, the analyzer knows that any references to `self.a` point to `MyFancyClass`". It also handles MRO-respecting lookup of inherited attributes, `super()`, and parameter annotations ("`def f(obj: Thing): obj.method()` draws an edge to `Thing.method`"). An unresolved attribute becomes a wildcard `*.name`, which since this version expands only to "targets whose module is actually imported" ("Import-aware wildcard resolution"). The old expansion "often generated spurious uses edges (because the wildcard to `*.name` expands to `X.name` _for all_ `X` that have an attribute called `name`.)" ([README](https://github.com/Technologicat/pyan)).
- **Offered as:** a CLI and a Python API with DOT, SVG, HTML and plain-text output ("Output plain text — especially useful for feeding call graph info to coding AI agents"). Its queries are `--function X --direction up|down`, `--paths-from A --paths-to B` and `--depth`, plus `--module-level` import graphs with `-C` cycle detection ([README](https://github.com/Technologicat/pyan)).
- **Freshness:** run per invocation. The README mentions no cache or incremental mode.
- **Unknowns:** wildcard nodes for names it cannot resolve. Annotations with `Optional[X]`, unions or strings "resolve to nothing" ([README](https://github.com/Technologicat/pyan)).
- **Status:** maintained ("Pyan3 is back in development"). v2.9.0 (2026-10-06). GPL-2.0 (GitHub API).

### PyCG (vitsalis/PyCG)

- **Reads:** a Python package, Python 3.12 or later. "it never imports or runs the code that it analyses" ([README](https://github.com/vitsalis/PyCG)).
- **Resolves:** by following values. It resolves "calls through variables, arguments, return values, attributes and containers", "methods through class hierarchies, `super()`, decorators, properties and descriptors", and "the calls that the interpreter makes without a call expression (`for`, `with`, operators, subscripts, `await` and others)". External calls are named "through type stubs" ([README](https://github.com/vitsalis/PyCG)). The first version is described in the ICSE 2021 paper cited by the README.
- **Offered as:** a CLI that writes one JSON document, and `pycg-view`, a standalone HTML page with callers and callees ([README](https://github.com/vitsalis/PyCG)).
- **Freshness:** run per invocation. "The document is deterministic: the same input gives the same bytes on every run" ([README](https://github.com/vitsalis/PyCG)).
- **Unknowns:** explicit. The document lists "the calls whose callee is not known, with the cause". `--cap N` bounds the objects kept per expression: "past it the value is treated as unknown, and calls through it are reported as unresolved (saturated)". The test suite keeps the failing micro-benchmark cases "each with its cause, in `tests/known_failures.txt`, as strict expected failures" ([README](https://github.com/vitsalis/PyCG)).
- **Status:** "PyCG is maintained again. The repository was archived in November 2023. Development restarted in 2026". The new engine "is not on PyPI yet (`pip install pycg` gives the 2021 version)" ([README](https://github.com/vitsalis/PyCG)). Last push 2026-11-27. Apache-2.0 (GitHub API).

---

## JS/TS dependencies

### dependency-cruiser

- **Reads:** JS, TS, CoffeeScript and LiveScript (ES6, CommonJS, AMD), plus `.jsx`, `.tsx`, `.vue` and `.svelte` through their compilers when installed, as `--info` lists them ([README](https://github.com/sverweij/dependency-cruiser); [cli.md](https://github.com/sverweij/dependency-cruiser/blob/main/doc/cli.md)).
- **Resolves:** modules, not calls: an import to the file it resolves to, honouring `--ts-config` and `--webpack-config` ([cli.md](https://github.com/sverweij/dependency-cruiser/blob/main/doc/cli.md)).
- **Offered as:** a CLI that validates rules (`forbidden`, with `circular`, `orphan`, `reachable`, `couldNotResolve`...) and reports in text, dot, mermaid, json, html ([rules reference](https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-reference.md)). `--affected <revision>`: "Only include modules changed since the revision + all modules that can reach them", which is "'syntactic sugar' around the `--reaches` option", with a GitHub Actions recipe that puts the graph in the PR summary. `--baseline` records known violations so only new ones fail ([cli.md](https://github.com/sverweij/dependency-cruiser/blob/main/doc/cli.md)).
- **Freshness:** `--cache`, invalidated on "changes to files that would be part of a cruise", detected "By default ... [with] `git`" (`--cache-strategy metadata`), or by content ([cli.md](https://github.com/sverweij/dependency-cruiser/blob/main/doc/cli.md)).
- **Unknowns:** `couldNotResolve` is a module property a rule can match: "To get an error for each unresolvable dependency" ([rules reference](https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-reference.md)).
- **Status:** maintained. v18.9.0 (2026-11-22). MIT (GitHub API).

### madge

- **Reads:** JS/TS module graphs through `dependency-tree` / `filing-cabinet`, with `requireConfig`, `webpackConfig` and `tsConfig` for aliases ([README](https://github.com/pahen/madge)).
- **Resolves:** modules, not calls.
- **Offered as:** a CLI and an API: `--circular`, `--orphans`, `--image`, `.warnings()` ([README](https://github.com/pahen/madge)).
- **Freshness:** run per invocation.
- **Unknowns:** "Run madge with the `--warning` option to see skipped files" ([README](https://github.com/pahen/madge)).
- **Status:** not archived, but dormant. The last commit is "Release 8.0.0" on 2024-08-05, and npm's latest is 8.0.0 of the same day ([npm registry](https://registry.npmjs.org/madge)). MIT.

---

## Ideas for graphe

Ranked by value for graphe. The value is measured, where possible, by the backlog's own counts (calls left `ambiguous` or `common`, the cost of a query) against the cost of the change. The costs are rough: **S** is a day or two, **M** a ticket of a week, **L** several tickets.

### 1. A diff-impact command

- **Feature:** `graphe affected [REV]` maps `git diff -U0 REV` hunks to the nodes whose line extent they touch (graphe already stores each body's start and end line), then prints those nodes' callers to a depth. A file list on stdin would also work.
- **Who does it:** dependency-cruiser `--affected <revision>`, built on `--reaches` ([cli.md](https://github.com/sverweij/dependency-cruiser/blob/main/doc/cli.md)); CodeGraph `codegraph affected` with `git diff --name-only | codegraph affected --stdin` ([README](https://github.com/colbymchenry/codegraph)); codebase-memory-mcp and GitNexus `detect_changes` ([CBM](https://github.com/DeusData/codebase-memory-mcp), [GitNexus](https://github.com/abhigyanpatwari/GitNexus)); CodeQL's diff-informed analysis by changed line ranges ([incremental analysis](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/scan-from-the-command-line/incremental-analysis)).
- **Backlog:** "What a diff reaches takes one `callers` per function."
- **Cost:** S. It reuses `callers --depth` and the line extents.
- **Conflicts:** none. The `[by name]` marks and the "+ N calls" lines carry over to each changed node.

### 2. Qualifier- and import-scoped linking in the generic reader

- **Feature:** narrow a name's candidates before the "one definition" test. `pkg.F()` keeps only definitions in the package the file imports under `pkg`. `T::f()` / `C.f()` keeps only methods of the host class `T`. A bare call keeps candidates in the imported files. A call is still linked only when one candidate is left, so a link stays exact.
- **Who does it:** pyan's "Import-aware wildcard resolution — `*.name` wildcards only expand to targets whose module is actually imported" ([README](https://github.com/Technologicat/pyan)). codebase-memory-mcp resolves `github.com/foo/bar` and `use my_crate::foo` "via manifest scanning (`go.mod`, `Cargo.toml`, ...)" ([README](https://github.com/DeusData/codebase-memory-mcp)). Joern keeps a known namespace in an unresolved name (`some.namespace.foo:<unresolvedSignature>(1)`) ([Defines.scala](https://github.com/joernio/joern/blob/master/joern-cli/frontends/x2cpg/src/main/scala/io/joern/x2cpg/Defines.scala)). stack-graphs is the full form, scoping rules as per-language data on tree-sitter, but it is archived ([README](https://github.com/github/stack-graphs)).
- **Backlog:** "The generic reader cannot tell a Go package's function from another's." (29123 `ambiguous`, 24888 `common` on gitea), and "A Rust `Type::f()` path is not linked when `f` is a common name." (14660 `common` sends, 8944 `ambiguous` on libsignal; the entry adds "Java's `C.f()` too").
- **Cost:** M for the `T::f` / `C.f` rule. L for Go, where the import path maps to a directory through `go.mod`, which is code: ADR 0003 prices a dedicated reader at "several hundred lines and one ticket per language".
- **Conflicts:** ADR 0003 links "by its name alone", and the Rust entry already says "outside 'by the name alone' (ADR 0003), to decide". It needs an ADR 0003 amendment. Go's module-path mapping is "code of its own", which ADR 0003 calls "the proof that it needs a dedicated reader". So for Go this is the dedicated Go reader the backlog entry names, not a generic-reader tweak. The `T::f` / `C.f` rule (the qualifier names a class of the host) is data-light and could stay generic. It fits "exact links over guessed ones", because it only links when one candidate is left.

### 3. Tell generated and duplicated files apart

- **Feature:** at build time, mark a file as generated when git says so (`git check-attr linguist-generated`) or when its header carries a known marker. Two uses, kept distinct. (a) Name the generated files in `check` and REPORT.md, with a suggested `exclude`; this is cheap and changes no link. (b) Drop a generated file's definitions from the candidates when the same name also has a non-generated definition, or when the generated files are copies of one another; this changes links and must be measured on protobuf.
- **Who does it:** Linguist's `linguist-generated` attribute, read from `.gitattributes` ([overrides](https://github.com/github-linguist/linguist/blob/main/docs/overrides.md)), with header detectors such as `"Generated by the protocol buffer compiler.  DO NOT EDIT!"` ([generated.rb](https://github.com/github-linguist/linguist/blob/main/lib/linguist/generated.rb)). That string is the one the backlog quotes for protobuf's Java. Go's convention, "`^// Code generated .* DO NOT EDIT\.$`", must "appear before the first non-comment, non-blank text in the file" ([cmd/go](https://pkg.go.dev/cmd/go#hdr-Generate_Go_files_by_processing_source)). SCIP's `Generated = 0x10` role ([scip.proto](https://github.com/scip-code/scip/blob/main/scip.proto)). Kythe's `generates` edges ([generated code](https://kythe.io/docs/schema/indexing-generated-code.html)).
- **Backlog:** "Generated Java code repeated in a host makes its names ambiguous." (57518 `ambiguous`, 19863 without the copies), "C#'s generated messages make their methods' names ambiguous.", and "A C amalgamation makes every name it repeats ambiguous." (79088 down to 56664 without the 4 files). Whether upb's amalgamated files carry a generated header is **not verified**; if not, only `linguist-generated` or a "same function body defined in N files" test would catch them.
- **Cost:** S for (a); M for (b), with protobuf as the measure.
- **Conflicts:** none with ADR 0003. A marker list is a language's data. Rule (b) must not hide a generated definition that is the only one: protobuf's generated messages are real code that the host calls.

### 4. An MCP server

- **Feature:** `graphe mcp` serves `explain`, `callers`, `path` and `search` as MCP tools over stdio, with the same text the CLI prints. The usage guidance goes in the `initialize` response.
- **Who does it:** Serena ([README](https://github.com/oraios/serena)); CodeGraph, which sends "its usage guidance to your agent automatically, in the MCP `initialize` response" and sets `alwaysLoad` because Claude Code "otherwise defers every MCP tool behind a tool-search step" ([README](https://github.com/colbymchenry/codegraph)); codebase-memory-mcp ([README](https://github.com/DeusData/codebase-memory-mcp)).
- **Backlog:** "A query needs a Bash permission, or it falls back to grep."
- **Cost:** S to M: a thin layer over the existing commands, plus an MCP library dependency.
- **Conflicts:** none with the no-LLM choice. The entry's "would need no shell rule" holds, but the permission step does not disappear. CodeGraph still suggests `"mcp__codegraph__*"` in `permissions.allow` "for auto-allow" ([README](https://github.com/colbymchenry/codegraph)). The gain is that one rule fits every OS (no Bash/PowerShell pair), and that agents speaking MCP but no shell are reached.

### 5. Read `.jsx`, `.tsx` and Vue

- **Feature:** route `.jsx` and `.tsx` to the JS reader with the TSX grammar, and give `.vue` the Svelte path (script plus template expressions).
- **Who does it:** dependency-cruiser's `--info` lists `.jsx`, `.tsx`, `.vue` and `.svelte` among its extensions ([cli.md](https://github.com/sverweij/dependency-cruiser/blob/main/doc/cli.md)). CodeGraph lists Vue, Svelte and Astro, and links Angular templates' `<app-foo>` "to the component that renders them" ([README](https://github.com/colbymchenry/codegraph)).
- **Backlog:** "`.jsx`, `.tsx` and Vue are not read."
- **Cost:** S for `.jsx`/`.tsx` (the backlog notes the grammars are already installed); M for Vue.
- **Conflicts:** none. A JSX `<Component/>` as a link belongs to idea 10.

### 6. Override families: link a call to the declaration its candidates share

- **Feature:** make abstract and interface methods (and Swift protocol requirements) nodes, with `overrides` links from each implementation. When every candidate of an ambiguous send overrides one declaration, link the call to that declaration (sure, not `[by name]` across the family). `callers` of an implementation then lists the calls through its declaration, marked as possible.
- **Who does it:** CodeQL separates `calls` (static target) from `polyCalls` ("may call `target` at runtime") ([call graph](https://codeql.github.com/docs/codeql-language-guides/navigating-the-call-graph/)). SCIP relates `Dog#sound()` to `Animal#sound()` with `is_implementation` ([scip.proto](https://github.com/scip-code/scip/blob/main/scip.proto)). Kythe has `overrides` and `overrides/transitive` ([schema](https://kythe.io/docs/schema/)). Serena exposes "find implementations" where the language server can ([README](https://github.com/oraios/serena)).
- **Backlog:** "A Java call to an abstract method is linked to none of its implementations." (407 `pushLimit` calls) and "Swift's FFI conformances make their methods' names ambiguous." (the entry names "the protocol's requirement as a node").
- **Cost:** M. It needs new captures for abstract and protocol methods and for base lists, then one rule in the linker.
- **Conflicts:** a new rule beyond "the name alone", so an ADR 0003 amendment. It does not link an ambiguous name to all its candidates (ADR 0003's rejected `?` option). It links to one declaration that exists in the code.

### 7. Say why a call was not attributed

- **Feature:** today the line is "+ {count} calls named `{name}` the graph could not attribute: grep them" (`src/graphe/cli.py`, `_missed`). It could add the cause and, when short, the candidates: "407 `ambiguous` between `ArrayDecoder.pushLimit`, `StreamDecoder.pushLimit`", "`common` name", "receiver of unknown type". The agent then knows whether a grep is worth it.
- **Who does it:** PyCG lists "the calls whose callee is not known, with the cause", and marks saturated values as "unresolved (saturated)" ([README](https://github.com/vitsalis/PyCG)). Joern keeps what is known (`some.namespace.foo:<unresolvedSignature>(1)`) ([Defines.scala](https://github.com/joernio/joern/blob/master/joern-cli/frontends/x2cpg/src/main/scala/io/joern/x2cpg/Defines.scala)). CodeGraph tags edges `resolvedBy` and `provenance` ([README](https://github.com/colbymchenry/codegraph)).
- **Backlog:** new. It extends the settled T-0025 ("`explain` does not say what it misses.").
- **Cost:** S. The categories already exist in `check`'s sites.
- **Conflicts:** none. It makes the existing honesty more precise.

### 8. Incremental resolution keyed on git blob ids

- **Feature:** store each file's git blob id (`git ls-files --format='%(objectname)_%(path)'`) with its cached definitions and sites. On a stale query, re-read only the changed files. Re-resolve only the sites whose name's definition set changed: a by-name link depends only on the definitions bearing that name. For Python's import resolution, re-resolve the files that import a changed module.
- **Who does it:** CodeQL's overlay analysis diffs exactly that `git ls-files` OID map against the base database ([incremental analysis](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/scan-from-the-command-line/incremental-analysis)). Glean gives each fact an owner unit and propagates ownership to facts that refer across units ([incrementality](https://glean.software/docs/implementation/incrementality)). stack-graphs keeps each file's graph dependent only on that file ([lib.rs](https://github.com/github/stack-graphs/blob/main/stack-graphs/src/lib.rs)). dependency-cruiser's cache is invalidated through git ([cli.md](https://github.com/sverweij/dependency-cruiser/blob/main/doc/cli.md)). CodeGraph's watcher re-syncs one edit in seconds (self-reported, [README](https://github.com/colbymchenry/codegraph)).
- **Backlog:** "On a large repository, a stale query still waits for the whole resolution." (~68 s per stale query on Django; protobuf's C/C++ has no cache).
- **Cost:** M for the generic reader (the by-name rule makes the dependency easy to track); L for the Python reader's cross-module resolution.
- **Conflicts:** none. The graph must stay identical to a full build, which a test can check on the sample hosts.

### 9. Read a SCIP index when the host has one

- **Feature:** an opt-in input. If the host produces `index.scip` (scip-go, rust-analyzer, scip-java, scip-dotnet, scip-clang), graphe maps its occurrences to its own nodes by file and range and upgrades the matching `[by name]` or unattributed calls to sure links.
- **Who does it:** Glean ingests SCIP and LSIF for Rust, Go, TypeScript, Java, Python and .NET ([README](https://github.com/facebookincubator/Glean)); Sourcegraph and Searchfox consume it ([scip-code.org](https://scip-code.org/)).
- **Backlog:** it touches most receiver entries at once: "A Java call to an abstract method is linked to none of its implementations.", "C#'s generated messages make their methods' names ambiguous.", "The generic reader cannot tell a Go package's function from another's.", "A Rust `Type::f()` path is not linked when `f` is a common name.", "A Kotlin extension function of one name on several types is ambiguous.", and perhaps "A Rust call inside a macro is not seen." (SCIP has a macro descriptor `!` ([scip.proto](https://github.com/scip-code/scip/blob/main/scip.proto)), but whether rust-analyzer's SCIP covers calls inside macro arguments is **not verified**). There is no Swift indexer in SCIP's list ([README](https://github.com/scip-code/scip)).
- **Cost:** M to L. Python has no listed SCIP binding, so it means generating one from `scip.proto` (a protobuf dependency). The index goes stale between indexer runs, so graphe must say when it is older than the code.
- **Conflicts:** real ones. The indexers need the host's build environment (scip-python needs the virtualenv, scip-go runs `go`), and ADR 0002 set the TypeScript compiler aside because it "would depend on each host's `tsconfig`". As a file the host chooses to produce, it would not make graphe a two-language program. It could be a local extension (ADR 0001) before it is a core feature. The freshness rule ("A query on a graph older than the code ... rebuilds it first") cannot rebuild a SCIP index itself.

### 10. Framework presets for keyed links

- **Feature:** ship `[keys]` pattern presets for common frameworks (Flask/FastAPI decorators, Express `app.get`, Gin `r.GET`, Django `path()`) that a host turns on in `graphe.toml`. Keys that are no string on one line (JSX tags, DI) remain outside.
- **Who does it:** CodeGraph's route table for more than 20 frameworks, with `route` nodes and `navigates` edges ([README](https://github.com/colbymchenry/codegraph)). codebase-memory-mcp's "HTTP route ↔ call-site matching with confidence scoring" ([README](https://github.com/DeusData/codebase-memory-mcp)). CodeQL's per-language framework models ([supported frameworks](https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks/)).
- **Backlog:** "The links a framework creates are outside the graph." The entry's leftover is "the frameworks, whose key is no string on one line".
- **Cost:** S per preset that a regex can express; L for decorators that span lines, JSX and injection.
- **Conflicts:** none for regex presets, which are data on an existing mechanism. Confidence-scored matching (CBM) would go against "exact links over guessed ones" unless it stays marked as guessed.

### 11. Fail-open agent hooks and installs for several agents

- **Feature:** `graphe install --agent auto` writes the skill or instructions for each detected agent. An optional PreToolUse hook adds a graph hint to a grep or read of a code name, without blocking it.
- **Who does it:** codebase-memory-mcp's "Search and read hooks", which are "context-only and fail-open", across "46 automatic or conditional client integrations" ([README](https://github.com/DeusData/codebase-memory-mcp)); CodeGraph `install --target=auto` ([README](https://github.com/colbymchenry/codegraph)); GitNexus registers Claude Code hooks ([README](https://github.com/abhigyanpatwari/GitNexus)).
- **Backlog:** "The skill reaches Claude Code alone, and only for the questions it names." (graphify's hooks are already noted there).
- **Cost:** M, mostly per-agent configuration formats.
- **Conflicts:** none. Fail-open keeps grep available when the graph is wrong.

### 12. Use tree-sitter's `locals.scm` to tell a variable from a bare call

- **Feature:** run the grammar's locals query (`@local.scope`, `@local.definition`, `@local.reference`) so that a bare identifier not defined as a local in an enclosing scope counts as a call.
- **Who does it:** tree-sitter's local-variable queries ([syntax highlighting docs](https://tree-sitter.github.io/tree-sitter/3-syntax-highlighting.html)). stack-graphs is the general form ([lib.rs](https://github.com/github/stack-graphs/blob/main/stack-graphs/src/lib.rs)).
- **Backlog:** "A Ruby bare call is missed, as a variable is." The entry names `locals.scm`.
- **Cost:** S to M. It is query data plus one pass in the generic reader.
- **Conflicts:** none, as long as it stays data per language (ADR 0003).

### 13. A regression gate on resolutions

- **Feature:** a snapshot of each sample host's link counts, or of a small annotated fixture per language. A change that loses resolutions fails, unless the loss is listed with its cause.
- **Who does it:** `scip snapshot` / `scip test` "for golden testing" ([CLI.md](https://github.com/scip-code/scip/blob/main/docs/CLI.md)). PyCG's `tests/known_failures.txt` as "strict expected failures" with causes ([README](https://github.com/vitsalis/PyCG)). stack-graphs' MAJOR bump when "some of these resolutions are missing" ([languages README](https://github.com/github/stack-graphs/blob/main/languages/README.md)). CodeGraph checks its Rust kernel's graphs "byte-for-byte identical to the reference engine" ([README](https://github.com/colbymchenry/codegraph)).
- **Backlog:** new. It protects every reader entry, including grammar upgrades ("A Go generic method is no node." waits on one).
- **Cost:** S to M.
- **Conflicts:** none.

### 14. A token-budgeted, ranked map

- **Feature:** `graphe map --tokens N` gives the most central definitions with their signatures, ranked by PageRank on the sure links and personalised by named files.
- **Who does it:** Aider's repo map (`nx.pagerank` with personalization, `--map-tokens`) ([repomap.py](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py); [docs](https://aider.chat/docs/repomap.html)).
- **Backlog:** new. REPORT.md already lists "the most connected nodes".
- **Cost:** S.
- **Conflicts:** Aider weights ambiguous candidates instead of refusing them, which is against ADR 0003. Ranking only graphe's sure links avoids that. The value is low: graphe answers questions, it does not fill a prompt.

### Not taken

- **Macros by expansion** (Kythe `ref/expands`, compiler-based indexers): every tool that sees inside macros does so through a compiler. No tree-sitter technique was found in these sources for "A Rust call inside a macro is not seen.", "A C++ class whose declaration an `#ifdef` cuts is lost." or "A file's gtest tests are one function.". The backlog's own idea (parse a token tree as expressions) stays the only cheap path. Idea 9 is the expensive one.
- **Cross-language FFI/JNI bridges** (CodeGraph's Swift to Objective-C and React Native resolvers, [README](https://github.com/colbymchenry/codegraph)): each is framework-specific code. "A call across languages by a translated name is not linked." notes that none of the user's hosts has one. Revisit when a host does.
- **Embedding search and chat** (codebase-memory-mcp): a neural model, against the no-LLM choice.
- **Architecture rules with a baseline** (dependency-cruiser `forbidden` rules and `--baseline`, [cli.md](https://github.com/sverweij/dependency-cruiser/blob/main/doc/cli.md)): useful, but a linter's job, not a navigation graph's.

---

## Sources

Status of every GitHub repository: `https://api.github.com/repos/<owner>/<repo>` and `.../releases/latest`, read 2026-11-27.

- Serena: https://github.com/oraios/serena; https://oraios.github.io/serena/01-about/035_tools.html; https://oraios.github.io/serena/02-usage/040_workflow.html
- Aider: https://aider.chat/docs/repomap.html; https://github.com/Aider-AI/aider/blob/main/aider/repomap.py
- CodeGraph: https://github.com/colbymchenry/codegraph
- codebase-memory-mcp: https://github.com/DeusData/codebase-memory-mcp
- GitNexus: https://github.com/abhigyanpatwari/GitNexus
- SCIP: https://github.com/scip-code/scip; https://github.com/scip-code/scip/blob/main/scip.proto; https://github.com/scip-code/scip/blob/main/docs/CLI.md; https://scip-code.org/; https://github.com/scip-code/scip-go; https://github.com/sourcegraph/scip-python
- stack-graphs: https://github.com/github/stack-graphs; https://github.com/github/stack-graphs/blob/main/stack-graphs/src/lib.rs; https://github.com/github/stack-graphs/blob/main/tree-sitter-stack-graphs/README.md; https://github.com/github/stack-graphs/tree/main/languages; https://github.com/github/stack-graphs/blob/main/languages/README.md
- Kythe: https://github.com/kythe/kythe; https://kythe.io/docs/kythe-overview.html; https://kythe.io/docs/schema/; https://kythe.io/docs/schema/indexing-generated-code.html
- Glean: https://github.com/facebookincubator/Glean; https://glean.software/docs/introduction; https://glean.software/docs/implementation/incrementality
- CodeQL: https://codeql.github.com/docs/codeql-overview/about-codeql/; https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks/; https://codeql.github.com/docs/codeql-language-guides/navigating-the-call-graph/; https://docs.github.com/en/code-security/codeql-cli/getting-started-with-the-codeql-cli/preparing-your-code-for-codeql-analysis; https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/scan-from-the-command-line/incremental-analysis; https://github.com/github/codeql-cli-binaries/blob/main/LICENSE.md
- Joern: https://github.com/joernio/joern; https://docs.joern.io/frontends/; https://github.com/joernio/joern/blob/master/joern-cli/frontends/x2cpg/src/main/scala/io/joern/x2cpg/Defines.scala; https://github.com/joernio/joern/blob/master/joern-cli/frontends/x2cpg/src/main/scala/io/joern/x2cpg/passes/frontend/XTypeRecovery.scala
- pyan: https://github.com/Technologicat/pyan
- PyCG: https://github.com/vitsalis/PyCG
- dependency-cruiser: https://github.com/sverweij/dependency-cruiser; https://github.com/sverweij/dependency-cruiser/blob/main/doc/cli.md; https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-reference.md
- madge: https://github.com/pahen/madge; https://registry.npmjs.org/madge
- For the ideas: https://tree-sitter.github.io/tree-sitter/3-syntax-highlighting.html; https://pkg.go.dev/cmd/go#hdr-Generate_Go_files_by_processing_source; https://github.com/github-linguist/linguist/blob/main/docs/overrides.md; https://github.com/github-linguist/linguist/blob/main/lib/linguist/generated.rb
- graphe's own: `README.md`, `BACKLOG.md` ("Open"), `docs/adr/0001-one-tool-local-extensions.md`, `docs/adr/0002-tree-sitter-for-new-readers.md`, `docs/adr/0003-generic-reader-by-name.md`, `src/graphe/cli.py` (`_missed`).
