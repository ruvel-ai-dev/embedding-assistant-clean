import os
import json
import tempfile
import zipfile
from io import BytesIO
from flask import Flask, request, jsonify, send_from_directory, send_file
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

# ── Azure Settings ──
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = "resources"
AZURE_BLOB_BASE_URL = f"https://embeddingassistantfiles.blob.core.windows.net/{AZURE_CONTAINER_NAME}/"

# ── System Prompt ──
SYSTEM_PERSONA = """You are a professional AI assistant designed to help academic staff at the University of Greenwich embed employability skills into their courses.

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

Limit your responses to 200 words excluding download links and pathway suggestions.
"""

# ── Load document index ──
try:
    VECTOR_INDEX = FAISS.load_local("faiss_index", OpenAIEmbeddings(), allow_dangerous_deserialization=True)
    QA_CHAIN = RetrievalQA.from_chain_type(llm=ChatOpenAI(model="gpt-4-1106-preview"), retriever=VECTOR_INDEX.as_retriever())
    print("✅ FAISS document index loaded")
except Exception as e:
    print(f"⚠️ Could not load FAISS document index: {e}")
    VECTOR_INDEX = None
    QA_CHAIN = None

# ── Load pathway index ──
try:
    PATHWAY_INDEX = FAISS.load_local("pathways_index", OpenAIEmbeddings(), allow_dangerous_deserialization=True)
    print("✅ pathways_index loaded")
except Exception as e:
    print(f"⚠️ Could not load pathways_index: {e}")
    PATHWAY_INDEX = None


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
        gpt_resp = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": SYSTEM_PERSONA},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500
        )
        answer = gpt_resp.choices[0].message.content
        file_links = []

    matched_pathways = match_pathways(user_message)

    return jsonify({
        "reply": answer,
        "downloads": file_links,
        "pathways": matched_pathways
    })


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


def match_pathways(user_input):
    if not PATHWAY_INDEX:
        return []
    results = []
    try:
        docs = PATHWAY_INDEX.similarity_search(user_input, k=5)
        for doc in docs:
            md = doc.metadata
            results.append({
                "title": md.get("title", ""),
                "description": md.get("description", ""),
                "url": md.get("url", "")
            })
    except Exception as e:
        print(f"⚠️ Pathway search failed: {e}")
    return results


@app.route("/download_zip", methods=["POST"])
def download_zip():
    data = request.get_json()
    files = data.get("files", [])
    pathways = data.get("pathways", [])

    if not isinstance(files, list):
        return jsonify({"error": "No files provided"}), 400

    try:
        blob_service = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(AZURE_CONTAINER_NAME)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Document files from Azure
            for fname in files:
                path = os.path.join(tmpdir, fname)
                with open(path, "wb") as f:
                    f.write(container.get_blob_client(fname).download_blob().readall())

            # Add pathways into a text file
            if pathways:
                with open(os.path.join(tmpdir, "matched_pathways.txt"), "w", encoding="utf-8") as f:
                    for p in pathways:
                        f.write(f"{p['title']}\n{p['description']}\n{p['url']}\n\n")

            # Create ZIP
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for fname in files:
                    zipf.write(os.path.join(tmpdir, fname), arcname=fname)
                if pathways:
                    zipf.write(os.path.join(tmpdir, "matched_pathways.txt"), arcname="matched_pathways.txt")

            zip_buffer.seek(0)
            return send_file(zip_buffer, as_attachment=True, download_name="selected_resources.zip")

    except Exception as e:
        print(f"❌ ZIP creation failed: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
