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
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ── Azure Storage Settings ──
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = "resources"
AZURE_BLOB_BASE_URL = f"https://embeddingassistantfiles.blob.core.windows.net/{AZURE_CONTAINER_NAME}/"

# ── System Prompt ──
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

    # Answer query using FAISS vector store if available
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

    # Dynamically find matching files
    file_links = find_document_links(user_message)

    # Pathway matches
    matched_pathways = match_pathways(user_message)

    return jsonify({
        "reply": answer,
        "downloads": file_links,
        "pathways": matched_pathways
    })

def find_document_links(user_input):
    matched_files = []

    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)
        blob_list = container_client.list_blobs()

        for blob in blob_list:
            filename = blob.name
            if any(word in filename.lower() for word in user_input.lower().split()):
                matched_files.append({
                    "name": filename,
                    "url": f"{AZURE_BLOB_BASE_URL}{filename}"
                })
    except Exception as e:
        print(f"⚠️ Azure file match failed: {e}")

    return matched_files

def match_pathways(user_input):
    matches = []
    for entry in PATHWAYS:
        combined_text = (entry.get("title", "") + " " + entry.get("description", "")).lower()
        if any(kw in user_input for kw in entry.get("keywords", [])) or any(word in combined_text for word in user_input.split()):
            matches.append({
                "title": entry["title"],
                "description": entry["description"],
                "url": entry["url"]
            })
    return matches

# ── Local development only ──
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

