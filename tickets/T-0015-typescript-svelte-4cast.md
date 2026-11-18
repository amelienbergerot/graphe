Status: ready-for-agent
Type: task
Part of: T-0001
Blocked by: T-0014
Created: 2026-11-17

# T-0015: TypeScript and Svelte, plugged into 4cast

## What to build

The JS reader also reads the `.ts` files and the `<script>` block of the `.svelte` files. 4cast becomes the third outside host. Its `graphe.toml` gives the identifier pattern of its issues, and its PHP API is read by the existing PHP reader.

## Acceptance criteria

- [ ] A small sample TS and Svelte project gives the expected links, including from a Svelte component to a TS function.
- [ ] In 4cast, `graphe path` links a Svelte component to the TS function it calls, and `explain` names the issue that cites it.
- [ ] The coverage of `check` on 4cast is noted in this ticket, as a reference.
- [ ] The missed calls are noted in the backlog, with the host.
