Status: ready-for-agent
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0022: The calls in a Svelte component's markup

## What to build

BACKLOG.md (4cast): only the `<script>` goes to the grammar; the markup is blanked out. About 213 calls in the markup of 17 components (`onclick={() => rafraichir(1)}`, `{jourCourt(j.date)}`) are missed: 36 of the 77 component functions have no caller. Each `{...}` of the markup (but `{#`, `{/`, `{:` blocks' keywords) is read as an expression; its calls belong to the component's file node.

## Acceptance criteria

- [ ] A function of the `<script>` called in the markup has the component as caller.
- [ ] 4cast's coverage noted here.
