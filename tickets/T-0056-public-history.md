Status: resolved
Type: grilling
Part of: T-0048
Created: 2026-11-26

# T-0056: What going public publishes

## Question

Making the repository public publishes its whole history, not only its last commit: the `E:\dev\graphe` paths (anonymised only from b3676a0), the names of the private hosts (Grid Zero, 4cast) and their local extensions, BACKLOG.md entries written from them, the tickets that cite their code. Which of it may stay public; is the history published as it is, rewritten, or started afresh; and do the local extensions of Grid Zero and 4cast become public examples or stay private? Decided before T-0054, which needs the repository public.

## Answer

Decided with the user (grilling, 2026-11-26). The facts found: 78 commits, all by `amelien <amelien.bergerot88@gmail.com>`; 41 `E:\dev\graphe` paths, the repository's own; no secret; Grid Zero and 4cast named in 50+ current files; their local extensions not in this repository; 5 commit hashes cited in files (`7681fac` four times, the layout fixture's name among them).

- **Grid Zero and 4cast stay named**, their code's details in the tickets, BACKLOG.md and the comments with them: the user's own projects, no secret, the cases that motivated the tool.
- **Their local extensions stay private**, in their hosts: tied to their code, of no use as an example here. The public example is a small invented one in `docs/contribution.md`.
- **The `E:\dev\graphe` paths stay** in the history: a drive letter and the repository's name.
- **The gmail does not go public: the history is rewritten, the author alone** (`git filter-repo --email-callback`), to `13414890+amelienbergerot@users.noreply.github.com`; the same address for the commits after, by a local `git config user.email`, and GitHub's "Block command line pushes that expose my email" on. filter-repo rewrites the hashes in the messages; the 5 cited in files are replaced from its commit map, and `tests/layout_7681fac.json` is renamed after its new hash. Rejected: a single fresh commit (the tickets cite the history), a separate public copy (two repositories to keep in step).
- **`github.com/amelienbergerot/graphe` goes public**; the Freebox stays the author's private remote, rewritten too (force-push to both), so the two histories stay one. Every other clone is re-cloned.
- **Who and when**: the rewrite is the first steps of T-0054, before its CI (GitHub Actions also runs on a private repository). **The user makes the repository public, when the effort is done**, not an agent.

## Comments

- 2026-11-26: resolved; T-0054 carries the rewrite.
