import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__, static_folder="static")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ✅ Resource links for file suggestions
resources = {
    "cv": [{
        "name": "CV Template",
        "url": "/static/cv-template.pptx"
    }, {
        "name": "Employability Checklist",
        "url": "/static/checklist.pdf"
    }],
    "cover letter": [{
        "name": "Cover Letter Template",
        "url": "/static/cover-letter.docx"
    }]
}


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/ask", methods=["POST"])
def ask_gpt():
    data = request.get_json()
    user_message = data.get("message")

    response = client.chat.completions.create(model="gpt-3.5-turbo",
                                              messages=[{
                                                  "role": "user",
                                                  "content": user_message
                                              }])

    answer = response.choices[0].message.content

    # ✅ Match keywords to file suggestions
    matched = []
    for keyword, files in resources.items():
        if keyword in user_message.lower():
            matched.extend(files)

    return jsonify({"reply": answer, "resources": matched})


@app.route('/static/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
