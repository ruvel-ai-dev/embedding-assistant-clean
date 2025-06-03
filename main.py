import os
import json
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

load_dotenv()

app = Flask(__name__, static_folder="static")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ── Settings ──
AZURE_BLOB_BASE_URL = "https://embeddingassistantfiles.blob.core.windows.net/resources/"

SYSTEM_PERSONA = """You are an AI assistant helping academic staff embed employability skills into their courses at the University of Greenwich.
Be practical, supportive, and link to the provided resources when appropriate."""

# ── Load FAISS vector index ──
try:
    VECTOR_INDEX = FAISS.load_local("faiss_index", OpenAIEmbeddings(), allow_dangerous_deserialization=True)
    QA_CHAIN = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model="gpt-3.5-turbo"),
        retriever=VECTOR_INDEX.as_retriever()
    )
    print("✅ FAISS vector store loaded")
except Exception as e:
    print(f"⚠️ Could not load FAISS vector store: {e}")
    VECTOR_INDEX = None
    QA_CHAIN = None

# ── Load pathway metadata JSON (static reference for link generation) ──
try:
    with open("pathways.json", "r") as f:
        PATHWAYS = json.load(f)
    print("✅ pathways.json loaded")
except Exception as e:
    print(f"⚠️ Could not load pathways.json: {e}")
    PATHWAYS = []

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route("/ask", methods=["POST"])
def ask_gpt():
    data = request.get_json()
    user_message = data.get("message", "").lower()

    # Use vector store for intelligent QA
    if QA_CHAIN:
        answer = QA_CHAIN.run(user_message)
    else:
        gpt_resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PERSONA},
                {"role": "user", "content": user_message}
            ]
        )
        answer = gpt_resp.choices[0].message.content

    # Match files for download links
    file_links = find_document_links(user_message)

    # Match pathways from metadata
    matched_pathways = match_pathways(user_message)

    return jsonify({
        "reply": answer,
        "downloads": file_links,
        "pathways": matched_pathways
    })

def find_document_links(user_input):
    keywords = ["cv", "checklist", "ppt", "doc", "cover letter", "template"]
    matched_files = []

    # Manually define known files for now
    all_files = [
        "cv-template.pptx.pptx",
        "cover-letter.docx.docx",
        "checklist.pdf.pdf"
    ]

    for file in all_files:
        for keyword in keywords:
            if keyword in user_input.lower() and keyword in file.lower():
                matched_files.append({
                    "name": file,
                    "url": AZURE_BLOB_BASE_URL + file
                })

    return matched_files

def match_pathways(user_input):
    matches = []
    for entry in PATHWAYS:
        text_blob = (entry.get("title", "") + " " + entry.get("description", "")).lower()
        if any(kw in user_input for kw in entry.get("keywords", [])) or any(word in text_blob for word in user_input.split()):
            matches.append({
                "title": entry["title"],
                "description": entry["description"],
                "url": entry["url"]
            })
    return matches

# ── Local run for Replit testing ──
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


