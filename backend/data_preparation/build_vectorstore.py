import os
import re
import json
import torch
from pathlib import Path
from tqdm import tqdm
from langchain.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
import faiss
import numpy as np
from codecarbon import EmissionsTracker
tracker = EmissionsTracker(project_name="Creation of index")

torch.cuda.empty_cache()
tracker.start()
# === CONFIGURATION ===
QA_JSON_PATH = "qa_dataset.json"
LEGAL_TEXTS_DIR = Path("Official_Legal_Publications_TXT")
EPC_SUBDIR = LEGAL_TEXTS_DIR / "EPC"
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"

# === WRAPPER POUR LE BATCHING ===
class BatchedEmbeddingModel:
    def __init__(self, base_model, batch_size=8):
        self.base_model = base_model
        self.batch_size = batch_size
  
    def embed_documents(self, texts):
        embeddings = []
        for i in tqdm(range(0, len(texts), self.batch_size), desc="Embedding batches"):
            batch = texts[i:i + self.batch_size]
            with torch.no_grad():
                batch_embeddings = self.base_model.embed_documents(batch)
            embeddings.extend(batch_embeddings)
            torch.cuda.empty_cache()
        return embeddings

    def embed_query(self, text):
        return self.base_model.embed_query(text)

# === INITIALISATION DU MODELE D'EMBEDDING ===
device = "cuda" if torch.cuda.is_available() else "cpu"
base_model = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME,
    model_kwargs={"device": device}
)
embedding_model = BatchedEmbeddingModel(base_model)
print(f"\u2705 Modèle d'embedding chargé sur : {device}")

# === CHARGEMENT DES QCM AU FORMAT JSON ===
def load_qa_documents(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    documents = []
    for item in data:
        question = item.get("question", "").strip()
        answer = item.get("answer", "").strip()
        page_content = f"Question:\n{question}\n\nAnswer:\n{answer}"
        documents.append(Document(
            page_content=page_content,
            metadata={"type": "exam", "source": os.path.basename(path)}
        ))
    return documents


# === PARSEURS SPECIFIQUES A CHAQUE TYPE DE FICHIER ===
def extract_blocks_by_marker(text, pattern):
    matches = list(re.finditer(pattern, text, flags=re.MULTILINE))
    blocks = []
    for i in range(len(matches)):
        start = matches[i].end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        title = matches[i].group(0).strip()
        content = text[start:end].strip()
        if len(content.split()) > 10:
            blocks.append((title, content))
    return blocks

def parse_pct(text):
    pattern = r"^(Article|Rule)\s+\d+[a-zA-Z0-9\(\)]*\s*$"
    blocks = extract_blocks_by_marker(text, pattern)
    docs = []
    for title, content in blocks:
        section = "rule" if title.lower().startswith("rule") else "article"
        docs.append(Document(
            page_content=f"{title}\n{content}",
            metadata={"type": "treaty", "source": "pct.txt", "section": section, "id": title}
        ))
    return docs

def parse_guidelines(text):
    pattern = r"Part\s+[A-H]\s+–\s+Chapter\s+[IVXLCDM0-9\-]+"
    blocks = extract_blocks_by_marker(text, pattern)
    docs = []
    for title, content in blocks:
        docs.append(Document(
            page_content=f"{title}\n{content}",
            metadata={"type": "guideline", "source": "guidelines.txt", "id": title}
        ))
    return docs

def parse_epc_file(text, source, section, pattern):
    blocks = extract_blocks_by_marker(text, pattern)
    docs = []
    for title, content in blocks:
        docs.append(Document(
            page_content=f"{title}\n{content}",
            metadata={"type": "law", "source": source, "section": section, "id": title, "lang": "en"}
        ))
    return docs

# === PARSEUR GLOBAL ===
def parse_legal_file(file_path):
    text = Path(file_path).read_text(encoding="utf-8")
    fname = file_path.name

    if fname == "2-PCT_wipo-pub-274-2024-en-patent-cooperation-treaty.txt":
        return parse_pct(text)
    elif fname == "3-en-epc-guidelines-2024-hyperlinked.txt":
        return parse_guidelines(text)
    elif fname == "Convention_EPC.txt":
        return parse_epc_file(text, "epc_convention", "article", r"^Article\s+\d+\s*$")
    elif fname == "Implementing_regulations.txt":
        return parse_epc_file(text, "epc_regulations", "rule", r"^Rule\s+\d+\s*$")
    elif fname == "protocol_application_article_69.txt":
        return parse_epc_file(text, "epc_protocol_69", "article", r"^Article\s+\d+\s*$")
    elif fname == "protocol_centralisation.txt":
        return parse_epc_file(text, "epc_protocol_centralisation", "section", r"^Section\s+[IVXLCDM]+\s*$")
    elif fname == "protocol_jurisdiction_recognition.txt":
        return parse_epc_file(text, "epc_protocol_jurisdiction", "article", r"^Article\s+\d+\s*$")
    elif fname == "rules_of_procedure_board_of_appeal_enlarged.txt":
        return parse_epc_file(text, "epc_rpeba", "article", r"^Article\s+\d+\s*$")
    elif fname == "rules_of_procedure_board_of_appeal.txt":
        return parse_epc_file(text, "epc_rpboa", "article", r"^Article\s+\d+\s*$")
    elif fname == "EPC_rules_relating_to_fees.txt":
        return parse_epc_file(text, "epc_fees", "article", r"^Article\s+\d+\s*$")
    else:
        return []

# === PIPELINE PRINCIPAL ===
def build_vectorstore():
    print("\n[1] Chargement des questions/réponses...")
    qa_documents = load_qa_documents(QA_JSON_PATH)

    print("[2] Chargement des textes légaux...")
    legal_documents = []

    for file_path in list(LEGAL_TEXTS_DIR.glob("*.txt")) + list(EPC_SUBDIR.glob("*.txt")):
        docs = parse_legal_file(file_path)
        legal_documents.extend(docs)
        print(f"  - {file_path.name}: {len(docs)} documents")

    all_documents = qa_documents + legal_documents
    print(f"\nTotal documents à indexer : {len(all_documents)}")

    print("\n[3] Construction du vectorstore FAISS (batch GPU-safe)...")
    texts = [doc.page_content for doc in all_documents]
    metadatas = [doc.metadata for doc in all_documents]
    embeddings = embedding_model.embed_documents(texts)

    text_embeddings = list(zip(texts, embeddings))
    vectorstore = FAISS.from_embeddings(
        text_embeddings=text_embeddings,
        embedding=base_model,
        metadatas=metadatas
    )
    vectorstore.save_local("faiss_index")
   
    print("\n✅ Index sauvegardé dans le dossier 'faiss_index'.")

if __name__ == "__main__":
    build_vectorstore()
    tracker.stop()
