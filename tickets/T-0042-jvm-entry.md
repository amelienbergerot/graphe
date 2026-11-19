Status: ready-for-agent
Type: task
Created: 2026-11-19

# T-0042: Kotlin and Java, one JVM entry

## What to build

A Kotlin call to a Java definition of its host is linked by name, as a C++ call to a C function is since T-0034: Java and Kotlin become one entry of the readers' registry, each file still read with its own grammar and queries. On libsignal, 488 of the 1822 Kotlin sites `external` name a definition of its Java (`nativeHandle` 71, `makeCancelable` 69, `fakeConnect` 58, `guardedMap` 48). The "same language" rule of ADR 0003 becomes "same family" for the JVM too: the ADR is amended, as for C/C++. BACKLOG.md: "Kotlin's calls to its host's Java are not linked".

## Acceptance criteria

- [ ] One entry reads `.java` and Kotlin's suffixes, each with its grammar and queries; the common names are the union of both lists, checked against libsignal's and protobuf's most frequent names by name.
- [ ] A test at `contribute(project)`: a Kotlin call to a function defined in a `.java` file is linked, and the reverse; `Foo.java` and `Foo.kt` still never share an id.
- [ ] The `graphe.toml` section name decided and written in the readers document; a host's existing `java` or `kotlin` section keeps working, or the change is said in the README.
- [ ] libsignal and protobuf, at their pinned commits, build with no dangling link; the Java and Kotlin `check` coverage before and after (the new ambiguous names included) and three queries compared with grep, noted in this ticket's comments.
- [ ] ADR 0003 amended; the readers document's Java and Kotlin sections, the README's rows and the BACKLOG.md entry updated.
- [ ] The tests pass.

## Blocked by

None (can start immediately).

## Comments
