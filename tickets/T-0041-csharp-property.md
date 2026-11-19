Status: closed
Type: task
Created: 2026-11-19

# T-0041: A C# property is the method `C.P`

## What to build

A C# property (`get`, `set`, `=> expr`) is a definition, the method `C.P`, so that the calls in its accessors belong to it and not to its class: `explain Person.Name` answers on protobuf, and `callers ProtoPreconditions.CheckNotNull` lists the setters rather than the generated classes (`Person:56`). A query change only (ADR 0003), as Swift's computed properties are methods since T-0037. The property has no caller: it is used without a call. BACKLOG.md: "A C# property is no definition".

## Acceptance criteria

- [x] C#'s query captures a property as a `@method`; a test at `read(language, file, source)`: a property with `get`/`set`, and one with `=> expr`, are `C.P`, their calls owned by them; an auto-property (`{ get; set; }`) is a node with no call.
- [x] protobuf, at its pinned commit, builds with no dangling link; its C# `check` coverage before and after, `explain Person.Name` and `callers ProtoPreconditions.CheckNotNull` before and after, noted in this ticket's comments.
- [x] C#'s section of the readers document (nodes, limits) and the BACKLOG.md entry updated.
- [x] The tests pass.

## Blocked by

None (can start immediately).

## Comments

- **The change** (2026-11-19): `(property_declaration name: (identifier) @name) @method` in `CSHARP_QUERY`, data only (ADR 0003). Tested at `read()`: a property with `get`/`set` and one with `=> expr` or `get => expr` are `C.P`, their calls their own; an auto-property is a node with no call, its initial value's call (`{ get; } = Init()`) its own. An interface's or abstract property, written as an auto-property but without a body, is no node (docs/readers.md, "Adding a language": definitions with a body only): the capture is limited to a class's, struct's or record's body, and a predicate leaves out `abstract`. An indexer and an event's accessors are not captured (a `shortcut:` with the operators).
- **protobuf** (`e08e1e7`): 65716 -> 69457 nodes (+3741 methods, the properties of its 224 `.cs` files; none lost), 104565 -> 108450 links, 0 dangling. A link is a pair that can carry several relations: 4013 gained (3741 `contains`; 259 calls and references from the properties, which took 117 from their classes, a class's one link per target now one per property; 13 to a delegate property invoked, `FieldCodec.ValueWriter` and its kin), 128 lost, holding 130 relations (117 the classes', 13 the methods' made ambiguous: `JsonToken.Name` 9, `SegmentedBufferHelper.IsAtEnd` 2, and `Empty.Empty` 2 wrong ones).
- **Coverage** (`graphe check`, csharp, 35466 sites): `ambiguous` 19463 -> 19499, `ours?` 5778 -> 5758, `common` 5092 -> 5230, `external` 5133 -> 4979. Every site that moved, read with and without the line:
  - `external` -> `common`, 138: NUnit's `Assert.False` 72, `Assert.True` 38, `Assert.Null` 27, `Assert.IsEmpty` 1, which a property's name linked to `JsonToken.False`, `ByteString.IsEmpty`... (first `ours?`): the four names added to `CSHARP.common`, at no cost (protobuf defines no other callable so named).
  - `external` -> `ours?`, 14: a delegate property invoked (`codec.ValueWriter(..)` 6, `ValueSizeCalculator` 4, `ValueReader` 2, `ValueMerger`, `FieldMerger`): right.
  - `ours?` -> `ambiguous`, 34: a property sharing a method's name, `JsonToken.Name` 27 and `SegmentedBufferHelper.IsAtEnd` 4, right links lost (the price, a `shortcut:`); `Array.Empty` 2 and `Enumerable.Empty` 1, wrong links to `Empty.Empty` before, a gain.
  - `external` -> `ambiguous`, 2: `thread.Start`, `process.Start`.
- **`explain Person.Name`**: before, "no node for 'Person.Name'"; after, `Addressbook.pb.cs:109-114`, calls `ProtoPreconditions.CheckNotNull`, held by `Person:56`, "+ 27 calls named `Name` the graph could not attribute" (`JsonToken.Name`'s, the price above). 60 -> 548 bytes.
- **`callers ProtoPreconditions.CheckNotNull`**: 138 -> 270 callers by name, 24410 -> 25557 bytes; the setters (`Person.Name:109`, `Person.Email:138`, `PhoneNumber.Number:464`...) where generated classes were (`Person:56`, 98 of the 138). 3 classes left: `Duration` and `Timestamp` (an `operator +`, `operator -`) and `MapField` (an indexer `this[object key]`), no definitions by the `shortcut:`.
- **The README's protobuf row**: `callers ByteString.copyFromUtf8` (Java) unchanged, 124 callers, 9253 bytes. Build time not remeasured in alternation (single warm runs), the row's 62.7 s left as it is, as T-0039 and T-0040 did.
- **The documents**: C#'s section in `docs/readers.md` (the nodes, a property read no call, NUnit's names, the quirk, the two `shortcut:`), the BACKLOG.md entry in Settled, protobuf in `docs/sample-hosts.md`.
- **Not checked**: the other hosts: none carries a `.cs` (T-0035), so their graphs are unchanged by construction.
- **The review** (2026-11-19, standards and spec): every criterion met, the figures re-checked against the raw outputs. Fixed: an interface's or abstract property was a node (8 of protobuf's 4210 properties; `I.P` but no `I.M`), against "definitions with a body only": no longer captured, tested (no site moves on protobuf, each such name being defined several times already); an event's accessors named in the `shortcut:`; the link figures counted by pair (+3885 = 4013 - 128); "138 generated classes" said 98 of 138; the second `shortcut:` names the wrong links a property's name draws (NUnit's), "callables" said in the docs' words. Left as they are: the prose repeated in the code comment, `docs/readers.md`, BACKLOG.md and this ticket, as each ticket did; the ambiguity a property's name makes kept as a `shortcut:` of C#'s section and no Open entry, as Swift's 26 sites (T-0037); `IsEmpty` among the common names for one send, at no cost.
