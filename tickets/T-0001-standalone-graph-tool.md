Status: ready-for-agent
Type: spec
Created: 2026-11-17

# The graph, a standalone tool for all my projects

## The problem

The code graph was born in Grid Zero and serves only Grid Zero. The agent that works on 4cast or on dpe has only grep and file reading, whereas the graph locates code with 2 to 12 times fewer tokens. It cannot be taken elsewhere: the folders read, the output, the Godot executable and the game's notions (scenarios, client-server protocol, server commands, online service, moonshot journal) are hard-coded in the readers and in the enrichment. No reader can read JavaScript, TypeScript or Svelte. Finally, what the graph lacks is noted in a file specific to Grid Zero, and the agent learns the tool only through memories specific to Grid Zero.

## The solution

The graph becomes a tool installed once, as a global command (`graphe`), that serves any host project. Run in a repository without any configuration, it reads the files git tracks with the reader of their language and answers the same questions as today: explain, callers, path, search. An optional `graphe.toml` serves to exclude folders, give the path of an external program, set up the documents and declare the local extensions. What holds only for Grid Zero becomes a local extension stored in Grid Zero, and Grid Zero gets exactly the same graph as before (ADR 0001). New readers, based on tree-sitter (ADR 0002), open the tool to dpe (`.mjs`) then to 4cast (TypeScript, Svelte and PHP). A Claude Code skill teaches the tool to the agent in every project. The tool stays in French during the extraction, then it switches to English before welcoming a second host: that is the condition for being able to publish it some day.

## User stories

1. As an agent working in a host project, I want to type `graphe explain X` in any repository, to locate code without grep.
2. As an agent, I want to designate a node by its id, its name, `Class.method` or `file::name`, so as not to have to know the internal ids.
3. As an agent, I want `graphe callers X --depth N`, to measure the reach of a change before making it.
4. As an agent, I want `graphe path A B`, to understand how an action leads to an effect.
5. As an agent, I want `graphe search PATTERN` by name, by displayed text and by comment, to find the code of a text seen on screen or of a concept.
6. As an agent, I want `explain X --source`, to read a function's body without opening its file.
7. As an agent, I want `explain X` to list the documents that cite X, to find the ticket that motivated some code.
8. As an agent, I want a query on a stale graph to rebuild it first, never to reason on a wrong graph.
9. As an agent, I want the graph to be considered stale also when the tool itself has changed, to benefit at once from a fixed reader.
10. As an agent, I want short, dense answers, to spend few tokens.
11. As an agent arriving in a new project, I want a skill that tells me when to prefer the graph to grep, how to designate a node and where to note a gap, to use the tool without a project-specific memory.
12. As an agent who finds a question the graph cannot answer, I want to note the gap in the tool's single backlog, naming the host, so that the tool improves in the same place for all projects.
13. As a developer, I want to install the tool once in editable mode, so that a fix serves all hosts without a copy.
14. As a developer, I want the tool to work in a repository without configuration, to try it on a project in one command.
15. As a developer, I want to exclude folders through `graphe.toml`, for example dpe's `scratch_debug`, to keep the graph on the code that matters.
16. As a developer, I want the files no reader takes, like dpe's XML, to be ignored without configuration.
17. As a developer, I want to set the path of each external program a reader runs, like the Godot executable, in `graphe.toml`, so that the tool works whatever the installation.
18. As a developer, I want a reader to find its program in the PATH when `graphe.toml` does not give it, and to go on without it with a warning that names the key to set when it does not find it, so that a missing program never breaks the build.
19. As a Grid Zero developer, I want my graph to stay identical after the extraction, to lose nothing of what tickets T-0353 and T-0354 built.
20. As a Grid Zero developer, I want to keep `python tools/graphe.py …`, my git hooks and my habits, so that the extraction costs me nothing day to day.
21. As a Grid Zero developer, I want the scenario hints, the state protocol, the server commands, the online service's actions, the texts of `I18n` and the moonshot journal to live in a local extension of Grid Zero, so that the core knows nothing of the game.
22. As the author of a local extension, I want to write a function `contribute(project)` that returns a contribution, like a reader, to have only one contract to learn.
23. As the author of a local extension, I want to read the graph already assembled, to link my nodes to those of the readers.
24. As the author of a local extension, I want a node returned with an existing id to enrich that node, to add attributes (displayed texts, for example) without recreating it.
25. As the author of a local extension, I want the schema of a node and of a link to be a documented contract, and not networkx's internal structure, so that my extension survives a change of library.
26. As the author of a reader, I want to return coverage sites, so that `graphe check` says what my reader resolved and what it missed.
27. As a developer, I want all the Markdown files git tracks to be documents by default, and `graphe.toml` to be able to restrict them, so that dpe's tickets and 4cast's issues enter the graph without setup.
28. As a developer, I want to set the documents' identifier pattern (`T-\d{4}` by default), so that tickets cite each other whatever the project's format.
29. As a dpe developer, I want the `.mjs` and `.js` files to be read, calls resolved by the name and by the imports, to navigate the calculation engine.
30. As a 4cast developer, I want the `.ts` files and the `<script>` block of the `.svelte` files to be read, and the PHP API by the existing PHP reader, to navigate from the front to the back.
31. As a developer, I want the tool to read itself, tickets included, to have a third test host at no cost.
32. As a developer, I want `graphe install` to set the git hooks and add the output folder to the host's `.gitignore`, so that a new host is ready in one command.
33. As a developer, I want `graphe install --remove` to remove the hooks, to take a host out cleanly.
34. As a future open-source maintainer, I want an interface entirely in English (commands, configuration keys, JSON fields, node kinds, code, documentation), so that others can use it.
35. As a developer, I want the switch to English to come before the second host, to have only one host (Grid Zero) and its memories to migrate.
36. As a developer, I want to keep `graphe.html` and `REPORT.md` for my own explorations, even if the agent comes first.

