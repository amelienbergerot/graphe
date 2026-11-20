# tree-sitter for the new readers, not the TypeScript compiler

The JS/TS readers (`.ts`, `.js`, `.mjs`, the `<script>` of `.svelte` files) rest on tree-sitter, and resolve calls by the name and by the imports. The TypeScript compiler (through Node) would resolve types with the precision of the Python reader, but it would make the tool a two-language program and would depend on each host's `tsconfig`. We move to it only if `BACKLOG.md` shows missed calls that the imports do not catch.

The Python (the `ast`), GDScript and PHP (patterns) readers stay as they are.

Amended by T-0045 (2026-11-20): the PHP reader by patterns is gone. PHP is read by the generic reader (ADR 0003), which, compared on 4cast, linked the same 81 calls, and read protobuf's 156 classes and 1723 methods where the patterns read 5 functions (T-0044). The Python and GDScript readers stay as they are.
