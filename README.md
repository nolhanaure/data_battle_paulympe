# 📚 Assistant d'entraînement au droit des brevets

Nous proposons ce rendu dans le cadre du data challenge de [l'association IA PAU](https://iapau.org/).
Ce projet propose un assistant pédagogique pour les étudiants en droit des brevets, capable de générer des questions d'examen réalistes et de fournir une évaluation automatique des réponses, avec des justifications juridiques extraites de textes officiels (EPC, PCT, Guidelines...).

---
## Auteurs

- GADZINA Guillaume
- BERGES Julien
- AURÉ Nolhan
  
⚠️ Sur CPU uniquement c'est très long !
### 1. Prérequis 
- Ollama installé sur votre machine [https://ollama.com/download]
- Python3.11 minimum

### 2. Lancement

#### Étape 1 : Cloner le dépôt 
  ```sh
    git clone https://github.com/nolhanaure/data_battle_paulympe.git
    cd data_battle_paulympe
  ```    

#### Étape 2 : Préparation de l'environnement 
Sous linux : 
  ```sh
    chmod 744 setup.sh
    ./setup.sh
  ```

Sous Windows : 
  ```sh
    .\setup.bat
  ```

#### Étape 2 : Préparation de l'environnement 
Front : 
  ```sh
    cd frontend
    npm install
    npm run dev
  ```

Dans un autre terminal, backend : 
  ```sh
    cd backend
    python3.11 -m uvicorn app:app --reload
  ```
#### Étape 3 : Ouverture dans le navigateur
Utilisez l'URL suivant dans votre navigateur:  
     http://localhost:5173

Ensuite, vous pouvez choisir entre question à thème, question aléatoire ou alors mettre votre propre question. Répondez-y et l'IA l'analysera et fournira une analyse détaillée. Si jamais vous n'avez pas la réponse, il suffit de cliquer sur "Je n'ai pas la réponse" pour que l'IA génère un modèle de réponse.
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
- - `logs/` : Logs reqêtes endpoint codecarbon
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
- 🧠 **Génération de questions d'examen** (MCQ ou ouvertes) à partir du contexte juridique, à choix multiples ou ouvert, sur un thème choisi ou non.
- ✅ **Analyse automatique des réponses** avec feedback, évaluation, justification et base légale
- 🌱 **Déploiement 100% local** via Ollama + modèle Mistral, sans dépendance cloud

---

## 🧠 Technologies utilisées

- **LangChain** – Chaîne RAG (Retrieval-Augmented Generation)
- **FAISS** – Index vectoriel performant pour la recherche sémantique
- **BAAI/bge-m3** –  Modèle de type embedding généraliste pour encoder efficacement questions et documents juridiques.
- **Ollama** – Exécution locale de LLM (Mistral 7B)
- **FastAPI** – API backend
- **CodeCarbon** – Estimation de l'empreinte carbone du traitement local
- **React** : Frontend interactif avec appels dynamiques à l’API.

---

## 🌍 Enjeux environnementaux

Le système a été pensé pour **minimiser son impact écologique** :
- Aucun appel cloud/API externe
- Modèles LLM exécutés localement
- Embedding fait une seule fois en batch, index persisté
- À chaque appel d'un endpoint du backend, nous utilisons la bibliothèque CodeCarbon pour estimer en temps réel les émissions de CO₂ liées à l'exécution. Le tracker s’active au début de chaque traitement (ex. : génération de question ou analyse de réponse) et s’arrête automatiquement après. Cela permet de mesurer de manière précise la consommation énergétique de chaque requête. En plus de l'affichage dans la console, toutes les interactions sont enregistrées dans un fichier JSONL (interactions_log.jsonl) situé dans le dossier backend/logs
---

## 🧠 Design de la décision

Chaque décision technique (nettoyage manuel, infrastructure, modèle, etc.) a été guidée par :
- **Pertinence pédagogique**
- **Sobriété énergétique**
- **Clarté de la chaîne de traitement**
- **Explicabilité des choix IA**

---
