from supabase import create_client
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        email = data.get("email")

if not email:
    return jsonify({"error": "No email"}), 400

user = supabase.table("users_credits").select("*").eq("email", email).execute()

if not user.data:
    return jsonify({"error": "No account"}), 403

credits = user.data[0]["credits"]

if credits <= 0:
    return jsonify({"error": "No credits left"}), 403

        if not images:
            return jsonify({"error": "No images sent"}), 400

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



       supabase.table("users_credits").update({
    "credits": credits - 1
}).eq("email", email).execute()

return jsonify({
    "result": answer,
    "credits_left": credits - 1
})

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json

        email = data.get("email") or data.get("customer", {}).get("email")

        if not email:
            return "No email", 400

        items = data.get("line_items", [])

        credits_to_add = 0

        for item in items:
            title = item.get("title", "").lower()

            if "express" in title:
                credits_to_add += 1

            elif "pack 5" in title:
                credits_to_add += 5

            elif "premium" in title:
                credits_to_add += 20

        if credits_to_add == 0:
            return "No product matched", 200

        existing = supabase.table("users_credits").select("*").eq("email", email).execute()

        if existing.data:
            current = existing.data[0]["credits"]

            supabase.table("users_credits").update({
                "credits": current + credits_to_add
            }).eq("email", email).execute()

        else:
            supabase.table("users_credits").insert({
                "email": email,
                "credits": credits_to_add
            }).execute()

        return "OK", 200

    except Exception as e:
        return str(e), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
