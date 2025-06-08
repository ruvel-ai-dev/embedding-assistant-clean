import os
import json
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

# ── Load environment variables ──
load_dotenv()

app = Flask(__name__, static_folder="static")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Azure Storage Settings ──
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = "resources"
AZURE_BLOB_BASE_URL = f"https://embeddingassistantfiles.blob.core.windows.net/{AZURE_CONTAINER_NAME}/"

# ── System Prompt ──
SYSTEM_PERSONA = """
You are a professional AI assistant designed to help academic staff at the University of Greenwich embed employability skills into their courses.

Use British English at all times. Keep answers clear, practical, and supportive. Avoid American spellings, overly technical jargon, or speculative advice.

Always try to:
- Reference relevant uploaded documents
- Suggest appropriate career development pathways
- Include download links when matching files are available
- Structure your answers with bullet points or headings when helpful

Do not:
- Invent facts not contained in the documents or pathways
- Offer legal or medical advice
- Use emojis or casual slang

You are familiar with UK Higher Education policies, career services, graduate employability strategies, and industry expectations.
"""

# ── Load FAISS vector index ──
try:
    VECTOR_INDEX = FAISS.load_local("faiss_index",
                                    OpenAIEmbeddings(),
                                    allow_dangerous_deserialization=True)
    QA_CHAIN = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model="gpt-3.5-turbo"),
        retriever=VECTOR_INDEX.as_retriever())
    print("✅ FAISS vector store loaded")
except Exception as e:
    print(f"⚠️ Could not load FAISS vector store: {e}")
    VECTOR_INDEX = None
    QA_CHAIN = None

# ── Load pathway metadata ──
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

    if QA_CHAIN:
        answer = QA_CHAIN.run(user_message)
        file_links = get_links_with_summaries(user_message)
    else:
        gpt_resp = client.chat.completions.create(model="gpt-3.5-turbo",
                                                  messages=[{
                                                      "role":
                                                      "system",
                                                      "content":
                                                      SYSTEM_PERSONA
                                                  }, {
                                                      "role":
                                                      "user",
                                                      "content":
                                                      user_message
                                                  }])
        answer = gpt_resp.choices[0].message.content
        file_links = []

    matched_pathways = match_pathways(user_message)

    return jsonify({
        "reply": answer,
        "downloads": file_links,
        "pathways": matched_pathways
    })


# 🔍 Generate download links + LLM-generated summaries
def get_links_with_summaries(query):
    results = []
    seen = set()
    try:
        docs = VECTOR_INDEX.similarity_search(query, k=6)
        for doc in docs:
            fname = os.path.basename(doc.metadata.get("source", ""))
            summary = doc.metadata.get("summary", "")
            if fname and fname not in seen:
                seen.add(fname)
                results.append({
                    "name": fname,
                    "url": f"{AZURE_BLOB_BASE_URL}{fname}",
                    "summary": summary
                })
    except Exception as e:
        print(f"⚠️ Failed to fetch summary metadata: {e}")
    return results


# ✅ Pathway matcher
def match_pathways(user_input):
    matches = []
    for entry in PATHWAYS:
        combined_text = (entry.get("title", "") + " " +
                         entry.get("description", "")).lower()
        if any(kw in user_input for kw in entry.get("keywords", [])) or any(
                word in combined_text for word in user_input.split()):
            matches.append({
                "title": entry["title"],
                "description": entry["description"],
                "url": entry["url"]
            })
    return matches


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)