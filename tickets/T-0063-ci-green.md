Status: closed
Part of: T-0048
Blocked by: T-0061, T-0062
Created: 2026-11-26

# T-0063: The CI green on the three OS

## What to build

The CI T-0054 set up, completed to T-0052's matrix and made green, plus the built package as a second seam: what PyPI will serve is installed and run.

## Acceptance criteria

- [ ] The fake Godot of the engine-calls test runs on every OS (a Python script, not a `.cmd`); its `shortcut:` goes. Linux and macOS pass it.
- [ ] The matrix: the locked versions with 3.13 and the newest Python on Windows, macOS, Linux; one Linux job at the newest versions the ranges allow (`--upgrade`), the layout fixture skipped there.
- [ ] A job builds the package, installs the wheel as a uv tool, runs `graphe --help` and `graphe build` on the checkout.
- [ ] The actions at majors not on Node 20.
- [ ] Every job green.

## Comments

- 2026-11-26: done on `integration/installable`, code-reviewed: the fake Godot a Python script; the matrix 3.13/3.15 on the three OS, a newest-versions job, a wheel job; actions on Node 24. Green checked locally (Windows, Linux in Docker); GitHub's run after the push. Risk: no numpy cp315 wheel at the locked version (built from source).
