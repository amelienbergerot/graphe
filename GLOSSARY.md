# Graphe

Un outil qui lit le code d'un dépôt et en tire un graphe (qui appelle quoi, qui cite quoi), interrogé d'abord par un agent qui navigue dans ce code.

Les termes sont en français jusqu'au passage de l'interface en anglais ; le nom anglais prévu est entre crochets.

## Langage

**Projet hôte** [host project] :
Un dépôt que le graphe lit et où ses résultats sont rangés.
_À éviter_ : projet cible, client, consommateur

**Cœur** [core] :
Ce que l'outil fait pour tout projet hôte, sans rien savoir de lui.
_À éviter_ : noyau, moteur

**Lecteur** [reader] :
Ce qui lit les fichiers d'un langage et en tire des nœuds et des liens.
_À éviter_ : parseur, extracteur, analyseur

**Extension locale** [local extension] :
Un enrichissement propre à un projet hôte, rangé dans le dépôt de cet hôte et déclaré par sa configuration.
_À éviter_ : plugin, greffon

**Contribution** [contribution] :
Ce qu'un lecteur ou une extension locale rend au graphe : des nœuds, des liens et, s'il y a lieu, des sites de couverture.
_À éviter_ : résultat, sortie, extraction

**Document** :
Un fichier Markdown du projet hôte, qui cite des nœuds et d'autres documents.
_À éviter_ : ticket (un ticket est un document parmi d'autres)

**Citation** [citation] :
Le lien d'un document vers un nœud qu'il nomme, ou vers un autre document qu'il désigne par son identifiant.
