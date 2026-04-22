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
You are an elite product authenticator AI specialized in {brand} products.

Analyze all uploaded images carefully.

Your task:
Classify the item as:
- LIKELY AUTHENTIC
- SUSPICIOUS
- LIKELY FAKE

Be accurate and fair.

Check:
- logo accuracy
- stitching quality
- proportions
- materials
- fonts
- embossing
- hardware
- symmetry
- labels
- expected authentic traits
- known counterfeit flaws

VERY IMPORTANT RULES:
- Official brand website photos, studio product photos, catalog photos, or professional ecommerce images should usually be rated LIKELY AUTHENTIC unless there is clear evidence otherwise.
- Do not invent flaws.
- Do not penalize lighting, shadows, reflections, compression, or camera angle.
- Normal wear is not a counterfeit sign.
- If evidence is mixed, choose SUSPICIOUS.
- If evidence strongly matches authentic standards, choose LIKELY AUTHENTIC.

Return JSON only:
{{
  "decision":"LIKELY AUTHENTIC",
  "confidence":92,
  "details":"Explain precisely why."
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
