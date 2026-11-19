Status: ready-for-agent
Type: task
Created: 2026-11-19

# T-0041: A C# property is the method `C.P`

## What to build

A C# property (`get`, `set`, `=> expr`) is a definition, the method `C.P`, so that the calls in its accessors belong to it and not to its class: `explain Person.Name` answers on protobuf, and `callers ProtoPreconditions.CheckNotNull` lists the setters rather than the generated classes (`Person:56`). A query change only (ADR 0003), as Swift's computed properties are methods since T-0037. The property has no caller: it is used without a call. BACKLOG.md: "A C# property is no definition".

## Acceptance criteria

- [ ] C#'s query captures a property as a `@method`; a test at `read(language, file, source)`: a property with `get`/`set`, and one with `=> expr`, are `C.P`, their calls owned by them; an auto-property (`{ get; set; }`) is a node with no call.
- [ ] protobuf, at its pinned commit, builds with no dangling link; its C# `check` coverage before and after, `explain Person.Name` and `callers ProtoPreconditions.CheckNotNull` before and after, noted in this ticket's comments.
- [ ] C#'s section of the readers document (nodes, limits) and the BACKLOG.md entry updated.
- [ ] The tests pass.

## Blocked by

None (can start immediately).

## Comments
