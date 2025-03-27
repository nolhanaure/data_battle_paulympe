import json
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama
from sklearn.metrics.pairwise import cosine_similarity
from langchain.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.llms.base import LLM
from codecarbon import EmissionsTracker
import subprocess
tracker = EmissionsTracker(project_name="PatentRAG")

app = FastAPI(title="RAG pour le système d'éducation aux brevets avec Ollama & LangChain")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://localhost:8000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

#########################################
# 1. Charger le vector store avec BGE-M3
#########################################
embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

vectorstore = FAISS.load_local(
    "faiss_index",
    embedding_model,
    allow_dangerous_deserialization=True
)

print(f"[INFO] Index FAISS chargé avec {len(vectorstore.docstore._dict)} documents.")

#########################################
# 2. Définir un LLM personnalisé utilisant Ollama
#########################################
class OllamaLLM(LLM):
    @property
    def _llm_type(self) -> str:
        return "ollama"

    def _call(self, prompt: str, stop: list = None) -> str:
        response = ollama.generate(model='mistral', prompt=prompt)

        try:
            return response.get("response", "")
        except Exception:
            return str(response)

    def predict(self, prompt: str, stop: list = None) -> str:
        return self._call(prompt, stop=stop)

ollama_llm = OllamaLLM()


#########################################
# 3. Endpoints FastAPI
#########################################
@app.get("/generate-question")
def generate_question(category: str):
    tracker.start()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 60})
    all_docs = retriever.get_relevant_documents(f"about {category}")
    random.shuffle(all_docs)

    # Sélection majoritaire d'examens
    exam_docs = [doc for doc in all_docs if doc.metadata.get("type", "").lower() == "exam"][:30]
    # Ajouter d'autres types pour enrichir le contexte
    other_docs = [
        doc for doc in all_docs
        if doc.metadata.get("type", "").lower() in ["law", "treaty", "guideline"]
    ][:15]

    selected_docs = exam_docs + other_docs
    if not selected_docs:
        selected_docs = all_docs[:20]

    context = "\n\n".join([doc.page_content[:600] for doc in selected_docs])

    formulations = [
        "Générez une seule question d'examen à choix multiples",
        "Créez une seule question d'examen ouverte et stimulante",
        "Produisez une question d'examen unique ayant une pertinence juridique",
        "Rédigez une question unique basée sur un scénario en droit des brevets"
    ]
    formulation = random.choice(formulations)

    prompt = f"""
-- DÉBUT DU CONTEXTE (documents officiels et supports d'examen) --
{context}
-- FIN DU CONTEXTE --

En français, générez une seule question concise en droit européen des brevets sur le thème '{category}'. {formulation}.
Ne fournissez pas la réponse. Retournez uniquement la question et assurez-vous d'en générer une seule.
"""

    try:
        question = ollama_llm.predict(prompt)
        tracker.start()
        return {"question": question.strip()}
    except Exception as e:
        return {"error": str(e)}

    
# === Génération de question aléatoire ===
@app.get("/generate-random-question")
def generate_random_question():
    retriever = vectorstore.as_retriever(search_kwargs={"k": 60})
    all_docs = retriever.get_relevant_documents("")
    random.shuffle(all_docs)

    exam_docs = [doc for doc in all_docs if doc.metadata.get("type") == "exam"][:30]
    other_docs = [doc for doc in all_docs if doc.metadata.get("type") in ["law", "treaty", "guideline"]][:15]

    selected_docs = exam_docs + other_docs
    context = "\n\n".join([doc.page_content[:600] for doc in selected_docs])

    formulations = [
        "Générez une seule question d'examen à choix multiples",
        "Créez une seule question basée sur un scénario ouvert",
        "Générez une question d'examen réaliste en droit européen des brevets"
    ]
    formulation = random.choice(formulations)

    prompt = f"""
-- CONTEXTE : Documents en droit européen des brevets (EPC, PCT, Directives, Examens) --
{context}
-- FIN DU CONTEXTE --

{formulation}. En français.Ne fournissez aucune réponse. Retournez uniquement une question, et seulement une.
"""

    try:
        question = ollama_llm.predict(prompt)
        return {"question": question.strip()}
    except Exception as e:
        return {"error": str(e)}


# Re-ranking pour l'analyse de réponses : on donne plus d'importance aux documents proches de la question mais on booste ceux qui sont proches des deux
def rerank_docs(question, answer, vectorstore, embedding_model, top_k_question=20, top_k_final=10):
    # Embedding des requêtes
    q_vec = embedding_model.embed_query(question)
    a_vec = embedding_model.embed_query(answer)

    # Récupération initiale par la question
    initial_docs = vectorstore.similarity_search(question, k=top_k_question)

    # Pour chaque doc, calcul de similarité avec Q et A
    scored_docs = []
    for doc in initial_docs:
        doc_vec = embedding_model.embed_query(doc.page_content)
        sim_q = cosine_similarity([q_vec], [doc_vec])[0][0]
        sim_a = cosine_similarity([a_vec], [doc_vec])[0][0]

        # Score mixte pondéré : plus important de coller à la question
        final_score = 0.7 * sim_q + 0.3 * sim_a
        scored_docs.append((final_score, doc))

    # Tri + sélection top-k
    top_docs = [doc for score, doc in sorted(scored_docs, reverse=True)[:top_k_final]]
    return top_docs


class AnalyzeRequest(BaseModel):
    category: str
    user_question: str
    user_answer: str

