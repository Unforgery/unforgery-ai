from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import base64

app = Flask(__name__)
CORS(app)

# limite upload (20MB)

app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@app.route("/")
def home():
    return "UNFORGERY AI ONLINE"


@app.route("/analyze-upload", methods=["POST"])
def analyze_upload():
    try:
        brand = request.form.get("brand", "").strip()
        brand_lower = brand.lower()

        files = request.files.getlist("files")
        if not brand:
            brand = "general"

        files = request.files.getlist("files")

        if not files:
            return jsonify({"result": "No images received"}), 400

        prompt = f"""
You are a world-class luxury and sneaker authenticator AI specialized in {brand} products.

Your job:
Evaluate the uploaded images fairly and professionally.

FINAL VERDICT:
- LIKELY AUTHENTIC
- SUSPICIOUS
- LIKELY FAKE

====================================
CORE RULES
====================================

1. Adapt expertise specifically to {brand}.
Use known standards for logos, materials, craftsmanship, proportions, fonts, hardware, labels and common counterfeit flaws.

2. Important:
Professional studio photos, official product photos, clean ecommerce images, and catalog-style visuals should generally be considered positive evidence unless visible inconsistencies exist.

3. Do NOT punish:
- white background
- professional lighting
- shadows
- reflections
- camera quality
- compression
- normal wear

4. If user photos are too limited and no key details are visible:
choose SUSPICIOUS with moderate confidence.

5. Only choose LIKELY FAKE when multiple clear red flags exist.

6. If item strongly matches authentic standards and no visible issues appear:
choose LIKELY AUTHENTIC.

====================================
ANALYZE
====================================

- logo accuracy
- font consistency
- stitching quality
- symmetry
- materials
- proportions
- shape
- hardware quality
- engravings
- labels
- serial/date codes if visible
- inside details
- outsole/insole if relevant
- consistency across all photos
- known fake flaws for {brand}

====================================
CONFIDENCE SCALE
====================================

90-100 = Strong visible evidence
75-89 = Good probability
60-74 = Moderate
40-59 = Limited evidence
0-39 = Strong counterfeit signs

====================================
RETURN ONLY VALID JSON
====================================

{{
  "decision":"LIKELY AUTHENTIC",
  "confidence":91,
  "details":"Explain the strongest authentic signs, any concerns, photo quality sufficiency, and why this verdict was selected."
}}
"""

        content = [{"type": "text", "text": prompt}]

        for file in files[:10]:
            img_bytes = file.read()
            encoded = base64.b64encode(img_bytes).decode("utf-8")

            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{encoded}"
                }
            })

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "temperature": 0
            },
            timeout=120
        )

        data = response.json()

        if "choices" not in data:
            return jsonify({"result": str(data)}), 500

        answer = data["choices"][0]["message"]["content"]

        return jsonify({"result": answer})

    except Exception as e:
        return jsonify({"result": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
