# This version of the code removes the old JSON-based resource loading
# and prepares for embedding-based semantic search in the next steps.

import os
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI

app = Flask(__name__, static_folder="static")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


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
    return jsonify({"reply": answer})


# Remove JSON loading code (this was part of the old static keyword system)
# No need for /resources or /resource route handlers anymore

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
