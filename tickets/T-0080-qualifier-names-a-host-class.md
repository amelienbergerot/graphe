Status: closed
Part of: T-0071
Blocked by: T-0073, T-0078, T-0079
Created: 2026-11-27

# T-0080: A qualifier that names a class of the host narrows the candidates

## What to build

`T::f()` in Rust and `C.f()` in Java or Kotlin name the class, yet the generic reader links the call only when `f` has a single definition in the whole language, and never when `f` is a common name: `DeviceId::new` (183 calls) and `KeyPair::generate` (118) stay unattributed on libsignal (BACKLOG.md, "A Rust `Type::f()` path is not linked when `f` is a common name.").

When a call's qualifier names a class of the host, its candidates are only the methods `f` of the classes named `T` in the same language or family, whatever file holds them (a Rust `impl` apart from its `struct`). It is linked, sure, only when one candidate is left; otherwise it is unattributed as before. A common name qualified by a host class is no longer skipped.

ADR 0003 gets one amendment, written with this ticket, for this rule and T-0081's: what "by its name alone" now admits, and why a link stays exact.

## Acceptance criteria

- [x] On the Rust sample host, `T::new()` is linked to `T.new` when `T` is a class of the host, `new` a common name included.
- [x] On the Java/Kotlin sample host, `C.f()` likewise.
- [x] A qualifier naming a class with two methods `f`, or no class of the host, leaves the call unattributed.
- [x] The snapshots' diff shows only the new links, reviewed in the commit.
- [x] Measured on libsignal and protobuf (`docs/sample-hosts.md`): calls linked before and after, 0 dangling; the README's figures and BACKLOG.md's entry updated.
- [x] ADR 0003's amendment is written.

## Blocked by

- T-0073 (the Rust and Java/Kotlin snapshots).
- T-0078 (both edit the README).
- T-0079 (both edit the generic reader).

## Comments

- 2026-11-27: done. An optional `@qualifier` on a send (Rust's `scoped_identifier` path, Java's `object`, Kotlin's `navigation_expression` head) gives `Use.qualifier`, the path's last name (generic arguments dropped; `f().g()` has none). `contribute` narrows a send whose qualifier names a class the host declares to the methods `f` of the classes so named: one, linked `EXTRACTED` (site `ours`); several, `ambiguous`; none, the name alone as before. A Rust `impl` is `@extension`: a type the host only implements a trait for (`impl From<X> for HashMap`) is not its class, found in review (libsignal's `HashMap::from([..])`, 30 sites). Snapshots: Rust `Point::new`, `Point::length` (its `impl` in `measure.rs`), `origin -> Point::new` new, `Point::origin` turned sure, `Line::new` still ambiguous (two `Line`); JVM `Circle.create`, `Square.of`, `Board.create` new, both `Circle.unit` turned sure. libsignal: Rust `calls` 5524 -> 7854, Java 1259 -> 1451, Kotlin 1371 -> 1478, 991 turned sure; protobuf: Java 10066 -> 13069, Rust 344 -> 449, Kotlin 8 -> 12, 1574 turned sure; none lost, 0 dangling, the sites unchanged in number. Left open (BACKLOG.md): a Rust path's modules (`KeyPair::generate` between 6 modules, std's `Duration` taken for libsignal's, about 42 sites), `Self::f()`.
- 2026-11-27: by name, the user's decision. The links T-0080 makes are `INFERRED` (site `ours?`), not sure as the ticket said: the class is found by its name, no import read, and at least 52 of libsignal's (std's `Duration`, the `uuid` crate's `Uuid`) are wrong; `?` tells an agent to check them. The figures above that say "turned sure" no longer hold: those links stay by name.
