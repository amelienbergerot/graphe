Status: ready-for-agent
Type: task
Part of: T-0001
Blocked by: T-0014
Created: 2026-11-17

# T-0015 : TypeScript et Svelte, branchés sur 4cast

## Ce qu'il faut construire

Le lecteur JS lit aussi les fichiers `.ts` et le bloc `<script>` des fichiers `.svelte`. 4cast devient le troisième hôte extérieur. Son `graphe.toml` donne le motif d'identifiant de ses issues, et son API PHP est lue par le lecteur PHP existant.

## Critères d'acceptation

- [ ] Un mini-projet témoin TS et Svelte donne les liens attendus, y compris d'un composant Svelte vers une fonction TS.
- [ ] Dans 4cast, `graphe chemin` relie un composant Svelte à la fonction TS qu'il appelle, et `expliquer` nomme l'issue qui la cite.
- [ ] La couverture de `verifier` sur 4cast est notée dans ce ticket, comme référence.
- [ ] Les appels manqués sont notés dans le backlog, avec l'hôte.