@app.post("/analyze-answer")
def analyze_answer(request: AnalyzeRequest):
    top_docs = rerank_docs(
        question=request.user_question,
        answer=request.user_answer,
        vectorstore=vectorstore,
        embedding_model=embedding_model,
        top_k_question=20,
        top_k_final=10
    )

    law_docs = [doc for doc in top_docs if doc.metadata.get("type") in ["law", "treaty", "guideline"]]
    exam_docs = [doc for doc in top_docs if doc.metadata.get("type") == "exam"]

    law_context = "\n\n".join([doc.page_content[:1000] for doc in law_docs])
    exam_context = "\n\n".join([doc.page_content[:1000] for doc in exam_docs])

    prompt = f"""
Vous êtes un examinateur juridique spécialisé en droit européen des brevets (EPC). Votre rôle est d'évaluer les réponses des étudiants dans le contexte des examens en droit européen des brevets. Vous disposez de textes juridiques officiels ainsi que de questions d'examen avec leurs réponses modèles pour vous aider dans votre évaluation.

-- CONTEXTE ISSU DES TEXTES JURIDIQUES OFFICIELS (EPC, PCT, DIRECTIVES) --
{law_context}
-- FIN DU CONTEXTE JURIDIQUE --

-- EXEMPLES DE QUESTIONS D'EXAMENS PRÉCÉDENTS AVEC LEURS RÉPONSES --
{exam_context}
-- FIN DES EXEMPLES --

-- ENTRÉE DE L'ÉTUDIANT --
Question : {request.user_question}
Réponse : {request.user_answer}
-- FIN DE L'ENTRÉE DE L'ÉTUDIANT --

-- TÂCHE --
Évaluez la réponse de l'étudiant dans le style d'un correcteur d'examens professionnel.

Si c'est une question à choix multiples, déterminez d'abord si l'option sélectionnée par l'étudiant est juridiquement correcte, notez que l'étudiant **n'est pas tenu** de fournir une justification — votre rôle est de confirmer ou infirmer l'option sélectionnée **en vous basant sur la précision juridique**, et de fournir le raisonnement correct.

Pour les autres types de questions, votre réponse doit inclure :

1. ✅ - **Évaluation Juridique** : La réponse sélectionnée est-elle correcte ? Indiquez clairement si elle est juste ou fausse et pourquoi.
2. 💬 - **Retour Constructif** : Si la réponse est incorrecte ou incomplète, expliquez ce qui manque à l'étudiant et comment s'améliorer.
3. 📝 - **Réponse Modèle** : Fournissez une réponse complète et juridiquement solide, telle qu'attendue dans un examen.
4. 📚 - **Fondement Juridique Cité** : Citez des articles, règles ou Directives spécifiques de l'EPC ou du PCT qui étayent votre évaluation.

Si la réponse de l'étudiant est vide ou hors sujet, fournissez uniquement la Réponse Modèle et le Fondement Juridique Cité.

**En français.Gardez votre analyse rigoureuse mais utile. Vous êtes à la fois un pédagogue et un juriste**.
"""
    try:
        response = ollama_llm.predict(prompt)
        return {"feedback": response.strip()}
    except Exception as e:
        return {"error": str(e)}

# === Génération de réponse modèle uniquement ===
class ModelAnswerRequest(BaseModel):
    user_question: str
@app.post("/generate-model-answer")
def generate_model_answer(request: ModelAnswerRequest):
    top_docs = rerank_docs(
        question=request.user_question,
        answer="",  # Pas de réponse étudiante
        vectorstore=vectorstore,
        embedding_model=embedding_model,
        top_k_question=20,
        top_k_final=10
    )

    law_docs = [doc for doc in top_docs if doc.metadata.get("type") in ["law", "treaty", "guideline"]]
    exam_docs = [doc for doc in top_docs if doc.metadata.get("type") == "exam"]

    law_context = "\n\n".join([doc.page_content[:1000] for doc in law_docs])
    exam_context = "\n\n".join([doc.page_content[:1000] for doc in exam_docs])

    prompt = f"""
Vous êtes un expert juridique en droit européen des brevets. À partir de la question, des documents juridiques et des examens précédents ci-dessous, fournissez uniquement une réponse modèle juridiquement solide ainsi que le fondement juridique pertinent.

-- CONTEXTE ISSU DES TEXTES JURIDIQUES OFFICIELS (EPC, PCT, DIRECTIVES) --
{law_context}
-- FIN DU CONTEXTE JURIDIQUE --

-- EXEMPLES D'EXAMENS PRÉCÉDENTS --
{exam_context}
-- FIN DES EXEMPLES --

-- ENTRÉE DE L'ÉTUDIANT (AUCUNE RÉPONSE FOURNIE) --
Question : {request.user_question}
-- FIN DE L'ENTRÉE --

Fournissez :
📝 Réponse Modèle
📚 Fondement Juridique
"""
    try:
        response = ollama_llm.predict(prompt)
        return {"feedback": response.strip()}
    except Exception as e:
        return {"error": str(e)}
    

@app.get("/retrieve")
def retrieve(query: str, k: int = 11):
    docs = vectorstore.similarity_search(query, k=k)

    results = [
        {
            "source": doc.metadata.get("source"),
            "type": doc.metadata.get("type"),
            "excerpt": doc.page_content[:2000]
        }
        for doc in docs
    ]
    return {"results": results}

#########################################
# 4. Lancer l'application
#########################################
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
    tracker.stop()
    print(tracker.emissions)