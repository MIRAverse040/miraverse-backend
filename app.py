import os
from flask import Flask, request, jsonify
from google import genai
import time

app = Flask(__name__)

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "app": "Miraverse",
        "message": "Mira is ready!"
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message is required"}), 400

    try:
      for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=(
                        "You are Mira, a warm and helpful AI companion "
                        "in the Miraverse app. Be kind, clear and responsible. "
                        "For health questions, provide general information, "
                        "never diagnose or prescribe, and identify urgent "
                        "warning signs.\n\n"
                        f"User: {message}"
                    )
                )

                return jsonify({"reply": response.text})

            except Exception as error:
                if (
                    ("503" in str(error) or "UNAVAILABLE" in str(error))
                    and attempt < 2
                ):
                    time.sleep(2 * (attempt + 1))
                else:
                    raise

    except Exception:
        app.logger.exception("Gemini request failed")
        return jsonify({
            "error": "Mira is temporarily unavailable. Please try again."
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
