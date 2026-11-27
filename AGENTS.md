# Graphe

## The backlog

Each time the graph does not answer and you search by hand (grep, reading), here or in a host, add an entry to `BACKLOG.md` under "Open", as soon as the gap appears:

```markdown
- **What the graph could not tell, in one line.** (Host, YYYY-MM-DD)
  What you were looking for, what the graph answered, how you found it,
  and the improvement that would have avoided the search.
```

- One entry per gap: when it is already noted, extend that entry.
- From a host, commit it in this repository, apart from the host's work.
- A settled entry moves to "Settled", with the commit that settles it.
- A gap the language's missing reader explains (no reader for that host yet) is already known: skip it.

## Agent skills

### Issue tracker

GitHub Issues of `amelienbergerot/graphe`, in the Project graphe, titled `T-NNNN: ...`; `tickets/` is the archive of T-0001 to T-0093. Work lands through a pull request that closes its issue. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default roles, as GitHub labels. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the root. See `docs/agents/domain.md`.
