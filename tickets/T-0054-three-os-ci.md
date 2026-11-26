Status: resolved
Type: task
Part of: T-0048
Blocked by: T-0050, T-0056
Created: 2026-11-26

# T-0054: The tests on the three OS

## Question

First, the history rewrite T-0056 decided: the author alone, to the GitHub noreply address (`git filter-repo --email-callback`), the 5 commit hashes cited in files replaced from its commit map, `tests/layout_01a698e.json` renamed after its new hash, a local `git config user.email` noreply, a force-push to both remotes. Then set up a CI (GitHub Actions, on `github.com/amelienbergerot/graphe`, still private: the user makes it public when the effort is done) that runs the tests and `graphe build` on a sample host on Windows, macOS and Linux, and record what fails. The matrix is T-0052's: the locked versions with 3.13 and the newest Python on each OS, plus one Linux job at the newest versions the ranges allow, the layout fixture skipped. The licence first (T-0050), the rewrite before any push the CI needs. Resolved when the CI runs; the answer lists the failures found, which later tickets depend on.

## Answer

Done with the user (2026-11-26). What was done:

- **The history rewritten** (T-0056): `git filter-repo --email-callback`, author and committer, to `13414890+amelienbergerot@users.noreply.github.com` (170 addresses, no other left); a mirror backup of the old history in `E:\dev\graphe-backup-2026-11-26.git`, the only copy; the agent's leftover worktree and merged branch removed; `research/distribution-channel` rewritten, not pushed. The cited hashes follow: `7681fac` -> `01a698e` (the fixture now `tests/layout_01a698e.json`), `b3676a0` -> `b6e5847`, `4c0a291` -> `b34b61f`, `9b35560` -> `8cfc450`, `7c10dbb` -> `a0f70a8`. Force-pushed by the user to the Freebox and GitHub (`91541f1`). The user made the GitHub repository public the same day.
- **The CI**: `.github/workflows/ci.yml`, locked versions, Python 3.14 only on the three OS (`requires-python` still pins `==3.14.*`: the 3.13 and newest-versions jobs come with T-0052's ranges, when implemented); the tests, then `graphe build` on graphe itself.

The failures found (run 45864462223, at `91541f1`):

- **Windows**: none; the tests and the build pass.
- **Linux and macOS**: one test, the same, `test_with_the_key_the_engine_calls_are_resolved` (`tests/test_host.py:114`): its fake Godot is a `.cmd`, run only by Windows (its own `shortcut:` said so). A test's fault, not graphe's: the build warns as it should (`… did not give the engine API …: its calls stay unresolved`). The fix: a fake Godot every OS runs (a Python script). The build step was skipped after it; reproduced in Docker on Linux (`python3.14-bookworm`): graphe builds itself, 565 nodes, 1849 links, 0 dangling.
- **Skipped as expected on all three**: the 4 `grid_zero` tests (Grid Zero absent).
- **To act on**: the Node.js 20 deprecation of `actions/checkout@v4` and `astral-sh/setup-uv@v6` (newer majors); no `LICENSE` at the root yet (T-0050) while the repository is public; GitHub may still serve the old commits (the gmail) by SHA until it collects unreachable objects: a purge request to GitHub support.

## Comments

- 2026-11-26, the steps (agreed with the user; ticked as done):
  - [x] mirror backup in `E:\dev\graphe-backup-2026-11-26.git`
  - [x] the agent's worktree and its merged branch removed
  - [x] filter-repo: author and committer to the noreply address; remotes put back; only noreply addresses left
  - [x] the cited hashes replaced from the commit map; the fixture renamed; pytest passes locally
  - [x] the CI workflow (locked 3.14 on the three OS; `graphe build` on graphe itself)
  - [x] force-push to the Freebox and GitHub
  - [x] the run read; the failures per OS under `## Answer`
- 2026-11-26: resolved; the run read from the user's logs (Ubuntu, macOS) and a Docker reproduction.
