Status: ready-for-agent
Type: task
Part of: T-0001
Blocked by: T-0007
Created: 2026-11-17

# T-0008 : Extension Grid Zero : les commandes du serveur

## Ce qu'il faut construire

Les branches de commande du serveur (lues aujourd'hui dans le lecteur Python), les ordres que le client envoie (lus dans le lecteur GDScript) et la vérification des ordres inconnus du serveur sortent des lecteurs. Ils passent dans l'extension locale de Grid Zero, rangée dans Grid Zero et déclarée dans son `graphe.toml`. L'extension relit le module du serveur elle-même. Les ids des nœuds de commande et les liens `dispatches` et `sends` sont inchangés. C'est l'étape la plus risquée du découpage.

## Critères d'acceptation

- [ ] Les lecteurs Python et GDScript ne contiennent plus rien des commandes de Grid Zero.
- [ ] `graphe verifier` dans Grid Zero signale toujours un ordre inconnu du serveur. Témoin : un ordre inventé dans un script de test le fait signaler.
- [ ] Le test de référence de Grid Zero passe.
