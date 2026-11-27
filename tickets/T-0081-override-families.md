Status: ready-for-agent
Part of: T-0071
Blocked by: T-0080
Created: 2026-11-27

# T-0081: A call to an overridden declaration is linked to it

## What to build

A call to an abstract method, or to a Swift protocol's requirement, is ambiguous between its implementations and linked to none: `input.pushLimit(n)` (407 calls) between `ArrayDecoder.pushLimit` and `StreamDecoder.pushLimit` on protobuf, `nativeHandle.const()` and `convertReturn` on libsignal (BACKLOG.md's Java and Swift entries).

Abstract methods, interface methods and Swift protocol requirements become nodes. An implementation gets an `overrides` link to the declaration it implements, found through its class's base list. When every candidate of an ambiguous call overrides one declaration, the call is linked, sure, to that declaration. A call is never linked to all its candidates (ADR 0003's option set aside). The new node kinds and the `overrides` relation change the graph's shape (CHANGELOG.md, **Contract**).

## Acceptance criteria

- [ ] On the Java sample host, a call to an abstract method two classes implement is linked to the abstract method; `explain` on an implementation leads to it through `overrides`.
- [ ] On the Swift sample host, a call to a protocol requirement likewise.
- [ ] Candidates that do not share one declaration leave the call unattributed.
- [ ] ADR 0003's amendment (T-0080) covers this rule.
- [ ] Measured on protobuf (`pushLimit`) and libsignal (Swift): calls linked before and after, 0 dangling; BACKLOG.md's entries updated.
- [ ] CHANGELOG.md notes the new kinds and relation under **Contract**.

## Blocked by

- T-0080 (the same linking rule, the same amendment).
