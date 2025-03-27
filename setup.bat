@echo off
echo 📦 Création de l'environnement virtuel (.venv)...
python -m venv .venv

echo 🚀 Activation de l'environnement...
call .venv\Scripts\activate

echo 📚 Installation des dépendances...
python -m pip install --upgrade pip
pip install fastapi uvicorn pydantic langchain langchain-community ollama scikit-learn codecarbon tqdm torch transformers sentence-transformers faiss-cpu

echo 🤖 Téléchargement du modèle Mistral avec Ollama...
ollama pull mistral

echo ✅ Environnement prêt !

echo ℹ️ Vous pouvez lancer manuellement avec :
echo Frontend : cd frontend && npm install && npm run dev
echo Backend  : call .venv\Scripts\activate && python -m uvicorn app:app --reload
