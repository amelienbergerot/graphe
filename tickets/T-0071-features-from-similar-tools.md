Status: closed
Type: spec
Created: 2026-11-27

# What similar tools do that the graph should

## Problem Statement

Similar tools were surveyed (`docs/research/similar-tools.md`, graphify compared before it): several answer questions the graph cannot, or answer them more precisely. An agent working in a host meets the gaps every day:

- An unattributed call is announced by a count only ("+ N calls named `f` the graph could not attribute: grep them"): the agent cannot tell a name two classes share, where a grep settles it in seconds, from a common name, where a grep returns hundreds of lines.
- What a change reaches takes one `callers` per function, listed by hand from the diff.
- A React host gets no graph of its `.jsx` and `.tsx` files, a Vue host none of its components.
- The skill's description is the only thing that brings the agent to the graph: an agent that greps a name the graph knows is never told.
- The skill reaches Claude Code alone; another agent's user is told to copy a folder.
- A generated file repeated in a host makes every name it defines ambiguous, and nothing names it: the host's author learns of it only by reading the backlog.
- `T::f()` in Rust and `C.f()` in Java or Kotlin name the class, yet the call is linked only when `f` has a single definition in the whole language: thousands of such calls stay unattributed on libsignal and protobuf.
- A call to an abstract method, or to a Swift protocol's requirement, is ambiguous between its implementations and linked to none.

Behind all of these, nothing protects the links already resolved: the sample hosts are measures taken by hand, and the tests check chosen links, not all of them. A change to the linking could lose links silently.

## Solution

- Every reader, and the core, gets a small sample host with a committed snapshot of all its links; a change that alters a link shows up in the diff of the snapshot, and is accepted only with its reason.
- The line about unattributed calls gives each cause and, when few, the candidates.
- `graphe affected [REV]` answers what a change reaches: the nodes a diff touches, then their callers.
- `.jsx` and `.tsx` are read by the JS reader, Vue components as Svelte's are.
- On Claude Code, a hook adds one line to a grep whose pattern is a name the graph knows, pointing to the query that answers it. It never blocks the grep.
- The skill ships to Codex, Cursor, Copilot and Gemini CLI too, each marked untested until users report back.
- `check` and the report name the generated files, with an `exclude` to paste.
- A qualifier that names a class of the host narrows a call's candidates to that class's methods; a call whose candidates all override one declaration is linked to that declaration. Both stay exact: a call is linked only when one candidate is left.

## User Stories

