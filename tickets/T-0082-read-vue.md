Status: ready-for-agent
Part of: T-0071
Blocked by: T-0076
Created: 2026-11-27

# T-0082: Read Vue components

## What to build

A Vue host gets no graph of its components. A `.vue` file takes the Svelte path: its `<script>` (and `<script setup>`) to the JS reader, in TypeScript when its `lang` says so, its template's expressions (`{{ }}`, `@click`, `:prop`) parsed for their calls, which belong to the component. A `<component>` tag as a link stays with the framework entry (T-0047).

## Acceptance criteria

- [ ] A host with a `.vue` component answers `explain` on its functions, a call in its template among their callers.
- [ ] A `<script setup lang="ts">` is read as TypeScript.
- [ ] A template the reader cannot parse costs its expression only, not the file.
- [ ] The JS sample host gains a `.vue` file, its snapshot updated.
- [ ] The README's "What it reads" and `docs/readers.md` say so; Vue leaves the "Not read" row, and BACKLOG.md's entry moves to Settled.

## Blocked by

- T-0076 (both edit the JS reader, its sample host and the README).
