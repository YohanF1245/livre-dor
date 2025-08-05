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

bash
```
docker exec -it <container-ollama> bash
ollama pull phi3
exit
```
4. Aller sur l’interface n8n et importer le workflow workflow.json fourni

## Technologies utilisées
- Flask (API backend)

- n8n (workflow d'automatisation)

- Ollama (gestion locale des modèles IA)

- Modèle IA phi3

- PostgreSQL (base de données)

- Docker / Docker Compose (conteneurs & orchestration)