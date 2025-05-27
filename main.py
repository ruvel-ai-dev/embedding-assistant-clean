import os
from flask import Flask, request, jsonify
from openai import OpenAI

# Step 1: Setup the Flask app
app = Flask(__name__, static_folder='static')

# Step 2: Initialize OpenAI client using API key from environment
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Step 3: Define a POST route to handle assistant questions
@app.route("/ask", methods=["POST"])
def ask_gpt():
    data = request.get_json()
    user_message = data.get("message", "")

    try:
        # Step 4: Send message to OpenAI GPT
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant that helps university lecturers embed careers content into their modules."},
                {"role": "user", "content": user_message}
            ]
        )

        # Step 5: Extract and return the reply
        answer = response.choices[0].message.content.strip()
        return jsonify({"reply": answer})

    except Exception as e:
        return jsonify({"reply": f"An error occurred: {str(e)}"})

# Step 6: Serve the HTML interface
@app.route("/")
def home():
    return app.send_static_file("index.html")

# Step 7: Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)


