import os
import time

from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

API_KEY = os.environ.get("GEMINI_API_KEY")

# You can change this through Render environment variables.
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")


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
        return jsonify({
            "error": "Message is required"
        }), 400

    if not API_KEY:
        app.logger.error("GEMINI_API_KEY is missing")
        return jsonify({
            "error": "AI service configuration is missing."
        }), 503

    prompt = (
        "You are Mira, a warm and helpful AI companion "
        "in the Miraverse app. Be kind, clear and responsible. "
        "For health questions, provide general information, "
        "never diagnose or prescribe, and identify urgent "
        "warning signs.\n\n"
        f"User: {message}"
    )

    try:
        client = genai.Client(api_key=API_KEY)

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=MODEL,
                    contents=prompt
                )

                reply = response.text

                if not reply:
                    raise ValueError("Gemini returned an empty response")

                return jsonify({"reply": reply}), 200

            except Exception as error:
                error_text = str(error).upper()

                temporary_error = any(
                    code in error_text
                    for code in [
                        "429",
                        "500",
                        "502",
                        "503",
                        "504",
                        "RESOURCE_EXHAUSTED",
                        "UNAVAILABLE",
                        "INTERNAL"
                    ]
                )

                if temporary_error and attempt < 2:
                    wait_time = 2 ** (attempt + 1)
                    app.logger.warning(
                        "Gemini temporary error. "
                        "Retrying in %s seconds. Attempt %s/3",
                        wait_time,
                        attempt + 1
                    )
                    time.sleep(wait_time)
                    continue

                raise

    except Exception:
        app.logger.exception("Gemini request failed")

        return jsonify({
            "error": "Mira is temporarily unavailable. "
                     "Please try again shortly."
        }), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
