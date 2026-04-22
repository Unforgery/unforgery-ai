from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import base64

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@app.route("/")
def home():
    return "UNFORGERY AI ONLINE"


@app.route("/analyze-upload", methods=["POST"])
def analyze_upload():
    try:
        brand = request.form.get("brand", "").strip()

        if not brand:
            brand = "general"

        files = request.files.getlist("files")

        if not files:
            return jsonify({"result": "No images received"}), 400

        prompt = f"""
You are a world-class authentication expert specialized ONLY in {brand} products.

You know authentic manufacturing standards, common counterfeit flaws, logos, fonts, materials, shape, labels, hardware, and construction details of {brand}.

Your mission:
Give the most professional and cautious authenticity verdict possible from the uploaded images.

Possible decisions:
- LIKELY AUTHENTIC
- SUSPICIOUS
- LIKELY FAKE

==================================================
STEP 1 — CHECK IMAGE SUFFICIENCY
==================================================

First determine if there is enough visual evidence.

Minimum useful evidence includes several of these:
- front view
- side view
- back view
- logo close-up
- stitching close-up
- label / size tag
- sole / outsole
- interior / insole
- hardware close-up
- serial code / date code (if relevant)

If images are too few, too blurry, too distant, missing key angles, or missing critical details:

You MUST return:
- decision = SUSPICIOUS
- lower confidence
- explain that more photos are required

Never return LIKELY AUTHENTIC with weak evidence.

==================================================
STEP 2 — BRAND EXPERT ANALYSIS
==================================================

Analyze according to {brand} standards:

1. Branding
- logo accuracy
- font
- spacing
- placement
- embossing
- engraving

2. Construction
- stitching quality
- symmetry
- craftsmanship
- finishing

3. Materials
- leather / suede / fabric quality
- texture
- hardware quality
- premium feel

4. Shape
- silhouette
- proportions
- structure
- dimensions consistency

5. Details
- labels
- serial codes
- insoles
- lining
- zippers
- buckles
- chains
- outsole pattern

6. Counterfeit Detection
- wrong font
- cheap materials
- poor stitching
- bad proportions
- weak embossing
- incorrect shape
- inconsistent details

==================================================
DECISION RULES
==================================================

- Strong consistency + enough evidence = LIKELY AUTHENTIC
- Mixed signs OR insufficient photos = SUSPICIOUS
- Clear fake indicators = LIKELY FAKE

Be strict, fair, and professional.

Return ONLY valid JSON:

{{
  "decision":"SUSPICIOUS",
  "confidence":63,
  "details":"Explain strongest positive signs, warning signs, and if more photos are needed."
}}
"""

        content = [{"type": "text", "text": prompt}]

        for file in files[:20]:
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