## Implementation decisions

- **Form.** A separate repository, a Python package that provides the `graphe` command, installed with `uv tool install -e`. The dependencies are networkx and tree-sitter, plus the grammars from the JS/TS reader on. The first commit cites the Grid Zero commit the code comes from, without taking over the history.
- **The host's root** is the current git repository, and no longer the script's location. The output stays in `graphe/` at the host's root.
- **The files read** are those git tracks, plus the untracked files that are not ignored, as today ("working tree included"). Each file goes to the reader its extension designates. Tests and build stay excluded by default in Grid Zero, through its `graphe.toml`.
- **The `contribute(project)` contract.** It is the single interface of readers and local extensions. `project` gives the root, the host's files, the configuration (the section specific to the contributor) and the graph already assembled, read-only. The contribution returns nodes, links and, where relevant, coverage sites.
- **The schema of nodes and links** takes the current fields: id, label, kind, source file, line for a node; source, target, relation, confidence (`EXTRACTED`/`INFERRED`), location, context for a link. It is documented as a contract, and networkx is not part of it.
- **The merge.** A node returned with an existing id merges its attributes into the node in place. A link to an absent node is counted as dangling, as today.
- **The assembly order**: the readers, then the core's enrichments, then the local extensions in the order `graphe.toml` declares them. Nodes and links are sorted before insertion, so that the communities (Louvain, fixed seed) do not depend on the order of the contributions.
- **The core** takes from the current enrichment:
  - the end of each body and its source lines;
  - the comment above a body;
  - the module variables and the bodies that read or write them;
  - the Python modules imported under an alias;
  - the fields passed by keyword to the constructor;
  - the values written in two languages;
  - the documents and their citations.

  The notion of displayed text stays in the core, but the pattern of the call that displays a text (in Grid Zero, `I18n.t` and `I18n.tn`) comes from the host's configuration.
- **The GDScript reader** takes the `preload` constants and their resolution to the preloaded script.
- **Grid Zero's local extension** takes:
  - the server's command branches (today read in the Python reader), the orders the client sends to the server (today in the GDScript reader) and the check of orders unknown to the server;
  - the fields of the state sent to the client and the keys the GDScript reads from it;
  - the `"action"`s posted by the GDScript to the PHP actions;
  - the scenario hints;
  - the moonshot journal.

  The node ids stay today's (`simulation_server_cmd_…`, `conseil_…`, etc.).
- **External programs.** Each reader that runs a program has its section in `graphe.toml`, with an `executable` key. The search order is: `graphe.toml`, then the PATH, then nothing. Without a program, the reader goes on with a warning that names the key, and the calls it would have resolved stay unresolved.
- **Documents.** They are all `.md` files by default, restricted by a list of patterns in `graphe.toml`. A document cites a node it names between backticks, and another document by an identifier with a configurable pattern (`T-\d{4}` by default). The code that contains a document's identifier cites that document. Grid Zero restricts its list to the tickets, to keep its graph; the moonshot journal goes through its extension.
- **Freshness.** The graph is stale if a file of the host or a file of the tool is newer than it. `install` sets the post-commit, post-merge, post-checkout and post-rewrite hooks, and adds the output folder to the `.gitignore`.
- **Grid Zero** keeps a reduced `tools/graphe.py`, which forwards its arguments to the `graphe` command. Its git hooks, its README and its memories keep working.
- **The JS/TS readers** rest on tree-sitter: a single reader for `.js`, `.mjs` and `.ts`, plus the `<script>` block of `.svelte` files. Calls are resolved by the name and by the imports. The choice of grammars (one common package or one package per language) is made in the reader's ticket.
- **The language.** The extraction and steps 2 and 3 stay in French. A dedicated step switches everything to English (commands, keys, JSON fields, node kinds, code, documentation, glossary), together with Grid Zero, its memories and its README.
- **The steps.** Each can be checked on its own:
  1. extraction with identical behaviour;
  2. configuration, `contribute` contract and Grid Zero's local extension;
  3. generalised documents;
  4. switch to English;
  5. JS reader (dpe);
  6. TypeScript and Svelte (4cast).