1. As an agent, I want the line about unattributed calls to say why each was not attributed, so that I know whether a grep is worth it.
2. As an agent, I want the candidates of an ambiguous call listed when there are few, so that I can query the right one instead of grepping.
3. As an agent, I want a common name said to be one, so that I do not grep a name that matches the whole repository.
4. As an agent, I want a call whose definition is outside the host told apart from an ambiguous one, so that I do not search the host for code it does not hold.
5. As an agent, I want a receiver of unknown type named as the cause, so that I know the graph's callers may miss some and a grep for `.f(` completes them.
6. As an agent, I want `graphe affected` to list what my uncommitted changes reach, so that I know what to re-test before committing.
7. As an agent, I want `graphe affected REV` to compare with a revision, so that I see what a branch reaches against its base.
8. As an agent, I want the reach of a diff to a depth I choose, defaulting to 1 as `callers`, so that the answer stays short unless I ask.
9. As an agent, I want a change outside any function counted for its file, so that a change at a module's top level is not lost.
10. As an agent, I want a function the diff removes listed by its name, so that I know to look for callers of something that no longer exists.
11. As an agent, I want the marks of `explain` and `callers` (`[by name]`, `?`, the unattributed line) kept in `affected`'s answer, so that I trust it as much and no more.
12. As a React host's author, I want my `.jsx` and `.tsx` files read, so that the graph answers for my components' code.
13. As a Vue host's author, I want my `.vue` components' script and template read, so that a call in the template has its caller.
14. As an agent on Claude Code, I want a grep for a name the graph knows to come back with one line naming the query that answers it, so that I use the graph without remembering to.
15. As an agent, I want the hook to stay silent when the pattern is no name the graph knows, so that it costs nothing on a text search.
16. As an agent, I want the hook never to block my grep, so that grep stays available when the graph falls short.
17. As an agent, I want the hook never to rebuild the graph, so that a grep never waits a minute on a large repository.
18. As an agent, I want the hook silent in a repository without a graph, so that it does no harm where graphe is not installed.
19. As a user of Codex, Cursor, Copilot or Gemini CLI, I want the skill installable for my agent, so that it locates code with the graph too.
20. As such a user, I want the README to say plainly that my agent's install is untested, and where to report how it went, so that I know what to expect and how to help.
21. As graphe's author, I want each agent's install to carry the same skill text, so that one edit serves every agent.
22. As a host's author, I want `check` and the report to name the generated files, so that I can exclude the ones that make names ambiguous.
23. As a host's author, I want the `exclude` line to paste, so that acting on it takes one edit.
24. As a host's author, I want a generated file only named, its links unchanged, so that nothing disappears from the graph without my decision.
25. As an agent in a Rust host, I want `T::f()` linked to `T`'s method `f` when `T` is a class of the host, so that `DeviceId::new` has its callers.
26. As an agent in a Java or Kotlin host, I want `C.f()` linked the same way, so that a static call names its definition.
27. As an agent, I want a class whose nodes are in several files (a Rust `impl` apart from its `struct`) to count as one class for its qualifier, so that the qualifier still narrows its candidates.
28. As an agent, I want a qualified call still unattributed when the class has several methods of the name, so that no link is a guess.
29. As an agent in a Java host, I want a call to an abstract method linked to its declaration when all its candidates override it, so that `input.pushLimit(n)` has a definition.
30. As an agent in a Swift host, I want a call to a protocol's requirement linked to the requirement, so that a conformance's calls are found.
31. As an agent, I want an abstract method and a protocol requirement to be nodes with links from their implementations, so that `explain` on an implementation leads to the calls through its declaration.
32. As graphe's author, I want each reader's sample host and the core's to have a snapshot of all their links, so that a change that loses a link fails a test.
33. As graphe's author, I want a script that rewrites the snapshots, so that a deliberate change costs one command and a reviewed diff.
34. As graphe's author, I want the snapshot to say for each link its relation and whether it is sure or by name, so that a link turning from sure to guessed is seen.
35. As graphe's author, I want the core's sample host to hold a document citing code, keyed links and a displayed text, so that the links no reader makes are protected too.
36. As graphe's author, I want ADR 0003 amended once for the two new linking rules, so that a future reader knows why "by its name alone" was widened and how far.
37. As graphe's author, I want each change that alters links measured on the sample host its backlog entry names, so that the README's figures and the backlog stay true.

## Implementation Decisions

The work is ten tickets, in this order. The snapshot gate blocks the two linking rules; the qualifier rule blocks the override rule.

1. **The snapshot gate.** One sample host per reader (Python, JS/TS/Svelte, GDScript, PHP, and each language of the generic reader) and one for the core (a document citing code by backticks and by identifier, a `graphe.toml` with `[keys]` and `displayed_text`). Each is built as a real host is. Its links are written one per line, sorted: source, relation, target, sure or by name. A test compares the built links with the committed snapshot; a script rewrites the snapshots. Nothing else in the build changes.
2. **The cause of an unattributed call.** The build already gives each call site a verdict; the answer of `explain` and `callers` groups the unattributed calls of a name by cause: several definitions (with the candidates when they are few, five at most), common name, receiver of unknown type, definition outside the host. The causes are the glossary's (Unattributed call). The graph's stored counts become counts per cause.
3. **`graphe affected [REV]`.** Without `REV`, the working tree against `HEAD`; with `REV`, against it. The diff's changed line ranges map to the nodes whose extent holds them (each body's start and end lines are already stored); a range outside any body counts for its file node. A function present in the diff's removed lines and no longer in the graph is listed by name, without callers. Then the callers of each touched node to `--depth`, default 1, printed as `callers` prints them, with its marks. The diff comes from git, as the files do.
4. **`.jsx` and `.tsx`.** Routed to the JS reader: `.jsx` with the JavaScript grammar, which parses JSX, `.tsx` with the TSX grammar the TypeScript package ships. A JSX `<Component/>` is not a call: it stays with the framework entry of the backlog (T-0047).
5. **The Claude Code hook.** A new command, `graphe hook`, reads the hook's JSON on stdin and writes the hook's JSON answer on stdout. It answers only for the Grep tool and for `grep`/`rg` run through Bash or PowerShell, and only when the pattern is a name a node bears: one line of added context naming `graphe explain` on it. It never blocks (fail-open), never rebuilds the graph, and is silent without a graph, on any error, or for any other tool. No cap on the hints at first; their frequency is measured before one is added. The plugin declares the hook.
6. **The other agents.** Codex, Cursor, Copilot and Gemini CLI. Where the agent has a plugin or skill format, a manifest beside Claude Code's, carrying the same skill text, kept free of anything Claude Code alone understands (T-0048, T-0049's precedent). Otherwise a README line saying where to copy the skill's folder. The README marks each one "untested, reports welcome in the issues". The hook stays Claude Code's. Each format is checked against the agent's own documentation when the ticket is worked, not assumed.
7. **Generated files, named.** A file is generated when git's attributes mark it (`linguist-generated`) or when its header carries a known marker (protobuf's compiler, Go's convention). The markers are data, beside each language's. `check` and the report list the generated files with a ready `exclude`. No link changes.
8. **The qualifier rule.** In the generic reader, a call whose qualifier names a class of the host (`T::f`, `C.f`) keeps as candidates only the methods `f` of the classes named `T` in the same language or family, whatever file holds them. It is linked, sure, only when one candidate is left; otherwise it is unattributed as before. A common name qualified by a host class is no longer skipped. ADR 0003 gets one amendment, written with this ticket, covering this rule and the next. Measured on libsignal and protobuf.
9. **Override families.** Abstract methods, interface methods and Swift protocol requirements become nodes; an implementation gets an `overrides` link to the declaration it implements, found by its class's base list. When every candidate of an ambiguous call overrides one declaration, the call is linked, sure, to that declaration. It does not link a call to all its candidates (ADR 0003's option set aside). Measured on protobuf (`pushLimit`) and libsignal (Swift).
10. **Vue.** A `.vue` file takes the Svelte path: its `<script>` to the JS reader, its template's expressions parsed for their calls, which belong to the component.

