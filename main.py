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

# ── Azure Blob Storage Settings ──
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

Limit your responses to 200 words excluding download links and pathway suggestions.
"""

# ── Load Document Vector Index ──
try:
    VECTOR_INDEX = FAISS.load_local("faiss_index",
                                    OpenAIEmbeddings(),
                                    allow_dangerous_deserialization=True)
    QA_CHAIN = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model="gpt-3.5-turbo"),  # 🟢 Downgraded to save cost
        retriever=VECTOR_INDEX.as_retriever())
    print("✅ FAISS document index loaded")
except Exception as e:
    print(f"⚠️ Could not load FAISS document index: {e}")
    VECTOR_INDEX = None
    QA_CHAIN = None

# ── Load Pathway Vector Index ──
try:
    PATHWAY_INDEX = FAISS.load_local("pathways_index",
                                     OpenAIEmbeddings(),
                                     allow_dangerous_deserialization=True)
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
            model="gpt-3.5-turbo",  # 🟢 Also changed here
            messages=[{
                "role": "system",
                "content": SYSTEM_PERSONA
            }, {
                "role": "user",
                "content": user_message
            }],
            max_tokens=500)
        answer = gpt_resp.choices[0].message.content
        file_links = []

    matched_pathways = match_pathways(user_message)

    return jsonify({
        "reply": answer,
        "downloads": file_links,
        "pathways": matched_pathways
    })


def get_links_with_summaries(query, top_k: int = 6):
    """Return document links sorted by FAISS score, always including general docs."""
    results = []
    seen = set()

    try:
        # Request scores from FAISS for query-specific results
        ranked_docs = VECTOR_INDEX.similarity_search_with_score(query, k=15)

        # Fetch general docs without filtering by query similarity
        general_pool = VECTOR_INDEX.similarity_search("", k=50)
        general_docs = [
            (doc, float("inf"))
            for doc in general_pool
            if "general" in doc.metadata.get("tags", [])
            or "main" in doc.metadata.get("tags", [])
        ]

        # Combine and sort by score (general docs have score = inf)
        combined = ranked_docs + general_docs
        combined.sort(key=lambda x: x[1])

        for doc, score in combined:
            fname = os.path.basename(doc.metadata.get("source", ""))
            summary = doc.metadata.get("summary", "")
            if fname and fname not in seen:
                seen.add(fname)
                results.append({
                    "name": fname,
                    "url": f"{AZURE_BLOB_BASE_URL}{fname}",
                    "summary": summary,
                    "_score": score,
                    "_is_general": "general" in doc.metadata.get("tags", [])
                    or "main" in doc.metadata.get("tags", [])
                })

        # Trim to top_k then append any missing general docs
        top_results = results[:top_k]
        included = {r["name"] for r in top_results}
        for item in results[top_k:]:
            if item["_is_general"] and item["name"] not in included:
                top_results.append(item)
                included.add(item["name"])

        # Remove helper keys
        for item in top_results:
            item.pop("_score", None)
            item.pop("_is_general", None)

        return top_results

    except Exception as e:
        print(f"⚠️ Failed to fetch summary metadata: {e}")
        return []


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
    if not isinstance(files, list) or not files:
        return jsonify({"error": "No files provided"}), 400

    try:
        blob_service = BlobServiceClient.from_connection_string(
            AZURE_STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(AZURE_CONTAINER_NAME)

        with tempfile.TemporaryDirectory() as tmpdir:
            for fname in files:
                path = os.path.join(tmpdir, fname)
                with open(path, "wb") as f:
                    f.write(
                        container.get_blob_client(
                            fname).download_blob().readall())

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for fname in files:
                    zipf.write(os.path.join(tmpdir, fname), arcname=fname)

            zip_buffer.seek(0)
            return send_file(zip_buffer,
                             as_attachment=True,
                             download_name="selected_resources.zip")

    except Exception as e:
        print(f"❌ ZIP creation failed: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
