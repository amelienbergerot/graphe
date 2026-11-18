Status: closed
Type: task
Part of: T-0001
Created: 2026-11-18

# T-0022: The calls in a Svelte component's markup

## What to build

BACKLOG.md (4cast): only the `<script>` goes to the grammar; the markup is blanked out. About 213 calls in the markup of 17 components (`onclick={() => rafraichir(1)}`, `{jourCourt(j.date)}`) are missed: 36 of the 77 component functions have no caller. Each `{...}` of the markup (but `{#`, `{/`, `{:` blocks' keywords) is read as an expression; its calls belong to the component's file node.

## Acceptance criteria

- [x] A function of the `<script>` called in the markup has the component as caller.
- [x] 4cast's coverage noted here.

## Comments

- `_source` keeps each `{...}` of the markup at its place, the braces read as a space and a `;`: ' f(x);', a statement of the module, its calls the component's (its file node). The keyword of a block is cut (`{#if x}`, `{:else if x}`, `{#each xs as x}` keeps `xs`, `{@const c = f()}` keeps `const c = f()`); `{:else}`, `{/if}`, `{#snippet}` keep nothing; neither `<script>`, `<style>` nor comments. A bare name as a statement (`onclick={fermer}`, a prop `onouvrir={ouvrir}`) is a `references`. Shortcut: a brace in a string of an expression miscounts.
- **4cast**: 2537 -> 2717 sites, `ours` 658 -> 731; the component functions without a caller (calls or references) 36 of 77 -> 6 of 80: Chart.js plugins' `beforeDatasetsDraw` (an object passed to the library), `pointillesSiPrevu`, `chargerParcelles`, `lireChampDepuisCarte`. Grid Zero: nothing more than T-0019's coverage.
- **After the review**: the keywords by a pattern (`{#if` before a line break, `{:else if}`, `{@attach f()}`); `{#await p then v}` keeps `p`, as `{#each xs as x}` keeps `xs`; any other `{#`, `{:`, `{/`, `{@` keeps nothing; an expression never closed stops the reading of the markup (no longer copies the rest, `<style>` included). `new it(...)` or a parameter named `it` is not a test (T-0021).
