@echo off

echo 📦 Création de l'environnement virtuel (.venv)...
python -m venv .venv

echo 🚀 Activation de l'environnement...
call .venv\Scripts\activate

echo 📚 Installation des dépendances...
pip install --upgrade pip
pip install fastapi uvicorn pydantic langchain langchain-community ollama scikit-learn codecarbon tqdm torch transformers sentence-transformers faiss-cpu

echo 🤖 Téléchargement du modèle Mistral avec Ollama...
ollama pull mistral

echo ✅ Environnement prêt !
set /p start=Souhaitez-vous lancer frontend et backend ? (y/n) 
if /i "%start%"=="y" (
    echo 🚀 Lancement...
    start cmd /k "cd frontend && npm install && npm run dev"
    .venv\Scripts\python.exe -m uvicorn app:app --reload
) else (
    echo ℹ️ Lancez manuellement avec :
    echo Frontend : cd frontend && npm run dev
    echo Backend  : .venv\Scripts\activate && python -m uvicorn app:app --reload
)