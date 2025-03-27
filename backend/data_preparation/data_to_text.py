import fitz  # PyMuPDF
import os
from docx import Document

# Dossiers à traiter récursivement pour les PDFs
input_dirs = [
    "data_base/EPAC Exams",
    "data_base/EQE Exams",
    "data_base/Official Legal Publications"
]

# Fichier Word unique
docx_files = [
    "data_base/Questions Sup OEB.docx"
]

# Dossier racine pour les fichiers TXT
output_root = "txt_output"

def clean_text(text):
    text = text.replace('\xa0', ' ')
    text = text.replace('\n', ' ')
    text = ' '.join(text.split())
    return text

def convert_pdf_to_txt(pdf_path, output_path):
    try:
        doc = fitz.open(pdf_path)
        all_text = ""
        for page in doc:
            text = page.get_text()
            all_text += clean_text(text) + "\n"
        doc.close()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(all_text)

        print(f"[✔] PDF : {pdf_path} → {output_path}")
    except Exception as e:
        print(f"[✘] Erreur avec {pdf_path} : {e}")

def convert_docx_to_txt(docx_path, output_path):
    try:
        doc = Document(docx_path)
        all_text = ""
        for para in doc.paragraphs:
            all_text += clean_text(para.text) + "\n"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(all_text)

        print(f"[✔] DOCX : {docx_path} → {output_path}")
    except Exception as e:
        print(f"[✘] Erreur avec {docx_path} : {e}")

# Conversion des fichiers PDF
for input_dir in input_dirs:
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                relative_path = os.path.relpath(pdf_path, input_dir)
                base_name = os.path.splitext(relative_path)[0] + ".txt"
                output_path = os.path.join(output_root, os.path.basename(input_dir), base_name)
                convert_pdf_to_txt(pdf_path, output_path)

# Conversion du fichier DOCX
for docx_path in docx_files:
    relative_path = os.path.splitext(os.path.relpath(docx_path, "data_base"))[0] + ".txt"
    output_path = os.path.join(output_root, relative_path)
    convert_docx_to_txt(docx_path, output_path)
