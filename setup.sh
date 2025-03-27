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


