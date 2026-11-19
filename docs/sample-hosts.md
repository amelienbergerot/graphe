# The sample hosts

Public repositories on which the readers are measured (T-0030): each pinned to a commit, so that any measure can be replayed. They are cloned outside this repository, shallow; they are measures, not automated tests. The README's "Tested on" table sums them up.

To replay a measure, clone at the pinned commit, then build:

```powershell
git init <host>; cd <host>
git config core.longpaths true   # Windows: gitea's paths reach 190 characters
git remote add origin <URL>
git fetch --depth 1 origin <commit>; git checkout FETCH_HEAD
graphe build; graphe check
```

## Django

- **URL**: https://github.com/django/django
- **Commit**: `9e2e5a31e2ef2e8673d3c2a38d2a391dbf42cf23` (2026-11-17). T-0016 and T-0026 recorded no commit: this one, cloned on 2026-11-19, gives their graph exactly (49936 nodes, 153089 links).
- **Languages**: Python (2943 of its 7104 files), JavaScript (111).
- **`graphe.toml`**: none. `tests/test_runner_apps/tagged/tests_syntax_error.py` does not parse on purpose: skipped (T-0016).
- **Measured by**: T-0016 (the cost and the scale), T-0025 (`explain` says what it misses), T-0026 (the rebuild of a large repository), T-0031 (its row in the README).

## gitea

- **URL**: https://github.com/go-gitea/gitea
- **Commit**: `c376d5d8b126a28781fffb4c8c3fc3b9deab8469` (2026-11-18).
- **Languages**: Go (3199 of its 6431 files), TypeScript (276), JavaScript (3).
- **`graphe.toml`**: none. The Go grammar does not parse 47 files (Go 1.26's `new(expr)`, generic methods): skipped and named at each build (BACKLOG.md).
- **Measured by**: T-0031 (the generic reader, Go).

## libsignal

- **URL**: https://github.com/signalapp/libsignal
- **Commit**: `956e1cab1d68291c92f2fcca3c29ec6c3b367e28` (2026-11-17).
- **Languages**: Rust (612 of its 1852 files), Java (344), Swift (218), TypeScript (176), Kotlin (125).
- **`graphe.toml`**: none. The Rust grammar does not parse 1 file (`dyn 's + FnOnce`): skipped and named at each build (BACKLOG.md).
- **Measured by**: T-0032 (Rust), T-0033 (its Java: 0 dangling, no file skipped), T-0034 (its 2 C headers, `swift/Sources/SignalFfi/*.h`: 544 structs, nothing else changed), T-0037 (Swift: 0 dangling; 10 of its 218 files have an error node, read all the same). The JS reader read it first there: a comment among the names of `import { }` (`node/ts/NativeNice.ts`) made it fail, fixed in T-0032.

## protobuf

- **URL**: https://github.com/protocolbuffers/protobuf
- **Commit**: `e08e1e7efe5b5e0c1a64fa3f9dbfffe400cf5190` (2026-11-18).
- **Languages**: C/C++ (1363 of its 3795 files: 636 `.h`, 576 `.cc`, 143 `.c`, 6 `.hpp`, 2 `.cpp`), Java (293), C# (224), PHP (158), Rust (128), Python (105), Objective-C (85), Ruby (54), Go (4), Swift (3).
- **`graphe.toml`**: none. 11 of its Java files are one generated file, `Proto3GencodeTestProto.java`, as 9 old versions generated it (`compatibility/smoke/v*/`, full and lite): read as they are (BACKLOG.md). Its C/C++ holds two amalgamations of upb (`php/ext/google/protobuf/php-upb.{c,h}`, `ruby/ext/google/protobuf_c/ruby-upb.{c,h}`): read as they are (BACKLOG.md). Its C# tests are copied in `csharp/compatibility_tests/v3.0.0/` (28 of its 224 `.cs` files): read as they are (BACKLOG.md).
- **Measured by**: T-0033 (Java), T-0034 (C/C++: 0 dangling, no file skipped; 765 of its 1363 files have an error node once the macros are erased, read all the same), T-0035 (C#: 0 dangling, no file skipped; 2 of its 224 files have an error node once the `#if` lines are erased, read all the same), T-0036 (Ruby: 0 dangling, every file parses), T-0037 (its 3 Swift files, `objectivec/`: 22 nodes, nothing else changed).
