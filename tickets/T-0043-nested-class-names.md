Status: ready-for-agent
Type: task
Created: 2026-11-19
Blocked by: T-0039, T-0040, T-0041, T-0042

# T-0043: A nested class is named `Outer.Inner`

## What to build

A class declared inside another is named `Outer.Inner`, and its methods `Outer.Inner.m`, in every language of the generic reader, so that the nested classes of one file no longer merge: on protobuf, each generated Java message's `Builder` (59 declarations sharing a name in their file) and each C# message's `Types` (18 files) are one class per file today. Written once, in the generic reader's naming, not per language (ADR 0003). An anonymous class's methods stay their enclosing class's: said as a `shortcut:`. Last of its batch, so that the sample hosts are measured once after the other changes. BACKLOG.md: "Java's nested and anonymous classes lose their outer name".

## Acceptance criteria

- [ ] A test at `read(language, file, source)` in Java and C#: a nested class is `Outer.Inner`, its method `Outer.Inner.m`, its call owned by it; a top-level class unchanged.
- [ ] A test at `contribute(project)`: two nested `Builder` of one file are two nodes; a call to `build` that both define stays ambiguous, linked to neither.
- [ ] `explain Outer.Inner.m` designates the node; `explain Inner.m` designates it too, or asks to pick, as an ambiguous name does today.
- [ ] Every language checked for its nesting (Java, C#, Kotlin, Swift, C++, Rust's `impl` in a module, Ruby's `class` in a `module`): what changes is noted in each section of the readers document.
- [ ] protobuf, libsignal and gitea build with no dangling link; their `check` coverage before and after, noted in this ticket's comments; the README's rows updated if a measure moves.
- [ ] Grid Zero's reference test identical; dpe, 4cast and the tool itself give the same graph.
- [ ] The BACKLOG.md entry updated.
- [ ] The tests pass.

## Blocked by

T-0039, T-0040, T-0041, T-0042: the sample hosts are measured once, after them.

## Comments
