Status: closed
Type: bug
Created: 2026-11-27

# T-0083: A body's extent reads its strings as code

## What to fix

`core.extent` follows a signature over several lines by counting the `(` and `)` from the first line on, strings included. `tests/test_host.py::GRID_ZERO_TOML`, a constant whose first line holds a regex (`\(\s*"((?:[^"\\]|\\.)*)"`, three `(` for two `)`), never closes its signature: its extent runs to the end of the file (405-918), and `graphe affected` lists it as touched by any line added below it (BACKLOG.md, found during T-0075).

A string over several lines (`'''`, `"""`) is read as code too: an unindented line inside it ends the block (a docstring's, a constant's).

The parentheses inside a string do not count. The lines of a string over several lines belong to the block, whatever their indentation. A signature never continues with a line at its own indentation, unless that line starts with a closing bracket.

## Acceptance criteria

- [x] A constant whose first line holds unbalanced parentheses in a string ends with its statement.
- [x] A constant holding a triple-quoted string over several lines, with unindented lines, ends with the closing quotes.
- [x] A function whose docstring holds an unindented line ends with its body.
- [x] `GRID_ZERO_TOML` reads 405-419.

## Blocked by

None.

## Comments

- 2026-11-27: done. `core._scan` counts a line's parentheses outside its strings and carries a triple quote left open; `core.extent` keeps the lines of an open string in the block, and ends a signature at a line back at its indentation unless it starts with a closing bracket. Tests in `tests/test_graphe.py` (`test_an_extent_reads_strings_as_strings`). On this repository, the extents that changed all end where their statement does now: the query constants of `generic.py` and the page of `cli.py` (triple-quoted strings), `godot.CALLS_BY_NAME` (45, was 386) and `generic.C` (517, was the end of the file), `GRID_ZERO_TOML` (405-419). The link snapshots do not change. shortcut kept: JavaScript's template literals and PHP's heredocs over several lines are still read as code.