- **The backlog and the skill.** The gaps file becomes the tool's single backlog, and each entry names its host. A Claude Code skill, shipped in the repository and installed once for the account, replaces Grid Zero's two "graphe" memories.

## Testing decisions

- **A good test checks observable behaviour**: the `graphe.json` and the text of a query, or the contribution returned. Never a reader's internal structure.
- **The three test points, validated by the user:**
  1. **The `graphe` command on a small sample host project**, one per language (Python, GDScript, PHP, JS, TS/Svelte), plus a project without configuration and a project with documents. The test runs `build`, then `explain`, `callers`, `path` and `search`, and checks the JSON and the text. It is the main point.
  2. **`contribute(project)`**, to test a reader or an extension in isolation. Grid Zero's `test_graphe.py` already does so: it calls the Python reading directly, on sources written in a temporary folder. It moves into the tool's repository and passes without changing its assertions.
  3. **The reference test, in Grid Zero.** Its `graphe.json` is compared to a snapshot, without the timestamp or the commit. The snapshot is taken *after* the sorting of nodes and links is introduced. We then check once, by hand, that the difference with the graph produced before the extraction is limited to the numbering of the communities. The test holds until the switch to English, which retakes it with the translated names.
- **The check of the readers** (`graphe check`) stays a coverage test on each host. Grid Zero keeps its threshold.
- **The regression threshold on dpe and 4cast**: none, to start with. The first run establishes a reference coverage, noted in the reader's ticket.

## Out of scope

- The TypeScript compiler and resolving calls by types (ADR 0002). We move to it only on proof of missed calls.
- An XML reader. dpe's XML is data.
- The `.po` translation files and the tests that compare a whole message: they stay outside the graph, as today.
- Publication: final name, licence, PyPI, documentation for strangers, and any platform other than Windows.
- Taking over Grid Zero's git history.
- A remote tracker for the tool.

## Notes

- The default pattern `T-\d{4}` already serves three hosts: Grid Zero, dpe and the tool itself. 4cast names its issues otherwise: its `graphe.toml` will give its pattern.
- **Risk of step 2:** moving the command branches out of the Python reader forces the extension to reread `server.py` through the `ast`. The reference test will tell whether the ids and the `dispatches` links stayed the same.
- **Risk of step 4:** the switch to English touches the JSON read by `graphe.html` and Grid Zero's memories that cite the French commands. The memories must be migrated in the same step.
- The decisions of the interview are in ADRs 0001 and 0002, and the vocabulary in `GLOSSARY.md`.

## Comments

**2026-11-17, after T-0002.** The reference test compares the graph of a frozen tree (Grid Zero's `graphe-reference` tag), not that of the working tree, which changes at each commit and contains the tool itself. The sorting changed the partition of the communities, not only their numbering: the snapshot taken after the sorting is authoritative. The tool's dependencies include scipy (the layout of large graphs).

**2026-11-18, after T-0010.** Grid Zero's snapshot is taken a second time, before the switch to English. A document cites a ticket by its identifier, and Grid Zero keeps its tickets as documents: its tickets therefore cite each other, whatever the restriction. Restricting to the tickets therefore does not keep the whole graph. The difference, checked by hand: 1902 `cite` links from one ticket to another, and the positions (x, y) of the 379 tickets. No community of the code changes. By the user's decision, the new snapshot (Grid Zero, T-0387) is authoritative.

**2026-11-18, after T-0011.** Grid Zero's snapshot is taken a third time, with the English names (Grid Zero, T-0388). The old one, translated by T-0011's correspondence table, is identical to the new one: 258 ids renamed (`value_`, `hint_`, `_constant`), no community or position changed. The reference test holds again, now for the English names.

**2026-11-18, after T-0012.** The code, the docstrings, the comments, the glossary, the ADRs, the backlog (`graphe_manques.md` becomes `BACKLOG.md`) and the open tickets are in English. Grid Zero's snapshot did not move.
