#!/bin/bash

echo "📦 Création de l'environnement virtuel (.venv)..."
python3 -m venv .venv

echo "🚀 Activation de l'environnement..."
source .venv/bin/activate

echo "📚 Installation des dépendances..."
pip install --upgrade pip
pip install fastapi uvicorn pydantic langchain langchain-community ollama scikit-learn codecarbon tqdm torch transformers sentence-transformers faiss-cpu

echo "🤖 Téléchargement du modèle Mistral avec Ollama..."
ollama pull mistral

echo "✅ Environnement prêt !"
read -p "Souhaitez-vous lancer le frontend (npm run dev) et le backend (uvicorn) maintenant ? (y/n) " answer
if [[ "$answer" == "y" ]]; then
  echo "🚀 Lancement du frontend et du backend..."
  # Lancer le frontend en tâche de fond
  (cd frontend && npm install && npm run dev) &

  # Lancer le backend avec l’interpréteur du venv
  .venv/bin/python3.11 -m uvicorn app:app --reload
else
  echo "ℹ️ Vous pouvez lancer manuellement avec :"
  echo "Frontend : cd frontend && npm run dev"
  echo "Backend  : source .venv/bin/activate && python3.11 -m uvicorn app:app --reload"
fi
