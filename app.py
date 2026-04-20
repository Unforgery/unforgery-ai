from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

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
You are an elite luxury authenticator AI.

Analyze the uploaded item images in detail.

Determine if the item is:
- Likely Authentic
- Suspicious
- Likely Fake

Inspect:
- logo accuracy
- stitching quality
- symmetry
- materials
- embossing
- font
- serial details
- proportions
- hardware engraving
- known counterfeit flaws

Ignore wear and used condition.

Return JSON:
{
 "decision":"Likely Authentic",
 "confidence":92,
 "details":{
   "logo":"Good alignment",
   "stitching":"Clean and consistent",
   "shape":"Correct proportions",
   "materials":"Consistent",
   "red_flags":"None detected"
 },
 "summary":"The item appears consistent with authentic references."
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
                "temperature": 0.2
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
