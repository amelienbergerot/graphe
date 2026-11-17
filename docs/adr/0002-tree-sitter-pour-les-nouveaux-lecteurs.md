# tree-sitter pour les nouveaux lecteurs, pas le compilateur TypeScript

Les lecteurs JS/TS (`.ts`, `.js`, `.mjs`, le `<script>` des `.svelte`) reposent sur tree-sitter, et résolvent les appels par le nom et par les imports. Le compilateur TypeScript (via Node) résoudrait les types avec la précision du lecteur Python, mais il ferait de l'outil un programme à deux langages et dépendrait du `tsconfig` de chaque hôte. On n'y passe que si `graphe_manques.md` montre des appels manqués que les imports ne rattrapent pas.

Les lecteurs Python (l'`ast`), GDScript et PHP (des motifs) restent tels quels.
