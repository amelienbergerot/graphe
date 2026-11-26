Status: open
Type: grilling
Part of: T-0048
Created: 2026-11-26

# T-0052: Python and the dependency pins

## Question

`requires-python = "==3.14.*"` and every dependency at an exact version, so that Grid Zero's layout fixture and its communities stay put. For a stranger's environment: ranges in `pyproject.toml`, exact versions only in `uv.lock` and the tests? Which Python versions are promised (3.13? 3.15 once scipy exists for it)? What does a user lose if the layout or the communities differ by a version?
