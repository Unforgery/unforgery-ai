from flask import Flask, request, jsonify
from flask_cors import CORS
import os, requests, base64

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

==================================================
CORE ANALYSIS FRAMEWORK
==================================================

Examine all uploaded images carefully and compare visual consistency across every photo.

Analyze:

1. Branding
- logo shape
- logo placement
- logo proportions
- spelling
- font accuracy
- engraving quality
- embossing precision

2. Construction Quality
- stitching alignment
- stitch density
- symmetry
- edge finishing
- glue marks
- craftsmanship level

3. Materials
- leather / fabric texture
- canvas grain
- suede quality
- shine / matte balance
- hardware finish
- weight impression
- overall premium feel

4. Shape & Structure
- silhouette
- proportions
- panel alignment
- sole shape
- handle shape
- dimensions consistency

5. Hardware & Details
- zipper quality
- screws
- buckles
- chains
- clasps
- metal color
- engravings
- serial plates

6. Labels / Codes / Interior
- tags
- date codes
- serial numbers
- insole prints
- lining quality
- inside stamps

7. Counterfeit Detection
Look for known fake indicators:
- wrong fonts
- poor spacing
- uneven stitching
- cheap materials
- weak embossing
- inaccurate shape
- inconsistent details
- low quality hardware
- branding errors
- mismatch between photos

==================================================
IMPORTANT DECISION RULES
==================================================

- Never assume authentic just because photos look professional.
- Never assume fake without real visible evidence.
- Do not invent flaws.
- Ignore lighting, shadows, blur, compression, reflections, and normal wear.
- If evidence is limited, lower confidence.
- If several strong red flags appear, classify as LIKELY FAKE.
- If item looks mostly correct but some concerns remain, classify as SUSPICIOUS.
- If details strongly match authentic standards with no meaningful red flags, classify as LIKELY AUTHENTIC.
- Be conservative with expensive luxury items.
- Use all photos together, not only one image.

==================================================
CONFIDENCE SCALE
==================================================

90-100 = Very strong evidence
75-89  = Strong probability
60-74  = Moderate confidence
40-59  = Uncertain / mixed evidence
0-39   = Strong counterfeit indicators

==================================================
OUTPUT RULES
==================================================

Return ONLY valid JSON.
No markdown.
No extra text.

{
  "decision":"SUSPICIOUS",
  "confidence":82,
  "details":"Explain the strongest authentic signs, the strongest warning signs, and why this final verdict was chosen."
}
"""

        content = [{"type": "text", "text": prompt}]

        for file in files[:20]:
            img = file.read()
            encoded = base64.b64encode(img).decode("utf-8")

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
                    {"role": "user", "content": content}
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
