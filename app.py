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
        data = request.json
        images = data.get("images", [])

        if not images:
            return jsonify({"result": "No images sent"})

        prompt = """
You are an elite luxury authenticator AI.

Your mission:
Determine if the product is likely AUTHENTIC, SUSPICIOUS, or INCONCLUSIVE.

You must inspect:
- logo shape
- stitching quality
- serial number
- font
- embossing
- hardware engraving
- zipper details
- symmetry
- proportions
- known counterfeit flaws

Ignore:
- wear
- scratches
- old condition
- used item condition

Compare with authentic references and identify anomalies.

Return JSON:
{
 "decision":"AUTHENTIC",
 "confidence":92,
 "reason":"Short explanation"
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
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "temperature": 0.2
            }
        )

        result = response.json()
        answer = result["choices"][0]["message"]["content"]

        return jsonify({"result": answer})

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
