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
