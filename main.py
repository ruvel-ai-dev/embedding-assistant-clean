# Filename: main.py
# Flask app with Replit + Azure Blob + GPT integration

import os
import json
from flask import Flask, request, jsonify
from openai import OpenAI
from azure.storage.blob import BlobServiceClient

# ── Flask + OpenAI setup ────────────────────────────────────────────
app = Flask(__name__, static_folder="static")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ── Azure Blob Storage setup ────────────────────────────────────────
AZURE_STORAGE_CONNECTION_STRING = os.environ.get(
    "AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = "resources"

try:
    blob_service_client = BlobServiceClient.from_connection_string(
        AZURE_STORAGE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(
        AZURE_CONTAINER_NAME)
except Exception as e:
    print("⚠️ Azure Blob error →", e)
    container_client = None

# ── Persona prompt ──────────────────────────────────────────────────
SYSTEM_PERSONA = """
You are the “Greenwich Employability Embedding Assistant”, an employability adviser for the
Employability & Apprenticeship Directorate at the University of Greenwich (UK) with extensive experience.
Audience: academic staff (lecturers, module leaders, tutors) who want to embed
employability skills and resources into their curriculum.

Speaking style:
• British English / UK spelling only and academic-friendly tone.
• Professional and wholly relevant with specifics.
• Concise and clear.

Never mention internal implementation details (e.g., JSON, code).
"""


# ── Helper: fetch matching files from Azure ─────────────────────────
def get_blob_resources(user_query):
    if not container_client:
        return []

    keywords = [
        "cv", "cover letter", "checklist", "template", "guide", "interview",
        "employability"
    ]
    query_lower = user_query.lower()

    try:
        blobs = container_client.list_blobs()
        matches = []

        for blob in blobs:
            blob_name = blob.name.lower()
            if any(kw in query_lower or kw in blob_name for kw in keywords):
                matches.append({
                    "name": blob.name,
                    "url":
                    f"https://{blob_service_client.account_name}.blob.core.windows.net/{AZURE_CONTAINER_NAME}/{blob.name}",
                    "kind": "file"
                })
        return matches
    except Exception as e:
        print("⚠️ Error listing blobs →", e)
        return []


# ── Load pathways.json (if available) ───────────────────────────────
try:
    with open("pathways.json", "r", encoding="utf-8") as f:
        PATHWAYS = json.load(f)
except Exception as e:
    print("⚠️ Pathways JSON error →", e)
    PATHWAYS = []


def find_matching_pathways(query: str, limit: int = 5):
    q = query.lower()
    matches = []
    for p in PATHWAYS:
        if any(kw in q for kw in p.get("keywords", [])):
            matches.append({
                "name": p["title"],
                "url": p["url"],
                "info": p.get("description", ""),
                "kind": "pathway"
            })
        if len(matches) >= limit:
            break
    return matches


# ── Routes ──────────────────────────────────────────────────────────
@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/ask", methods=["POST"])
def ask_gpt():
    data = request.get_json()
    user_message = data.get("message", "")

    # GPT response
    gpt_resp = client.chat.completions.create(model="gpt-3.5-turbo",
                                              messages=[{
                                                  "role":
                                                  "system",
                                                  "content":
                                                  SYSTEM_PERSONA
                                              }, {
                                                  "role": "user",
                                                  "content": user_message
                                              }])
    answer = gpt_resp.choices[0].message.content

    # Find resources and pathways
    matched_files = get_blob_resources(user_message)
    matched_pathways = find_matching_pathways(user_message)

    return jsonify({
        "reply": answer,
        "resources": matched_files + matched_pathways
    })


# Static file serving (if needed)
@app.route("/static/<path:filename>")
def static_files(filename):
    return app.send_static_file(filename)


@app.errorhandler(404)
def not_found(e):
    return app.send_static_file("index.html")


# Optional route for testing Azure connection
@app.route("/test-azure")
def test_azure():
    if not container_client:
        return jsonify({"error": "Azure connection failed."}), 500
    try:
        blobs = container_client.list_blobs()
        file_names = [blob.name for blob in blobs]
        return jsonify({"files": file_names})
    except Exception as e:
        return jsonify({"error": str(e)})


# ── Replit-compatible server start ──────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=True)
