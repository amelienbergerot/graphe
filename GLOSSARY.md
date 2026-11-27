# Graphe

A tool that reads a repository's code and draws a graph from it (what calls what, what cites what), queried first by an agent that navigates that code.

## Language

**Host project**:
A repository that the graph reads and where its results are stored.
_Avoid_: target project, client, consumer

**Core**:
What the tool does for any host project, without knowing anything about it.
_Avoid_: kernel, engine

**Reader**:
What reads the files of one language and draws nodes and links from them.
_Avoid_: parser, extractor, analyzer

**Generic reader**:
A reader that serves many languages the same way: their definitions, and their calls linked by the name alone, or by the class the call names (`T::f()`, `C.f()`).
_Avoid_: fallback reader, basic reader

**Dedicated reader**:
A reader written for one language, which follows its imports and its receivers to link a call to its definition with certainty.
_Avoid_: full reader, native reader

**Common name**:
A method name so frequent outside the host (`Join`, `get`, `push`) that the generic reader never links a call on a receiver to it by name; such a call counts as not attributed.
_Avoid_: stop word, blacklist

**Unattributed call**:
A call whose definition the graph cannot name, for a cause it states: several definitions bear the name, the name is a common name, the receiver's type is unknown, or the definition is outside the host project.
_Avoid_: unresolved call, missing call, unknown call

**Generated file**:
A file of the host project that a tool produced rather than a person wrote, as git's attributes or the file's own header say.
_Avoid_: vendored file, build output

**Local extension**:
An enrichment specific to one host project, stored in that host's repository and declared by its configuration.
_Avoid_: plugin, add-on

**Contribution**:
What a reader or a local extension returns to the graph: nodes, links and, where relevant, coverage sites.
_Avoid_: result, output, extraction

**Takeover**:
What an extension that contributes with the readers returns so that one of its nodes takes the links of certain lines from a reader's node, as a command takes those of its branch from the function that dispatches.
_Avoid_: move, reassignment

**Document**:
A Markdown file of the host project, which cites nodes and other documents.
_Avoid_: ticket for any document (a ticket is a document that has an identifier)

**Identifier**:
What designates a document in a text (`T-0012`), and what its file name starts with. Its pattern is set in `graphe.toml`. A document that has an identifier is a **ticket** (its node kind).
_Avoid_: number, key

**Citation**:
The link from a document to a node it names, or to another document it designates by its identifier.

**Keyed link**:
A link from the place that names a **key** (a string shared by both ends: a route, a command, an action) to the code that answers that key, where no name in the code joins them.
_Avoid_: framework link, magic link, convention link
