# 📚 Assistant d'entraînement au droit des brevets

Ce projet propose un assistant pédagogique pour les étudiants en droit des brevets, capable de générer des questions d'examen réalistes et de fournir une évaluation automatique des réponses, avec des justifications juridiques extraites de textes officiels (EPC, PCT, Guidelines...).

---
## Auteurs

- GADZINA Guillaume
- BERGES Julien
- AURÉ Nolhan

### 1. Prérequis
- Docker  
- Ollama installé sur votre machine [https://ollama.com/download]
- Le modèle mistral téléchargé via : 
  ```sh
     ollama pull mistral
  ```

### 2. Lancement
Placez vous dans `data_battle_paulympe/` puis utilisez les commandes suivante pour démarrer l'application :  
  ```sh
    docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
    docker-compose up --build
  ```

### 3. Ouverture dans le navigateur
Utilisez l'URL suivant dans votre navigateur:  
     [http://localhost:5173]

## 🗂️ Arborescence du projet

Voici une description de l'arborescence du projet, en expliquant le rôle de chaque répertoire et fichier important :

---

### 🔧 `backend/` : Partie backend avec FastAPI et embeddings IA
- `app.py` : API FastAPI principale (génération de questions, analyse de réponses).
- `index_faiss/` : Index FAISS final, utilisé pour la recherche de documents vectorisés.
- `data_preparation/` : Scripts de nettoyage, parsing et transformation des textes.
- `json/` : Fichiers QCM nettoyés au format JSON (question / réponse).
- `Official_Legal_Publications_TXT/` : Textes légaux officiels bruts ou nettoyés.
  - `EPC/` : Convention EPC, Règlement d'application, Protocoles, etc. nettoyés.
- `data_base/` : Versions brutes ou anciennes des fichiers.
- `emissions.csv` : Mesure de la consommation énergétique (outil CodeCarbon).

---

### 💻 `frontend/` : Interface utilisateur React
- `public/` : Fichiers statiques accessibles (favicon, index.html...).
- `src/` : Composants React :
  - UI (pages, boutons, formulaire)
  - Appels à l’API FastAPI (fetch des questions, analyse des réponses)
- `package.json` : Dépendances Node.js et scripts de développement.


---

## ⚙️ Fonctionnalités principales

- 🔎 **Recherche de contexte juridique** via FAISS et LangChain
- 🧠 **Génération de questions d'examen** (MCQ ou ouvertes) à partir du contexte juridique
- ✅ **Analyse automatique des réponses** avec feedback, évaluation, justification et base légale
- 🔄 **Re-ranking contextuel** pour combiner la similarité question + réponse
- 🌱 **Déploiement 100% local** via Ollama + modèles Mistral / Gemma, sans dépendance cloud


---

## 🧠 Technologies utilisées

- **LangChain** – Chaîne RAG (Retrieval-Augmented Generation)
- **FAISS** – Index vectoriel performant pour la recherche sémantique
- **BAAI/bge-m3** –  Modèle de type embedding généraliste pour encoder efficacement questions et documents juridiques.
- **Ollama** – Exécution locale de LLM (Mistral 7B)
- **FastAPI** – API backend
- **CodeCarbon** – Estimation de l'empreinte carbone du traitement local
- **React** : Frontend interactif pour les étudiants, avec appels dynamiques à l’API.

---

## 🌍 Enjeux environnementaux

Le système a été pensé pour **minimiser son impact écologique** :
- Aucun appel cloud/API externe
- Modèles LLM exécutés localement
- Embedding fait une seule fois en batch, index persisté
- Évaluation de la consommation via `codecarbon`

---

## 🧠 Design de la décision

Chaque décision technique (nettoyage manuel, infrastructure, modèle, etc.) a été guidée par :
- **Pertinence pédagogique**
- **Sobriété énergétique**
- **Clarté de la chaîne de traitement**
- **Explicabilité des choix IA**

---