The contract (`contribute(project)`, the shape of the nodes and links) changes in two tickets only: 2 (the counts per cause) and 9 (the `overrides` relation and the new node kinds). A release that carries either notes it in CHANGELOG.md's **Contract** section.

## Testing Decisions

- A good test drives the tool from outside: a host made of a few files, a command, the answer it prints or the links it builds. No test reaches into a reader's internals.
- Three seams, two existing. The temporary host (prior art: the host tests, a git repository made in a temporary folder, a command, its output) serves tickets 2 to 5 and 7 to 10, the hook included: `graphe hook` is fed a JSON on stdin and its stdout read. The snapshot of links is the new seam, at the same height: a sample host per reader and one for the core, built, its links compared with the snapshot (ticket 1). The plugin tests (prior art: the version and the skill's allowed tools checked) serve ticket 6.
- The per-language tests of the generic reader stay for each language's details; tickets 8 and 9 add theirs there too.
- Tickets 8 and 9 update the snapshots their rule changes, the diff reviewed in the commit, and measure their sample hosts as `docs/sample-hosts.md` replays them.
- Ticket 2's answer is tested for each cause; ticket 3 for an uncommitted change, a revision, a change outside a body and a removed function; ticket 5 for a known name, an unknown pattern, another tool, no graph and malformed input.

## Out of Scope

- An MCP server: until an agent without a shell needs one; the hook and the `Bash(graphe *)` rule serve Claude Code.
- Incremental resolution, reading a SCIP index, framework presets for keyed links, `locals.scm` for Ruby's bare calls: kept in their backlog entries, with a pointer to the research note.
- A token-budgeted ranked map: set aside.
- A dedicated Go reader (`pkg.F()` through `go.mod`): its backlog entry stays open until a host needs it.
- Dropping generated files' definitions from the candidates: after ticket 7, if an `exclude` does not suffice.
- A JSX `<Component/>` or a Vue `<component>` tag as a link: the framework entry (T-0047).
- A cap on the hook's hints, a strict mode that blocks grep.

## Further Notes

- Sources: `docs/research/similar-tools.md` (12 tools and three code-graph MCP servers, 14 ideas ranked), graphify's comparison in BACKLOG.md, the decisions of a grilling session on 2026-11-27.
- Glossary terms added in that session: Unattributed call, Generated file.
- The backlog entries these tickets settle: "What a diff reaches takes one `callers` per function.", "`.jsx`, `.tsx` and Vue are not read.", "The skill reaches Claude Code alone, and only for the questions it names.", "A Rust `Type::f()` path is not linked when `f` is a common name.", "A Java call to an abstract method is linked to none of its implementations.", and in part the generated-code entries (Java, C#, the C amalgamation) and "Swift's FFI conformances make their methods' names ambiguous.".

## Comments

- 2026-11-27: closed. Its implementation tickets (`Part of: T-0071`: T-0072 to T-0086, T-0083 aside) are all closed, T-0082 resolved; the backlog entries it kept open stay so, each with its pointer (Out of Scope above). The skill's reach to the other agents (T-0078) still waits on users' reports, in its backlog entry.
