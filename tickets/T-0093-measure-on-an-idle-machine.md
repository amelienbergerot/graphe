Status: ready-for-agent
Created: 2026-11-27

# T-0093: The build's times measured again on an idle machine

## What to build

T-0088's times were taken on a machine at about 85% CPU load (another program running): about 2.5 times the idle times of T-0087, and with few free cores the pool's gain is understated and its cost overstated. So the README's "Tested on" table still shows T-0087's build times (Django 35.8 s, libsignal 9.1 s, protobuf 30.3 s), from before the readers ran at once, and `PARALLEL_FILES` (250, `src/graphe/cli.py`) may be too high.

Before measuring, check the machine is idle: the CPU load under 20% for a minute (`(Get-CimInstance Win32_Processor).LoadPercentage`, sampled), no build of another session running. If it is not, stop and say so: do not measure under load.

Then, the old code (`73428fa`, before T-0088) and the current one alternated, medians of three, warm (one build each beforehand):

- the build on Django, libsignal and protobuf (gitea too if cloned);
- the threshold again: hosts of k Rust and k Java files taken from libsignal (the first k of each, sorted), k = 100, 150, 200, 250, 300, with the pool forced on (`PARALLEL_FILES = 0`) and off; the smallest k where the pool wins sets `PARALLEL_FILES`, counted beside the largest reader as today;
- the pool's cost on a host of 4 files (the `python` and `go` fixtures together), pool forced on and off.

## Acceptance criteria

- [ ] The load checked before measuring, and said in the closing comment.
- [ ] The README's "Tested on" table and docs/sample-hosts.md with the idle times.
- [ ] `PARALLEL_FILES` and its `shortcut:` comment set from the measured threshold, ADR 0005's figures updated; the tests pass.
- [ ] CHANGELOG.md, if the threshold changes.

## Comments
