import os
from flask import Flask, request, jsonify
from openai import OpenAI

# Step 1: Setup the Flask app
app = Flask(__name__)

# Step 2: Initialize OpenAI client with API key from Replit Secrets
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# Step 3: Define a route that listens to POST requests
@app.route("/ask", methods=["POST"])
def ask_gpt():
    data = request.get_json()
    user_message = data.get("message")

    # Step 4: Send the message to OpenAI's GPT
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # or "gpt-4" if you want
        messages=[{
            "role": "user",
            "content": user_message
        }])

    # Step 5: Return the AI's reply
    answer = response.choices[0].message.content
    return jsonify({"reply": answer})

@app.route("/")
def home():
    return app.send_static_file("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)


