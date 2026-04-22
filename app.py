from supabase import create_client
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return "UNFORGERY AI ONLINE"


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json(force=True)

        images = data.get("images", [])
        plan = data.get("plan", "express")
        email = data.get("email", "").strip().lower()

        # CHECK EMAIL
        if not email:
            return jsonify({"error": "No email"}), 400

        # CHECK USER
        user = (
            supabase
            .table("users_credits")
            .select("*")
            .ilike("email", email)
            .execute()
        )

        if not user.data:
            return jsonify({"error": "No account"}), 403

        credits = int(user.data[0]["credits"])

        if credits <= 0:
            return jsonify({"error": "No credits left"}), 403

        # CHECK IMAGES
        if not images:
            return jsonify({"error": "No images sent"}), 400

        # ==================================================
        # PROMPTS (INCHANGÉS)
        # ==================================================
      
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
        
        # ==================================================

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

        if "choices" not in result:
            return jsonify({"error": result}), 500

        answer = result["choices"][0]["message"]["content"]

        # REMOVE 1 CREDIT
        (
            supabase
            .table("users_credits")
            .update({"credits": credits - 1})
            .eq("email", user.data[0]["email"])
            .execute()
        )

        return jsonify({
            "result": answer,
            "credits_left": credits - 1
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)

        email = (
            data.get("email")
            or data.get("customer", {}).get("email")
            or ""
        ).strip().lower()

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

        existing = (
            supabase
            .table("users_credits")
            .select("*")
            .ilike("email", email)
            .execute()
        )

        if existing.data:
            current = int(existing.data[0]["credits"])

            (
                supabase
                .table("users_credits")
                .update({"credits": current + credits_to_add})
                .eq("email", existing.data[0]["email"])
                .execute()
            )
        else:
            (
                supabase
                .table("users_credits")
                .insert({
                    "email": email,
                    "credits": credits_to_add
                })
                .execute()
            )

        return "OK", 200

    except Exception as e:
        return str(e), 500

import base64

@app.route("/analyze-upload", methods=["POST"])
def analyze_upload():
    try:
        files = request.files.getlist("files")

        if not files:
            return jsonify({"result": "No images received"}), 400

        content = [{
            "type": "text",
            "text": """
You are an elite product authenticator AI.

Analyze these item photos.

Possible results:
- Likely Authentic
- Suspicious
- Likely Fake

Return only:
{
 "decision":"Likely Authentic"
}
"""
        }]

        for file in files[:20]:
            img_bytes = file.read()
            encoded = base64.b64encode(img_bytes).decode("utf-8")

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

        result = response.json()

        if "choices" not in result:
            return jsonify({"result": str(result)}), 500

        answer = result["choices"][0]["message"]["content"]

        return jsonify({
            "result": answer
        })

    except Exception as e:
        return jsonify({"result": str(e)}), 500
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
