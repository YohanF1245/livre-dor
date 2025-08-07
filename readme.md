# Agent d'analyse de commentaires (WIP)

## Description

Ce projet est un exercice personnel pour me former aux agents IA et à l'automatisation avec n8n.  
L'objectif est de créer un workflow automatisé qui analyse un commentaire utilisateur pour en extraire des informations clés :  
- résumé synthétique  
- sentiment (positif / négatif / neutre)  
- mots clés principaux  

## Fonctionnement

À chaque nouveau commentaire posté, une requête est envoyée au webhook n8n.  
n8n transmet ensuite un prompt à un agent IA local (`phi3` via Ollama).  
Après réception de la réponse, n8n effectue une requête PUT vers le serveur Flask pour mettre à jour la base de données avec les résultats de l'analyse.

## Installation

1. Cloner ce repository  
2. Lancer le projet avec Docker Compose :  
   ```
   docker compose up -d
   ```
3. Télécharger (pull) le modèle IA phi3 dans le conteneur Ollama :

```
docker exec -it <container-ollama> bash
ollama pull phi3
exit
```

pour le modele phi3
```
docker exec -it <container-ollama> bash
ollama pull mistral:instruct
exit
```
pour le modele mistral instruct
4. Aller sur l’interface n8n et importer le workflow workflow-phi3.json ou workflow-mistral-instruct (selon le modèle choisi) fourni <br>
### Choix du modèle
Ce projet propose deux workflows distincts selon le modèle de langage utilisé : phi3 et mistral-instruct.
Le modèle phi3 est plus léger et rapide, idéal si vous cherchez des réponses rapides avec un compromis sur la finesse des analyses. En revanche, il peut parfois générer des erreurs de parsing JSON ou des résultats moins précis.<br>
Le modèle mistral-instruct est plus puissant et précis, offrant des réponses plus robustes et réalistes, au prix d’un temps de traitement plus long et d’une image Docker plus volumineuse. Ce modèle est recommandé si la qualité et la fiabilité des résultats sont prioritaires.<br>

## Technologies utilisées
- Flask (API backend)

- n8n (workflow d'automatisation)

- Ollama (gestion locale des modèles IA)

- Modèle IA phi3

- PostgreSQL (base de données)

- Docker / Docker Compose (conteneurs & orchestration)