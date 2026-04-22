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
        files = request.files.getlist("files")

        if not files:
            return jsonify({"result": "No images received"}), 400

        prompt = f"""
You are an elite AI authenticator specialized in {brand} products.

Analyze all uploaded images carefully.

Your task:
Classify the item as:
- LIKELY AUTHENTIC
- SUSPICIOUS
- LIKELY FAKE

Check:
- logo accuracy
- stitching
- proportions
- materials
- fonts
- hardware
- symmetry
- finishing quality
- known counterfeit flaws

BALANCED RULES:
- Official brand product photos or highly consistent retail-quality images should usually be LIKELY AUTHENTIC
- If details strongly match authentic standards and no red flags appear => LIKELY AUTHENTIC
- If evidence is mixed, limited, or uncertain => SUSPICIOUS
- If multiple flaws or major inconsistencies appear => LIKELY FAKE
- Do not penalize studio lighting, clean backgrounds, compression, or normal wear

Return JSON only:
{{
  "brand":"{brand}",
  "decision":"LIKELY AUTHENTIC",
  "confidence":91,
  "details":"Explain what was checked, what looks correct, what looks suspicious if any, and why."
}}
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
