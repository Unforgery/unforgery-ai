from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import base64
import json
import re

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
CORS(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


# ==================================================
# HELPERS SUPABASE
# ==================================================

def sb_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }


def get_user(email):
    url = f"{SUPABASE_URL}/rest/v1/users_credits?email=eq.{email}&select=*"
    r = requests.get(url, headers=sb_headers(), timeout=20)
    data = r.json()
    return data[0] if data else None


def get_credits(email):
    user = get_user(email)
    return user["credits"] if user else 0


def add_credits(email, amount):
    user = get_user(email)

    if user:
        row_id = user["id"]
        new_total = int(user["credits"]) + int(amount)

        url = f"{SUPABASE_URL}/rest/v1/users_credits?id=eq.{row_id}"
        requests.patch(
            url,
            headers=sb_headers(),
            json={"credits": new_total},
            timeout=20
        )
    else:
        url = f"{SUPABASE_URL}/rest/v1/users_credits"
        requests.post(
            url,
            headers=sb_headers(),
            json={
                "email": email,
                "credits": amount
            },
            timeout=20
        )


def remove_credit(email):
    user = get_user(email)

    if not user:
        return False

    current = int(user["credits"])

    if current <= 0:
        return False

    row_id = user["id"]

    url = f"{SUPABASE_URL}/rest/v1/users_credits?id=eq.{row_id}"
    requests.patch(
        url,
        headers=sb_headers(),
        json={"credits": current - 1},
        timeout=20
    )

    return True


# ==================================================
# BASIC ROUTE
# ==================================================

@app.route("/")
def home():
    return "UNFORGERY AI ONLINE"


# ==================================================
# SHOPIFY WEBHOOK (AJOUT CREDITS APRES PAIEMENT)
# ==================================================

@app.route("/shopify-webhook", methods=["POST"])
def shopify_webhook():
    try:
        data = request.json
        email = data.get("email", "").strip().lower()

        if not email:
            return jsonify({"status": "no email"}), 400

        total = 0

        for item in data.get("line_items", []):
            title = item.get("title", "").lower()
            qty = int(item.get("quantity", 1))

            if "express authentication scan" in title:
                total += 1 * qty

            elif "pack 5 authentication scans" in title:
                total += 5 * qty

            elif "premium authentication scan" in title:
                total += 20 * qty

        if total > 0:
            add_credits(email, total)

        return jsonify({
            "status": "success",
            "email": email,
            "credits_added": total
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================================================
# GET CREDITS
# ==================================================

@app.route("/get-credits", methods=["POST"])
def get_user_credits():
    try:
        data = request.json
        email = data.get("email", "").strip().lower()

        return jsonify({
            "email": email,
            "credits": get_credits(email)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================================================
# MAIN SCAN ROUTE (PROMPT INTACT)
# ==================================================

@app.route("/analyze-upload", methods=["POST"])
def analyze_upload():
    try:
        # Vérifie clé API
        if not OPENAI_API_KEY:
            return jsonify({"result": "OPENAI_API_KEY missing"}), 500

        email = request.form.get("email", "").strip().lower()

        if not email:
            return jsonify({"result": "Email required"}), 400

        # Vérifie crédits
        if get_credits(email) <= 0:
            return jsonify({"result": "No credits remaining"}), 403

        brand = request.form.get("brand", "").strip()
        if not brand:
            brand = "general product"

        files = request.files.getlist("files")

        if not files or len(files) == 0:
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

        # Max 10 images
        for file in files[:10]:
            try:
                img = file.read()

                if not img:
                    continue

                encoded = base64.b64encode(img).decode("utf-8")

                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded}"
                    }
                })

            except Exception:
                continue

        # Si aucune image valide
        if len(content) == 1:
            return jsonify({"result": "Invalid images"}), 400

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

        # Vérifie erreur API OpenAI
        if response.status_code != 200:
            return jsonify({
                "result": f"OpenAI Error {response.status_code}: {response.text}"
            }), 500

        data = response.json()

        if "choices" not in data:
            return jsonify({"result": str(data)}), 500

        answer = data["choices"][0]["message"]["content"].strip()

        # Nettoyage markdown
        answer = answer.replace("```json", "").replace("```", "").strip()

        # Extraction JSON
        match = re.search(r"\{.*\}", answer, re.DOTALL)
        if match:
            answer = match.group(0)

        # Retire 1 crédit seulement si scan OK
        remove_credit(email)

        # JSON clean
        try:
            parsed = json.loads(answer)
            return jsonify({"result": json.dumps(parsed)})
        except Exception:
            return jsonify({"result": answer})

    except requests.exceptions.Timeout:
        return jsonify({"result": "Request timeout"}), 500

    except Exception as e:
        return jsonify({"result": f"Server error: {str(e)}"}), 500


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


@app.route("/get-credits", methods=["GET"])
def get_credits():
    try:
        email = request.args.get("email", "").strip().lower()

        if not email:
            return jsonify({"credits": 0, "plan": "No Plan"})

        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
        }

        url = f"{SUPABASE_URL}/rest/v1/users_credits?email=eq.{email}&select=*"

        r = requests.get(url, headers=headers)
        data = r.json()

        if not data:
            return jsonify({"credits": 0, "plan": "No Plan"})

        user = data[0]

        return jsonify({
            "credits": user.get("credits", 0),
            "plan": user.get("plan", "Unknown")
        })

    except Exception as e:
        return jsonify({
            "credits": 0,
            "plan": "Error"
        })
