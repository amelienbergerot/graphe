Status: open
Type: task
Part of: T-0048
Blocked by: T-0050
Created: 2026-11-26

# T-0054: The tests on the three OS

## Question

Set up a CI (GitHub Actions, the public repository) that runs the tests and `graphe build` on a sample host on Windows, macOS and Linux, and record what fails. The matrix is T-0052's: the locked versions with 3.13 and the newest Python on each OS, plus one Linux job at the newest versions the ranges allow, the layout fixture skipped. Needs the repository public, so its licence first. Resolved when the CI runs; the answer lists the failures found, which later tickets depend on.
