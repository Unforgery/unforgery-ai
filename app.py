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
You are a world-class AI product authenticator specialized in {brand} products, including luxury goods, sneakers, accessories, bags, watches, and fashion items.

Your mission:
Deliver the most accurate, fair, and professional authenticity assessment possible using only the uploaded images.

You must classify the item as one of these:
- LIKELY AUTHENTIC
- SUSPICIOUS
- LIKELY FAKE

Analyze all uploaded photos together.

Check carefully:
1. Branding
- logo shape
- placement
- proportions
- spelling
- font
- engraving
- embossing

2. Construction Quality
- stitching alignment
- symmetry
- edge finishing
- glue marks
- craftsmanship

3. Materials
- leather / fabric quality
- suede texture
- canvas grain
- hardware finish
- premium feel

4. Shape & Structure
- silhouette
- proportions
- panel alignment
- dimensions consistency

5. Hardware & Details
- zipper quality
- buckles
- chains
- clasps
- screws
- engravings

6. Labels / Codes / Interior
- tags
- serial numbers
- insole prints
- lining
- inside stamps

7. Counterfeit Indicators
- wrong fonts
- poor spacing
- cheap materials
- uneven stitching
- inaccurate shape
- weak embossing
- inconsistent details

Important rules:
- Never assume authentic only because photos look professional.
- Never assume fake without visible evidence.
- Ignore lighting, shadows, blur, reflections, compression, and normal wear.
- If evidence is limited, lower confidence.
- If strong red flags appear = LIKELY FAKE.
- If mixed evidence = SUSPICIOUS.
- If strong consistency and no red flags = LIKELY AUTHENTIC.

Return ONLY valid JSON.
No markdown.
No extra text.

{{
  "decision": "LIKELY AUTHENTIC",
  "confidence": 91,
  "details": "Short but professional explanation of authentic signs, warning signs if any, and final reasoning."
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
