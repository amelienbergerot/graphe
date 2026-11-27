Status: closed
Part of: T-0071
Blocked by: T-0080
Created: 2026-11-27

# T-0081: A call to an overridden declaration is linked to it

## What to build

A call to an abstract method, or to a Swift protocol's requirement, is ambiguous between its implementations and linked to none: `input.pushLimit(n)` (407 calls) between `ArrayDecoder.pushLimit` and `StreamDecoder.pushLimit` on protobuf, `nativeHandle.const()` and `convertReturn` on libsignal (BACKLOG.md's Java and Swift entries).

Abstract methods, interface methods and Swift protocol requirements become nodes. An implementation gets an `overrides` link to the declaration it implements, found through its class's base list. When every candidate of an ambiguous call overrides one declaration, the call is linked, sure, to that declaration. A call is never linked to all its candidates (ADR 0003's option set aside). The new node kinds and the `overrides` relation change the graph's shape (CHANGELOG.md, **Contract**).

## Acceptance criteria

- [x] On the Java sample host, a call to an abstract method two classes implement is linked to the abstract method; `explain` on an implementation leads to it through `overrides`.
- [x] On the Swift sample host, a call to a protocol requirement likewise.
- [x] Candidates that do not share one declaration leave the call unattributed.
- [x] ADR 0003's amendment (T-0080) covers this rule.
- [x] Measured on protobuf (`pushLimit`) and libsignal (Swift): calls linked before and after, 0 dangling; BACKLOG.md's entries updated.
- [x] CHANGELOG.md notes the new kinds and relation under **Contract**.

## Blocked by

- T-0080 (the same linking rule, the same amendment).

## Comments

- 2026-11-27: done. Java's method without a body (abstract, an interface's; not a `native` one) and Swift's protocol `func` requirement are `@abstract`, an `abstract` node `C.m` whose id is `<file>_abstract_<name>`, so that a method's id never moves. A base list is `@base` (Java's `extends`, `implements`, an interface's `extends`; Swift's `: P` on a type, a protocol or an extension, its heir the extended type; Kotlin's supertypes, so a Kotlin class implementing a Java interface overrides it). A method `overrides` the declaration of its name in its class or a direct base, by the bare names. The links are `INFERRED`, not sure as the ticket said: ADR 0003's amendment and the user's decision in e072ad4 (by name, no import read). A declaration settles a tie only: a single concrete candidate is linked as before, a declaration beside it or not (an interface with one implementation, a functional interface named like an unrelated method), so no link moves; several that all override one declaration, or none and one declaration, go to it. Snapshots: only links added (`s.area()`, `describe`'s `area()`, `Board.place`'s `s.area()` to `Shape.area`, Swift's `shape.draw()` to `Drawable.draw`, through `struct C: P` and `extension Label: Drawable`), `s.perimeter()` still ambiguous (`Fence.perimeter`). protobuf: Java call sites linked 20214 -> 24016 (`pushLimit` 420, `writeUInt32NoTag` 688), 4148 `abstract` nodes, 1334 `overrides`; libsignal: Swift 2348 -> 3509 (`const` 475, `emptyFfiReturn` 164), Java 2093 -> 2097; none lost or moved, 0 dangling on both. Left (BACKLOG.md): libsignal's `toOpaque` (two protocols require it) and `convertReturn` (a test helper defines one without conforming); the direct bases only, and no declarations in C#, Kotlin, Rust, Go and PHP (`docs/readers.md`).
- 2026-11-27: review. A class's bases are found by its whole name: two nested `ListenerBridge`s of libsignal each overrode both listeners (protobuf's `Builder`s alike: `overrides` 1593 -> 1334); a Kotlin anonymous object's supertype is no base of the class that holds it. `callers` of a method lists the callers of the declarations it overrides, marked `?`: `callers Circle.area` said "nothing calls it" once its calls went to `Shape.area`; `affected` likewise. Left, a `shortcut:`: by the name, not the signature, so a concrete `f()` beside an `abstract f(int)` of its class overrides it. protobuf: Java call sites linked 20214 -> 24016; libsignal unchanged (Swift 2348 -> 3509); none lost or moved, 0 dangling. The docs that said C#'s and PHP's bodiless methods are none "as Java's" corrected; GLOSSARY.md has **Declaration**.
