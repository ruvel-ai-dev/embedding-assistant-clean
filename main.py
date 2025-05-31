import os, json
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__, static_folder="static")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ── Persona / system prompt ─────────────────────────────────────────
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

# ── Static downloadable resources ───────────────────────────────────
resources = {
    "cv": [
        {"name": "CV Template", "url": "/static/cv-template.pptx", "kind": "file"},
        {"name": "Employability Checklist", "url": "/static/checklist.pdf", "kind": "file"}
    ],
    "cover letter": [
        {"name": "Cover Letter Template", "url": "/static/cover-letter.docx", "kind": "file"}
    ]
}

# ── Load pathways.json (if present) ─────────────────────────────────
try:
    with open("pathways.json", "r", encoding="utf-8") as f:
        PATHWAYS = json.load(f)
except Exception as e:
    print("⚠️  Pathways JSON error →", e)
    PATHWAYS = []

def find_matching_pathways(query: str, limit: int = 5):
    q = query.lower()
    matches = []
    for p in PATHWAYS:
        if any(kw in q for kw in p.get("keywords", [])):
            matches.append({
                "name": p["title"],
                "url":  p["url"],
                "info": p.get("description", ""),
                "kind": "pathway"
            })
        if len(matches) >= limit:
            break
    return matches

# ── Flask routes ───────────────────────────────────────────────────
@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/ask", methods=["POST"])
def ask_gpt():
    data = request.get_json()
    user_message = data.get("message", "")

    # 1. ChatGPT answer with persona context
    gpt_resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PERSONA},
            {"role": "user",   "content": user_message}
        ]
    )
    answer = gpt_resp.choices[0].message.content

    # 2. Match static files
    matched = []
    for kw, files in resources.items():
        if kw in user_message.lower():
            matched.extend(files)

    # 3. Match pathways
    matched.extend(find_matching_pathways(user_message))

    return jsonify({"reply": answer, "resources": matched})

@app.route("/static/<path:filename>")
def static_files(filename):
    return app.send_static_file(filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
    


