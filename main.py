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

SYSTEM_PERSONA = """You are an AI assistant helping academic staff embed employability skills into their courses at the University of Greenwich.
Be practical, supportive, and link to the provided resources when appropriate."""

# ── Load known resource files (PDF, PPTX, DOCX) ──
resources = {
    "cv": ["cv-template.pptx"],
    "cover letter": ["cover-letter.docx"],
    "checklist": ["checklist.pdf"]
}

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

# ── Load pathway data ──
try:
    with open("pathways.json", "r") as f:
        PATHWAYS = json.load(f)
    print("✅ Pathways loaded")
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

    use_vector = any(word in user_message for word in ["cv", "checklist", "cover letter", "template", "document", "ppt", "doc", "pdf"])

    if use_vector and QA_CHAIN:
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

    matched_resources = []
    for keyword, files in resources.items():
        if keyword in user_message:
            matched_resources.extend(files)

    matched_pathways = match_pathways(user_message)

    return jsonify({
        "reply": answer,
        "resources": matched_resources,
        "pathways": matched_pathways
    })

def match_pathways(user_input):
    results = []
    for entry in PATHWAYS:
        if any(keyword in user_input for keyword in entry["keywords"]):
            results.append({
                "title": entry["title"],
                "description": entry["description"],
                "url": entry["url"]
            })
    return results

# ── Local run only for Replit testing ──
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

