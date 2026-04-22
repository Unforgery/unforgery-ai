from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import base64

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
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
            brand = "general product"

        files = request.files.getlist("files")

        if not files:
            return jsonify({"result": "No images received"}), 400

        prompt = f"""
You are UNFORGERY AI V3, a world-class authentication expert.

The customer states the brand is: {brand}

You MUST use this brand as the primary reference and adapt your expertise accordingly.

==================================================
MISSION
==================================================

Analyze all uploaded images and provide the most reliable verdict possible.

Final decisions:
- LIKELY AUTHENTIC
- SUSPICIOUS
- LIKELY FAKE

==================================================
STEP 1 — BRAND REFERENCE LOGIC
==================================================

Use the brand "{brand}" as the main reference.

Compare the uploaded product against:
- official product standards
- known design language
- common materials
- expected logos
- typical shapes
- authentic construction quality
- common counterfeit flaws

If the product visually matches official brand catalog / ecommerce standards,
this is positive evidence.

If an exact official model cannot be identified,
do NOT fail.

Instead perform the best complete expert analysis possible from visible evidence.

==================================================
STEP 2 — IMAGE TYPE DETECTION
==================================================

Determine whether the uploaded images are:

A) Official product photos / studio photos / ecommerce photos
B) Real user photos
C) Low quality / insufficient evidence photos

Rules:
- Official studio photos with strong consistency are positive evidence.
- Real user photos require detailed inspection.
- Poor or incomplete photos reduce confidence.

==================================================
STEP 3 — FULL AUTHENTICATION CHECK
==================================================

Check:

1. Branding
- logo accuracy
- font
- placement
- spacing
- embossing
- engraving
- spelling

2. Construction
- stitching
- symmetry
- edge finishing
- glue marks
- craftsmanship

3. Materials
- leather quality
- suede texture
- fabric quality
- canvas grain
- hardware finish
- premium feel

4. Shape
- silhouette
- proportions
- dimensions
- structure
- sole shape
- toe shape

5. Details
- labels
- serial/date codes if visible
- insole
- lining
- zipper
- buckle
- chains
- outsole

6. Cross-image consistency
- same product across all photos
- no contradictions

7. Counterfeit indicators
- wrong fonts
- cheap materials
- weak embossing
- poor stitching
- bad proportions
- incorrect shape
- suspicious finishing
- low quality hardware

==================================================
DECISION RULES
==================================================

Choose LIKELY AUTHENTIC when:
- strong consistency with official brand standards
- no meaningful red flags
- professional official images OR convincing real evidence

Choose SUSPICIOUS when:
- evidence is mixed
- images are insufficient
- too few angles
- uncertain details
- not enough proof either way

Choose LIKELY FAKE when:
- multiple visible counterfeit indicators exist
- clear contradictions with authentic standards

==================================================
IMPORTANT RULES
==================================================

- Always prioritize the customer brand: {brand}
- If no exact model found, continue with best expert analysis
- Never invent flaws
- Never assume fake without visible evidence
- Never assume authentic blindly
- Ignore lighting, shadows, blur, reflections, compression, background style
- Use all images together
- Stay objective and professional

==================================================
CONFIDENCE SCALE
==================================================

90-100 = Very strong evidence
75-89 = Strong probability
60-74 = Moderate confidence
40-59 = Limited evidence
0-39 = Strong counterfeit indicators

==================================================
RETURN ONLY VALID JSON
==================================================

{{
  "brand":"{brand}",
  "image_type":"official_product_photo",
  "decision":"LIKELY AUTHENTIC",
  "confidence":92,
  "details":"Explain strongest authentic signs, warning signs if any, whether it resembles official references, and why this final verdict was selected."
}}
"""

        content = [{"type": "text", "text": prompt}]

        for file in files[:10]:
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

        answer = data["choices"][0]["message"]["content"].strip()

        start = answer.find("{")
        end = answer.rfind("}") + 1

        if start != -1 and end != -1:
            answer = answer[start:end]

        return jsonify({"result": answer})

    except Exception as e:
        return jsonify({"result": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
