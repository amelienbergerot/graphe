# tree-sitter for the new readers, not the TypeScript compiler

The JS/TS readers (`.ts`, `.js`, `.mjs`, the `<script>` of `.svelte` files) rest on tree-sitter, and resolve calls by the name and by the imports. The TypeScript compiler (through Node) would resolve types with the precision of the Python reader, but it would make the tool a two-language program and would depend on each host's `tsconfig`. We move to it only if `BACKLOG.md` shows missed calls that the imports do not catch.

The Python (the `ast`), GDScript and PHP (patterns) readers stay as they are.
