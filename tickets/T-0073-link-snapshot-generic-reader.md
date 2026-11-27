Status: closed
Part of: T-0071
Blocked by: T-0072
Created: 2026-11-27

# T-0073: A snapshot of the links, for the generic reader's languages

## What to build

T-0072's mechanism, extended to every language of the generic reader: Go, Rust, Java and Kotlin (one family), C and C++ (one family), C#, Ruby, Swift. One small sample host per language or family, with its committed snapshot.

Each host holds what T-0080 and T-0081 will change, so that their diffs show it: a call linked by name, an ambiguous one, a common name on a receiver, a qualified call (`T::f()` in Rust, `C.f()` in Java and Kotlin), a call to an abstract method (Java) and to a protocol's requirement (Swift).

## Acceptance criteria

- [x] Each language or family of the generic reader has a sample host and a committed snapshot, and the test passes on them.
- [x] The Rust, Java/Kotlin and Swift hosts hold the qualified, abstract and protocol calls named above, unattributed today.
- [x] The script of T-0072 rewrites these snapshots too.

## Blocked by

- T-0072

## Comments

- 2026-11-27: seven sample hosts in `tests/fixtures/` (go, rust, jvm with Java and Kotlin, c with C and C++, csharp, ruby, swift), each with its `.links` snapshot; `tests/snapshots.py` takes every folder, so it rewrites them unchanged. Each host holds a call linked by name, an ambiguous send, a common name on a receiver (`c.Close`, `p.len`, `q.getName`, `c.size`, `c.ToString`, `c.to_s`, `c.count`). Unattributed today, for T-0080: Rust's `Point::new` and `Line::new` (common), `Point::length` (ambiguous), `Vec::new` (no host class); Java's `Circle.create` (ambiguous), `Square.of` (common); Kotlin's `Board.create` (ambiguous with the Java ones). For T-0081: Java's and Kotlin's `s.area()` (abstract `Shape.area`), C#'s `s.Area()` (interface), Swift's `shape.draw()` (protocol `Drawable`). 112 tests pass.
