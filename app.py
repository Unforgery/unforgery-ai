from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@app.route("/")
def home():
    return "UNFORGERY AI ONLINE"

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        images = data.get("images", [])
        plan = data.get("plan", "express")

        if not images:
            return jsonify({"error": "No images sent"})

        if plan == "premium":
            prompt = """
You are an elite product authenticator AI specialized in luxury and sneakers.

Your task:
Classify the item as:
- LIKELY AUTHENTIC
- SUSPICIOUS
- LIKELY FAKE

Be accurate and balanced.

Use:
- logo accuracy
- stitching
- proportions
- materials
- font
- embossing
- hardware
- symmetry
- expected authentic design traits
- known counterfeit flaws

Important rules:
- Official brand product photos should normally be rated LIKELY AUTHENTIC.
- Do not penalize lighting, shadows, camera angle, compression, or normal wear.
- Do not mark suspicious unless there are clear inconsistencies.
- If evidence is limited, prefer cautious but fair judgment.

Return JSON only:
{
 "decision":"LIKELY AUTHENTIC",
 "confidence":92,
 "reason":"Short explanation"
}
"""
        else:
            prompt = """
You are an elite product authenticator AI.

Analyze the uploaded item images.

Possible results:
- Likely Authentic
- Suspicious
- Likely Fake

Check:
- logo
- stitching
- proportions
- shape
- counterfeit flaws

Ignore wear and used condition.

Return JSON:
{
 "decision":"Likely Authentic"
}
"""

        content = [{"type": "text", "text": prompt}]

        for img in images:
            content.append({
                "type": "image_url",
                "image_url": {"url": img}
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
            timeout=60
        )

        result = response.json()
        answer = result["choices"][0]["message"]["content"]

        return jsonify({"result": answer})

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
