Status: resolved
Part of: T-0071
Blocked by: T-0076
Created: 2026-11-27

# T-0082: Read Vue components

## What to build

A Vue host gets no graph of its components. A `.vue` file takes the Svelte path: its `<script>` (and `<script setup>`) to the JS reader, in TypeScript when its `lang` says so, its template's expressions (`{{ }}`, `@click`, `:prop`) parsed for their calls, which belong to the component. A `<component>` tag as a link stays with the framework entry (T-0047).

## Acceptance criteria

- [x] A host with a `.vue` component answers `explain` on its functions, a call in its template among their callers.
- [x] A `<script setup lang="ts">` is read as TypeScript.
- [x] A template the reader cannot parse costs its expression only, not the file.
- [x] The JS sample host gains a `.vue` file, its snapshot updated.
- [x] The README's "What it reads" and `docs/readers.md` say so; Vue leaves the "Not read" row, and BACKLOG.md's entry moves to Settled.

## Blocked by

- T-0076 (both edit the JS reader, its sample host and the README).

## Comments

- 2026-11-27: done. `js._parse` gives a `.vue` file the Svelte treatment: its `<script>` blocks kept, the rest blanked out byte for byte, then its template's `{{ }}` and the values of its directives (`@x`, `:x`, `v-on`, `v-bind`, `v-if`, `v-else-if`, `v-show`, `v-model`, `v-html`, `v-text`, `v-memo`; `v-for` after its `in`/`of`) kept as statements. Each expression is parsed alone first, and one with an error is left blank, so it costs only itself. The grammar is the one `lang` names (`ts`, `tsx`), JavaScript without one. Vue's compiler macros (`defineProps`...) and `$emit` are globals. The JS sample host gains `src/Meter.vue`; the snapshot's seven new lines were written by hand before the build, which gave exactly those. Not read: the Options API's `methods: {}` (a call to one stays `unknown`), `v-slot`/`#slot` (a pattern, no call).
- 2026-11-27: after the review: an expression is kept only if the `;` that ends it is a token, so `{{ a // b }}` no longer swallows the expressions after it on its line; Svelte and Vue share `_component` (the blanking and the spans not read). Left as is (rare): an unclosed `{{` runs on to the next `}}`, and `{{ }}` in an attribute or a `:x=""` in text are read too.
