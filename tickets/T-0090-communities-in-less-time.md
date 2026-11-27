Status: closed
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

- [x] The time of `communities()` and of the build, before and after, on libsignal, protobuf and Django (medians of three alternated runs; say the machine's load), in the closing comment and docs/sample-hosts.md.
- [x] The modularity, the count of communities and the ten largest communities' names, before and after, on the three hosts, in the closing comment.
- [x] `graphe.json`'s nodes (but `community`) and links identical on the three hosts; the fixtures' link snapshots unchanged.
- [x] The communities stay deterministic (two builds, the same partition), as the test of Grid Zero checks today.
- [x] CHANGELOG.md: the communities' change, if any.

## Comments

- 2026-11-27: done. `communities()` folds each node of one neighbour into it, again up the chain (a tree hanging off the graph ends in the node it hangs from), the folded link's weight kept as a self-loop of that node, as Louvain's own levels aggregate; Louvain runs on the folded graph, each node takes the community of the node it was folded into. The separate kinds, `s != t` and the weight `len(locations)`, as before. A node of one neighbour now always shares its community (the new test: a chain off a triangle, which plain Louvain split, and a pair apart).

  **The options**, measured on the graphe.json of each host (Louvain alone, `seed=0`; dQ against today's partition, the modularity on today's weighted undirected graph). The machine at 83 to 90% CPU load throughout (another program running), so the times are about 2.5 times idle ones:

  | option | libsignal | protobuf | Django |
  |---|---|---|---|
  | today | 3.4 s, Q 0.9133 | 11.7 s, Q 0.9132 | 12.0 s, Q 0.7477 |
  | the files' graph (no self-loops) | 0.35 s, dQ -0.025 | | |
  | the files' graph, self-loops | 0.43 s, dQ -0.011 | 0.95 s, dQ -0.039 | 1.2 s, dQ -0.012 |
  | each top-level definition (a class with its methods) | 1.8 s, dQ -0.003 | 4.3 s, dQ -0.018 | 13.5 s, dQ +0.012 |
  | the same, then the leaves | 1.5 s, dQ -0.003 | 3.7 s, dQ -0.017 | 13.7 s, dQ +0.008 |
  | `threshold` 1e-4 / 1e-3 | 3.7 / 3.6 s, dQ 0 | 14.1 / 13.2 s, dQ 0 | 14.8 / 14.2 s, dQ 0 |
  | `max_level` 2 | 3.5 s, dQ -0.047 | 11.4 s, dQ -0.036 | 12.6 s, dQ -0.025 |
  | `max_level` 3 | 3.8 s, dQ -0.002 | 11.8 s, dQ -0.002 | 13.2 s, dQ -0.001 |
  | **the leaves folded** | 3.1 s, dQ +0.001 | 8.4 s, dQ -0.0004 | 13.7 s, dQ +0.007 |
  | the leaves folded, then `max_level` 3 (fold alone in the same run) | 2.87 s (2.85), Q 0.9139 (0.9145) | 8.01 s (7.64), Q 0.9111 (0.9128) | 11.27 s (11.98), Q 0.7545 (0.7547) |

  The "today" row is Louvain alone on each graphe.json, whose node order differs from the build's: its Q is not exactly the built partition's below (libsignal 0.9133 against 0.9135); the rule holds against either. The fold, `max_level 3` and the two together keep the rule on the three hosts; the fold cuts the most. The thresholds cut nothing: Louvain's first level loops full passes until no node moves, with no threshold there, and it is most of the time (`_one_level`, 264445 neighbour scans on libsignal's 22780 nodes); only a smaller graph shortens it. `max_level 3` on top of the fold gains nothing steady (slower on protobuf, equal on libsignal, 6% on Django) for a lower modularity: left out. Nothing was profiled after the change: the undirected graph's building and the naming are in the `communities()` times above. On sparse random graphs (300 nodes, 330 links, 30 seeds) the fold's partition goes from -0.014 to +0.017 against plain Louvain (mean -0.002): Louvain's own spread on small graphs, but the rule is measured on the three hosts only, a `shortcut:` in the code says so. The files' graph loses most on protobuf, where files split across communities (its generated classes, `compatibility/smoke/v*/`). Leiden needs a networkx backend: out of scope. Django gains nothing: 49928 nodes -> 41778, few leaves, 152368 links.

  **`communities()` itself** (the real function, HEAD against the new, alternated, medians of three, on each graphe.json): libsignal 4.38 -> 3.13 s, protobuf 12.12 -> 7.64 s, Django 12.74 -> 13.24 s (no gain, within the load's noise).

  **The build** (`graphe build`, HEAD against the new, alternated, medians of three): libsignal 16.9 -> 14.5 s (load 84%), protobuf 49.4 -> 47.9 s (load 90%), Django 98.0 -> 89.6 s (its runs 129.5, 98.0, 91.9 against 172.5, 89.6, 78.0, the load falling from 90 to 57%: no conclusion on Django). T-0093 measures again on an idle machine.

  **The partitions**, from the built graphe.json (the separate kinds aside):

  - libsignal: Q 0.9135 -> 0.9145, 344 -> 334 communities, the largest 1925 -> 1935 nodes, over 1000 nodes 8 -> 6. The ten largest, before: RegistrationServiceTypes + ChatConnection+Fake (swift), NativeNice + NativeTestingNice (swift), rust/net/infra/src/route/schedule + route, NativeTestingNice + NativeNice (java), rust/bridge/shared/src/protocol + rust/protocol/src/state/session, rust/bridge/shared/testing/src/net/chat + rust/net/chat/src/grpc/accounts, rust/bridge/shared/src/zkgroup + avatar_upload_credential, CompletableFutureTest + UnauthBackupsService, rust/message-backup/src/backup/recipient + serialize, rust/message-backup/src/backup + rust/net/src/svrb. After: RegistrationServiceTypes + ChatConnection+Fake (swift), NativeTestingNice + NativeNice (swift), NativeTestingNice + NativeNice (java), rust/bridge/shared/src/zkgroup + avatar_upload_credential, rust/bridge/shared/testing/src/net/chat + rust/net/chat/src/grpc/accounts, rust/bridge/shared/src/protocol + rust/protocol/src/sealed_sender, rust/net/infra/src/route/schedule + route, CompletableFutureTest + UnauthBackupsService, rust/message-backup/src/backup + backup/recipient, node/ts/NativeNice.
  - protobuf: Q 0.9131 -> 0.9130, 870 -> 855 communities, the largest 8848 -> 8527 nodes, over 1000 nodes 23 -> 23. The ten largest, before: Unittest.pb + Descriptor.pb (csharp), Proto3GencodeTestProto v21.12 + v3.19.0, v3.0.0 + v21.12, src/google/protobuf/descriptor.pb, repeated_ptr_field + generated_message_tctable_lite, Proto3GencodeTestProto v3.0.0 + v25.8, descriptor.pb + descriptor, java Descriptors + Proto3GencodeTestProto v21.12, php EncodeDecodeTest + FileOptions, java CodedInputStream + CodedOutputStream. After: Unittest.pb + Descriptor.pb (csharp), Proto3GencodeTestProto v21.12 + v3.19.0, v3.0.0 + v21.12, descriptor.pb + descriptor.pb, Proto3GencodeTestProto v25.8 + v32.1, repeated_ptr_field + generated_message_tctable_lite, compiler/cpp/message + helpers, java Descriptors + GeneratedMessage, Unittest.pb + TestMessagesProto2.pb (csharp), php EncodeDecodeTest + FileOptions.
  - Django: Q 0.7484 -> 0.7535, 913 -> 911 communities, the largest 4604 -> 4305 nodes, over 1000 nodes 17 -> 17. The ten largest, before: django/db/models/fields/__init__ + expressions, tests/auth_tests/test_forms + django/forms/widgets, tests/admin_views/tests + models, tests/invalid_models_tests/test_models + test_relative_fields, template_tests/syntax_tests/test_if + django/template/defaulttags, tests/queries/tests + tests/expressions/tests, tests/admin_scripts/tests + tests/migrations/test_commands, tests/cache/tests + tests/check_framework/test_security, django/db/models/sql/query + django/db/backends/base/schema, django/core/validators + tests/validators/tests. After: tests/invalid_models_tests/test_models + test_relative_fields, tests/custom_lookups/tests + tests/bulk_create/tests, tests/queries/tests + tests/expressions/tests, tests/admin_views/tests, tests/decorators/tests + tests/generic_views/test_base, tests/modeladmin/test_checks + tests/admin_views/admin, template_tests/syntax_tests/test_if + django/template/defaulttags, tests/admin_scripts/tests + tests/migrations/test_commands, django/db/models/fields/__init__ + django/forms/widgets, django/db/models/sql/query + django/db/backends/base/schema.

  **The graph**: `graphe.json` identical on the three hosts but `community` and `communities` (nodes, links and every other field); REPORT.md differs by the communities' count and sections only. The fixtures' link snapshots unchanged (`test_snapshots`), the layout of T-0017 unchanged (`test_the_layout_keeps_the_positions_of_the_tool_before_t_0016`), Grid Zero's two builds the same partition (`test_the_graph_does_not_change_from_one_build_to_the_next`). 145 tests pass.
