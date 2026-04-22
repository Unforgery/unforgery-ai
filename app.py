from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import base64

app = Flask(__name__)
CORS(app)

app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@app.route("/")
def home():
    return "UNFORGERY AI ONLINE"


@app.route("/analyze-upload", methods=["POST"])
def analyze_upload():
    try:
        # Client inputs
        brand = request.form.get("brand", "").strip()
        if not brand:
            brand = "general product"

        files = request.files.getlist("files")

        if not files:
            return jsonify({"result": "No images received"}), 400

        prompt = f"""
You are UNFORGERY AI, a world-class product authentication expert.

You are now specifically analyzing a product from the brand: {brand}

Your role:
Use the uploaded images and adapt your expertise to this exact brand automatically.

You must understand the expected standards, design language, craftsmanship, materials, logos, fonts, shapes, hardware, labels, packaging details, and common counterfeit flaws typically associated with {brand}.

==================================================
MISSION
==================================================

Return the most accurate and professional authenticity assessment possible.

Final decision must be one of:
- LIKELY AUTHENTIC
- SUSPICIOUS
- LIKELY FAKE

==================================================
STEP 1 — PHOTO SUFFICIENCY CHECK
==================================================

Before judging authenticity, determine whether enough useful evidence is visible.

Useful evidence may include:
- front view
- side view
- back view
- logo close-up
- stitching close-up
- label / size tag
- sole / outsole
- insole
- hardware close-up
- serial code
- interior details
- multiple angles

If photos are too few, blurry, too far, missing key details, or incomplete:

DO NOT guess authenticity.

Instead:
- choose SUSPICIOUS
- reduce confidence
- explain which additional photos are needed

Never return LIKELY AUTHENTIC with weak evidence only.

==================================================
STEP 2 — BRAND-ADAPTED AUTHENTICATION
==================================================

Analyze according to the standards of {brand}.

Check carefully:

1. Branding
- logo shape
- placement
- size
- spacing
- font
- engraving
- embossing
- spelling

2. Construction
- stitching quality
- stitch alignment
- symmetry
- edge finishing
- glue marks
- precision
- craftsmanship level

3. Materials
- leather quality
- suede quality
- fabric texture
- canvas grain
- hardware finish
- premium feel
- expected material consistency

4. Shape & Structure
- silhouette
- proportions
- dimensions
- panel alignment
- sole shape
- toe shape
- structure consistency

5. Details
- labels
- tags
- date codes
- serial numbers
- insole print
- lining
- zipper quality
- buckles
- chains
- clasps
- outsole pattern

6. Cross-Image Consistency
- same product across photos
- matching details
- no contradictions between images

7. Counterfeit Indicators
Look for:
- wrong fonts
- poor spacing
- low-quality materials
- weak embossing
- inaccurate shape
- uneven stitching
- cheap hardware
- wrong proportions
- incorrect logos
- mismatched details
- suspicious finishing

==================================================
DECISION LOGIC
==================================================

Choose LIKELY AUTHENTIC when:
- enough visual evidence exists
- details strongly match expected authentic standards
- no meaningful red flags appear

Choose SUSPICIOUS when:
- evidence is incomplete
- photos are insufficient
- quality is uncertain
- some concerns exist but not enough proof of fake

Choose LIKELY FAKE when:
- multiple visible counterfeit indicators appear
- clear inconsistencies exist
- strong evidence contradicts authentic standards

==================================================
IMPORTANT RULES
==================================================

- Adapt automatically to the brand {brand}
- Never assume authentic only because photos look professional
- Never assume fake without visible evidence
- Do not invent flaws
- Ignore lighting, blur, reflections, shadows, compression, background style, and normal wear
- Use all photos together, not only one image
- Be stricter for premium/luxury brands
- Stay objective and professional

==================================================
CONFIDENCE SCALE
==================================================

90-100 = Very strong evidence
75-89  = Strong probability
60-74  = Moderate confidence
40-59  = Limited evidence / uncertainty
0-39   = Strong counterfeit indicators

==================================================
OUTPUT FORMAT
==================================================

Return ONLY valid JSON.
No markdown.
No extra text.

{{
  "decision":"SUSPICIOUS",
  "confidence":72,
  "details":"Explain strongest authentic signs, warning signs, whether photos were sufficient, and why this final verdict was selected."
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

        answer = data["choices"][0]["message"]["content"]

        return jsonify({"result": answer})

    except Exception as e:
        return jsonify({"result": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
