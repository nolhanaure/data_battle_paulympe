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

app = FastAPI(title="RAG for Patent Education System with Ollama & LangChain")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000","http://localhost:5173","http://localhost:8000"],
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
        response = ollama.generate(model='mistral', prompt=prompt, options={"server": "http://host.docker.internal:11434"})

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
        "Generate one and only one multiple-choice exam question",
        "Create one and only one challenging open-ended exam question",
        "Produce an unique legally relevant exam question",
        "Write an unique scenario-based question in patent law"
    ]
    formulation = random.choice(formulations)

    prompt = f"""
-- START OF CONTEXT (official documents and exam materials) --
{context}
-- END OF CONTEXT --

Generate one and only one concise question in European patent law on the topic '{category}'. {formulation}.
Do not give the answer. Only return the question and ensure you generate only one question.
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
        "Generate one and only one multiple-choice exam question",
        "Create one and only one open-ended scenario-based question",
        "Generate a realistic legal exam question in European patent law"
    ]
    formulation = random.choice(formulations)

    prompt = f"""
-- CONTEXT: European patent law documents (EPC, PCT, Guidelines, Exams) --
{context}
-- END CONTEXT --

{formulation}. Do not give any answer. Only return one question, no more.
"""

    try:
        question = ollama_llm.predict(prompt)
        return {"question": question.strip()}
    except Exception as e:
        return {"error": str(e)}


#Re-ranking pour l'analyse de réponses on donne plus d'importance aux documents prochent de la question mais on booste ceux qui sont proche des deux
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
You are a legal examiner specialized in European Patent Law (EPC). Your role is to assess student answers in the context of European patent law exams. You are provided with official legal texts and exam questions with model answers to help you assess.

-- CONTEXT FROM OFFICIAL LEGAL TEXTS (EPC, PCT, GUIDELINES) --
{law_context}
-- END OF LEGAL CONTEXT --

-- EXAMPLES OF PREVIOUS EXAM QUESTIONS WITH ANSWERS --
{exam_context}
-- END OF EXAMPLES --

-- STUDENT INPUT --
Question: {request.user_question}
Answer: {request.user_answer}
-- END OF STUDENT INPUT --

-- TASK --
Evaluate the student's answer in the style of a professional exam corrector.



If this is a multiple-choice question,determine first whether the student's selected option is legally correct, note that the student **don't have** to provide a justification — your role is to confirm or refute the selected option **based on legal accuracy**, and provide the correct reasoning.

For others type of questions, your response must include:

1. ✅ - **Legal Evaluation**: Is the selected answer correct? Clearly state whether it is right or wrong and why.
2. 💬 - **Constructive Feedback**: If the answer is wrong or incomplete, explain what the student missed and how to improve.
3. 📝 - **Model Answer**: Provide a complete and legally sound answer as expected in an exam.
4. 📚 - **Cited Legal Basis**: Quote specific EPC or PCT articles, rules or Guidelines that support your evaluation.

If the student's answer is empty or irrelevant, just do Model answer and Cited Legal Basis.

**Keep your analysis rigorous but helpful. You are both a pedagogue and a jurist**.
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
You are a legal expert in European patent law. Based on the question and the legal documents and previous exams below, provide only a legally sound model answer and the relevant legal basis.

-- CONTEXT FROM OFFICIAL LEGAL TEXTS (EPC, PCT, GUIDELINES) --
{law_context}
-- END OF LEGAL CONTEXT --

-- PREVIOUS EXAM EXAMPLES --
{exam_context}
-- END OF EXAMPLES --

-- STUDENT INPUT (NO ANSWER GIVEN) --
Question: {request.user_question}
-- END OF INPUT --

Provide:
📝 Model Answer
📚 Legal Basis
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
