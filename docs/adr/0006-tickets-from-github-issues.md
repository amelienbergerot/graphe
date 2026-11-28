# Tickets read from the host's GitHub issues

A host whose tickets are GitHub issues says so in `graphe.toml` (`[tickets] github = true`, or `github = "owner/repo"`), and the build makes each issue whose title starts with an identifier a ticket, as a document whose file name starts with one is (T-0095). Without the setting, nothing changes: a build reads no network, and a host's ticket files stay its tickets. graphe's own tickets moved to its issues (T-0094); the graph had to follow or lose every link from the code to them.

It is the first time a build leaves the host. Three rules keep a build what it was, local and never blocked:

- **A cache, fetched at most every 10 minutes.** The issues and their comments are kept under `graphe/` (not committed) and fetched again, only what changed since (`since`), when the cache is older than that. A build that cannot reach GitHub uses the cache, or builds without the issues, and says so in one line: a git hook never stops a commit because GitHub does not answer. An issue edited on GitHub does not make the graph stale; it is in the graph within 10 minutes of the next build.
- **The repository is the host's.** `github = true` takes the one github.com repository the remotes' URLs name (fetch and push); none, or several, and the build goes without the issues and says what to set, `graphe installer` asking when several. A remote is never guessed into a fetch the host did not ask for.
- **The standard library, no `gh`.** The REST API by `urllib`: a public repository needs no token, and 100 issues fit in one or two requests, far under the 60 an hour an unauthenticated client gets. A token is used when one is there (`GH_TOKEN`, `GITHUB_TOKEN`, then `gh auth token`).

An issue and a file with the same identifier: the issue is the ticket, the file a document. An issue's location is its URL (a citation from a comment: the comment's), without a line.

## Options set aside

- `gh` for the fetch: a stranger who installs graphe would need it installed and logged in.
- A fetch on demand only (a command of its own): a new ticket would stay outside the graph until someone thinks to run it.
- A fetch at every build: a network call in every git hook and every stale query, for issues that rarely change between two builds.
- A committed cache: stale at the next commit, and a diff for every issue edited.
- The pull requests: they cite tickets too, but the commit and the issue already carry the link.
