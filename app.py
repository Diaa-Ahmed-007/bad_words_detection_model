from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import logging
import json
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Setup Flask
app = Flask(__name__)
CORS(app)

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logging.error("GEMINI_API_KEY not found in environment variables.")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    logging.info("Gemini API configured successfully.")

@app.route("/check_text", methods=["POST"])
def check_text():
    data = request.get_json()
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "text is required"}), 400

    try:
        # Strict prompt
        prompt = (
            "You are a strict content moderation system.\n"
            "ONLY return one of the following JSON responses and nothing else:\n"
            '{"is_clean": true, "message": "The text is clean"}\n'
            'OR\n'
            '{"is_clean": false, "message": "The text contains abusive language"}\n\n'
            "Rules:\n"
            "- Mark as abusive ONLY if the text contains profanity, vulgarity, hate speech, or offensive slurs.\n"
            "- DO NOT mark as abusive if the text contains criticism, negative opinion, or poor product reviews.\n"
            "- Sentences like 'this product is bad' or 'I hate this service' are just opinions and NOT abusive.\n"
            "- Return JSON only. DO NOT explain your answer or return any additional text.\n\n"
            f'Sentence: "{text}"'
        )



        response = model.generate_content(prompt)
        result_text = response.text.strip()
        logging.info(f"Gemini raw response: {result_text}")

        try:
            result = json.loads(result_text)
            if isinstance(result, dict) and "is_clean" in result:
                return jsonify(result)
            else:
                raise ValueError("Invalid JSON format.")
        except json.JSONDecodeError as e:
            logging.error(f"Gemini response JSON decode error: {e}")
            return jsonify({
                "is_clean": False,
                "message": "Failed to parse Gemini response. Please try again."
            }), 500

    except Exception as e:
        logging.error(f"Error in /check_text endpoint: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    from os import environ
    app.run(host="0.0.0.0", port=int(environ.get("PORT", 5000)))
