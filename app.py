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


@app.route("/")
def home():
    return "UNFORGERY AI ONLINE"


@app.route("/analyze-upload", methods=["POST"])
def analyze_upload():
    try:
        brand = request.form.get("brand", "").strip()

        if not brand:
            brand = "general product"

        files = request.files.getlist("files")

        if not files:
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
- authentic
