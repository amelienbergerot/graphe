Status: claimed
Type: task
Part of: T-0048
Blocked by: T-0050, T-0056
Created: 2026-11-26

# T-0054: The tests on the three OS

## Question

First, the history rewrite T-0056 decided: the author alone, to the GitHub noreply address (`git filter-repo --email-callback`), the 5 commit hashes cited in files replaced from its commit map, `tests/layout_01a698e.json` renamed after its new hash, a local `git config user.email` noreply, a force-push to both remotes. Then set up a CI (GitHub Actions, on `github.com/amelienbergerot/graphe`, still private: the user makes it public when the effort is done) that runs the tests and `graphe build` on a sample host on Windows, macOS and Linux, and record what fails. The matrix is T-0052's: the locked versions with 3.13 and the newest Python on each OS, plus one Linux job at the newest versions the ranges allow, the layout fixture skipped. The licence first (T-0050), the rewrite before any push the CI needs. Resolved when the CI runs; the answer lists the failures found, which later tickets depend on.

## Comments

- 2026-11-26, the steps (agreed with the user; ticked as done):
  - [x] mirror backup in `E:\dev\graphe-backup-2026-11-26.git`
  - [x] the agent's worktree and its merged branch removed
  - [x] filter-repo: author and committer to the noreply address; remotes put back; only noreply addresses left
  - [x] the cited hashes replaced from the commit map; the fixture renamed; pytest passes locally
  - [x] the CI workflow (locked 3.14 on the three OS; `graphe build` on graphe itself)
  - [ ] force-push to the Freebox and GitHub
  - [ ] the run read; the failures per OS under `## Answer`
