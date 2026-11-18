# The sample hosts

Public repositories on which the readers are measured (T-0030): each pinned to a commit, so that any measure can be replayed. They are cloned outside this repository, shallow; they are measures, not automated tests. The README's "Tested on" table sums them up.

To replay a measure, clone at the pinned commit, then build:

```powershell
git init <host>; cd <host>
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
