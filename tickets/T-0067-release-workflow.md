Status: ready-for-agent
Part of: T-0048
Blocked by: T-0063, T-0064
Created: 2026-11-26

# T-0067: The release workflow and the changelog

## What to build

A release is a tag the author pushes (T-0058): a workflow builds the package, uploads `graphe-code` to PyPI by Trusted Publishing, and creates the GitHub release; a contract change is announced in a changelog.

## Acceptance criteria

- [ ] On a `vX.Y.Z` tag: build, upload by Trusted Publishing (no stored token), a GitHub release linking to its changelog entry.
- [ ] The workflow fails, before uploading, when the tag, the package's version and the plugin's version differ.
- [ ] A changelog at the root with a `0.1.0` entry; its header says a release changing `contribute(project)`, `Project` or the shape of the nodes and links carries a **Contract** section and is at least a minor bump in `0.x`.
- [ ] The release steps written for the author in Developing graphe (set both versions, the changelog entry, push the tag); the grammar caps are not a release step.
