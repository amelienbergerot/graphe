# A generic reader by name for the other languages, a dedicated reader on proof

Java, C#, Go, Rust, Ruby, C, C++, Swift and Kotlin are read by one generic reader: it runs, on each language's tree-sitter grammar from PyPI, queries of ours (definitions, calls) and links a call by its name alone, only when that name has a single definition in the same language; the other calls are counted as not attributed, so that `explain` tells the agent to grep them. No call is linked by name to another language. A language gets a dedicated reader (imports, receivers, like the JS reader) only when `BACKLOG.md` shows the generic one falls short on a real host.

The graph of such a host does not lift an ambiguous name, which is what the graph does best against grep; it still gives what grep does not: what a function calls, `path`, `callers --depth`, and the documents that cite the code.

The queries are written from the `tags.scm` the grammars ship, but kept in this repository, one capture convention for all, each tested on a snippet, and specified per language in `docs/readers.md`. Run as shipped (py-tree-sitter 0.26.1, 2026-11-18), the upstream ones fall short: C, C++ and Swift capture no call, C# no bare call `f()`, Ruby takes a variable for a call, and C#'s wheel stores its queries outside its package.

A language is data only: its grammars, its queries, the method names never linked by name. A quirk the queries cannot express is a `shortcut:` in `docs/readers.md`; a language that needs code of its own is the proof that it needs a dedicated reader.

## Options set aside

- The upstream `tags.scm` as shipped, completed where they fall short: eight capture conventions, and a grammar's upgrade changes the graph silently.

- A dedicated reader per language at once: several hundred lines and one ticket per language before any host gains anything, for languages no host has asked for yet.
- Linking an ambiguous name to all its candidates (`?`): `callers` overflows on a large repository, and a false link costs the agent more than a missing one it is told about.
