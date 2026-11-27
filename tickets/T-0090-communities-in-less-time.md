Status: ready-for-agent
Created: 2026-11-27

# T-0090: The communities in less time

## What to build

Since T-0088 the readers run at once, and what follows them is serial: the communities are now its largest part. Measured 2026-11-27, the build's own process timed by phase, on a machine at about 85% CPU load (so the times are about 2.5 times the idle ones, the proportions kept):

- protobuf: `communities()` 11.6 s of a 53.5 s build (76741 nodes, 122860 links, 2439 files, 873 communities); `core.enrich` 11.1 s (T-0091), REPORT.md 2.6 s, `_sorted` 1.9 s, `_insert` 1.6 s.
- libsignal: `communities()` 3.9 s of 16.6 s (22804 nodes, 1517 files, 345 communities).
- Django: not timed by phase; 49936 nodes, 3059 files, 909 communities.

A profile of protobuf's build (cProfile, the main process) puts nearly all of `communities()` in networkx's `louvain_communities` (`louvain_partitions`, `_one_level`), with `modularity()` computed at each level a fifth of it.

The communities feed `graphe.json` (each node's `community`), REPORT.md, `graphe view`'s layout and `explain`'s `community:` line. Nodes and links stay exactly as they are; only the partition may change, and only within the rule below.

Options, each to measure on the three hosts before choosing:

1. **Louvain on the files' graph.** The nodes collapsed into their file (a link between two files weighs the sum of its links' weights), Louvain on 2439 nodes instead of about 77000, each node taking its file's community. A community then never splits a file; today a community is already named after its most frequent file.
2. **Louvain's own knobs**: `threshold` (the gain of modularity under which a level stops, 1e-7 by default) and `max_level`.
3. Whatever the profile shows next (the building of the undirected graph, the naming), if it weighs.

No new dependency (a faster Louvain backend is out of scope).

## Rule for the partition

On each of libsignal, protobuf and Django, the modularity of the new partition, computed with `nx.community.modularity` on today's weighted undirected graph (the one `communities()` builds), is within 0.01 of today's. Among the options that meet it, take the largest cut of time. If none does, change nothing and say so in the closing comment, with the measures.

## Acceptance criteria

- [ ] The time of `communities()` and of the build, before and after, on libsignal, protobuf and Django (medians of three alternated runs; say the machine's load), in the closing comment and docs/sample-hosts.md.
- [ ] The modularity, the count of communities and the ten largest communities' names, before and after, on the three hosts, in the closing comment.
- [ ] `graphe.json`'s nodes (but `community`) and links identical on the three hosts; the fixtures' link snapshots unchanged.
- [ ] The communities stay deterministic (two builds, the same partition), as the test of Grid Zero checks today.
- [ ] CHANGELOG.md: the communities' change, if any.

## Comments
