Status: closed
Type: task
Part of: T-0030
Created: 2026-11-19
Blocked by: T-0031

# T-0036: Ruby on protobuf

## What to build

A Ruby host gets a graph with no configuration: `explain`, `callers`, `path` and `search` answer on its functions, methods (`Class.method`) and types, with the tickets that cite them, through the generic reader of T-0031 (ADR 0003). The upstream `tags.scm` takes a variable for a call: our queries capture explicit calls only (`b()`, `x.c`, `c arg`), and a bare `b`, which may be a variable, is a `shortcut:` in the readers document. Proven on the sample host `protocolbuffers/protobuf`.

## Acceptance criteria

- [x] The readers' registry has a `ruby` entry; its `Language` is data only; its grammar is pinned in the main dependencies.
- [x] Its queries are ours, written from the grammar's `tags.scm` in the capture convention of T-0031, and tested at the internal seam `read(language, file, source)` on a snippet: definitions, `Class.method`, calls with their owner.
- [x] A local variable is not a call, tested; the bare-name limit noted as a `shortcut:`.
- [x] `protocolbuffers/protobuf`, at a pinned commit (added to the sample hosts document if no ticket pinned it yet), builds with no dangling link; its Ruby `check` coverage, its build time and three `explain` or `callers` queries compared with grep are noted in this ticket's comments.
- [x] The common method names are tuned from `check`'s most frequent Ruby names by name.
- [x] The readers document has Ruby's section (suffixes, grammar and version, nodes, links and confidence, quirks, `shortcut:` limits, sample host); the README's "Tested on" table has `protocolbuffers/protobuf`'s row, or its Ruby column if the row exists, measures only.
- [x] The existing hosts checked for Ruby files: noted, kept or excluded; the existing readers' nodes and links unchanged.
- [x] What the generic reader misses on `protocolbuffers/protobuf` is in BACKLOG.md, naming the host.
- [x] The tests pass.

## Blocked by

T-0031.

## Comments

- **The entry** (2026-11-19): `ruby` in `READERS`, `RUBY` data only in `graphe_generic.py`, `tree-sitter-ruby` 0.23.1 pinned. Its `tags.scm` takes a bare identifier for a call under `#is-not? local`, which py-tree-sitter does not apply: `v = 1; v` gives two calls `v`. The query is ours: `b()` and `c arg` are `@call`, `x.c`, `self.c`, `x&.c`, `A::B.c` are `@send`; `C.new` and a superclass are `references` by the last name. Classes and modules (a module holds its `def self.m`), and `X.class_eval do`, which reopens `X` (`well_known_types.rb`: `Any.pack` rather than `Protobuf.pack`); `def m` and `def self.m` are `C.m`; `class << self` is no class. Tested at `read()` on a snippet; a local variable is no call, tested; a bare call missed with it, a `shortcut:` in Ruby's section.
- **protobuf** (`e08e1e7`, 3795 files, 54 `.rb`): 65550 nodes, 104359 links, 0 dangling, every `.rb` parses (neither `tolerant` nor `erased`). Ruby: 808 nodes (54 files, 150 classes, 596 methods, 8 functions). Build 62.0 / 62.7 / 71.3 s (warm; 67.1 s without Ruby the same session, T-0035's 65.0 s): no slower measurably; the README's row takes 62.7 s.
- **Coverage** (`graphe check`, ruby, 7368 sites): `common` empty first: `external` 4891, `ambiguous` 1728, `ours?` 749. The most frequent sends by name: `new` (892, `C.new`, 9 `def self.new` in ffi) and `each` (38), ambiguous: taken. The most frequent linked by name, `push` (43), `pop` (28), `first` (24), `delete` (20), `last`, `to_a`, `values`, are protobuf's `RepeatedField` and `Map` in their tests (`m.repeated_int32.push`), which mirror `Array` and `Hash`: left out. The others guessed (`Object`'s, the conversions, `Enumerable`'s, `Array`'s, `Hash`'s, `String`'s, `IO`'s). With them: `external` 4891, `common` 1117, `ours?` 738, `ambiguous` 622. The guesses cut 11 links that were protobuf's (`empty?` 4, `keys` 4 on a `Map`, `eql?` 2, `merge` 1): the list's price. `external`: minitest's (`assert_equal` 685), `raise` 167, the fields read through `method_missing` (`m.repeated_string` 171), FFI's `attach_function` 124, `require` 123.
- **Three queries against grep** (bytes of the answer; grep over the `.rb` files):
  - `callers ruby/lib/google/protobuf/ffi/descriptor_pool.rb::DescriptorPool.generated_pool`: 26 callers, 1425 bytes; grep `generated_pool`: 42 lines in 13 files, 6390 bytes. `callers DescriptorPool.generated_pool` asks to pick: C++ defines it too (`descriptor.cc`).
  - `explain convert_upb_to_ruby`: 18 callers by name, 1436 bytes; grep `convert_upb_to_ruby(`: 17 lines in 4 files, 2230 bytes.
  - `explain Any.pack`: 5 callers by name, 597 bytes; grep `.pack(`: 10 lines in 4 files, 857 bytes. `def self.pack` and `def pack` are one method.
- **The existing hosts**: Grid Zero, dpe, 4cast, cadastre-poc, the tool itself, gitea, libsignal and Django carry no `.rb`: no contribution. Grid Zero's reference test (`graphe_reference.py comparer`): identical.
- **protobuf's other readers, a cross-check** (the graph without Ruby against this one): their nodes identical (64742), no link lost; 1255 links gained, Ruby's, and one `names` link (`docs/upb/wrapping-upb.md` naming `method_missing`).
- **What it misses** (BACKLOG.md): the message class built by `Class.new(..) do` (its 41 methods `Descriptor`'s, `encode` and `decode` ambiguous), the fields read through `method_missing`; a bare call (at least 17 to protobuf's methods), a class reopened in several files (12 names). Said in Ruby's section: `attr_*`, `alias`, `define_method` are no definitions; `include M` is a call.
- **The documents**: Ruby's section in `docs/readers.md` (and a Ruby `module` among the `@class`), protobuf in `docs/sample-hosts.md`, protobuf's README row, `docs/contribution.md`, `--help` and the skill name the `ruby` reader. The `graphe` tool reinstalled (`uv tool install -e`), its environment now holding the grammar.
- **Not checked**: Linux and macOS wheels of the grammar; protobuf's Objective-C (no ticket).
