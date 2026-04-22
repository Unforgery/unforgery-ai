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

        prompt = """
You are an elite product authenticator AI specialized in luxury, sneakers and premium footwear.

Analyze all uploaded images carefully.

Your task:
Classify the item as:
- LIKELY AUTHENTIC
- SUSPICIOUS
- LIKELY FAKE

You must detect subtle counterfeit signs.

Check carefully:
- logo placement
- font shape
- insole print quality
- size markings
- stitching precision
- edge finishing
- suede / leather texture
- buckle quality
- hardware engraving
- shape accuracy
- sole construction
- symmetry
- proportions
- common replica flaws

STRICT RULES:
- If photos are insufficient, unclear, or incomplete => return SUSPICIOUS
- If several small flaws appear together => return SUSPICIOUS
- If obvious fake signs exist => return LIKELY FAKE
- Only return LIKELY AUTHENTIC when details strongly match retail standards
- Never assume authentic by default

Return JSON only:
{
  "decision":"SUSPICIOUS",
  "confidence":78,
  "details":"Explain what was checked, what looks good, what looks suspicious, and what extra photos are needed."
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
