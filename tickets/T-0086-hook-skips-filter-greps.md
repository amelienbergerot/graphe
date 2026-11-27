Status: closed
Part of: T-0071
Created: 2026-11-27

# T-0086: The hook skips a grep that filters a pipe

## What to build

The hook (T-0077) hints on the first grep or rg of a command, even one that filters another command's output: `ls -la ~/.local/bin/ | grep graphe` got "`graphe` is in the code graph" twice in the session that built T-0084 (2026-11-27). Such a grep searches no code.

A grep or rg right after a pipe (`|`, `|&`) is skipped; the next grep of the command, if any, is read instead. `||` is no pipe.

## Acceptance criteria

- [x] `ls | grep aider` and `git log | rg aider`: no output.
- [x] `grep -rn aider . | head` and `false || grep -rn aider .`: the line, as before.
- [x] `git log | grep x; grep -rn aider .`: the second grep's line.

## Comments

- 2026-11-27: done. `hook._grep_pattern` takes the first grep/rg whose previous word is not `|` or `|&`; `||`, `;` and `&&` end a command, they feed it nothing. Tested on the cases of the criteria (tests/test_host.py).
