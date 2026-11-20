
from flask import Flask, request, jsonify
from flask_cors import CORS
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import requests
import re
import os
import hmac

app = Flask(__name__)
CORS(app)

API_URL = "https://uaas.kaixindou.net/service/batchQuery"

ADMIN_ID = os.environ.get("ADMIN_ID", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "")

def make_serializer():
    if not SECRET_KEY:
        return None
    return URLSafeTimedSerializer(SECRET_KEY)

def verify_admin():
    serializer = make_serializer()
    if serializer is None:
        return False

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False

    try:
        serializer.loads(auth[7:], max_age=3600)
        return True
    except (BadSignature, SignatureExpired):
        return False

@app.route("/")
def home():
    return "Qwick Live Diamond Recharge Backend Running!"

@app.route("/api/lookup", methods=["GET"])
def lookup():
    uid = request.args.get("uid", "").strip()

    if not re.fullmatch(r"[0-9]{1,20}", uid):
        return jsonify({"error": "Invalid UID"}), 400

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://uaas-test.kaixindou.net",
        "Referer": "https://uaas.kaixindou.net/html/tool.html"
    }

    payload = {
        "appId": "ikxd",
        "with_oa": "1",
        "type": "3",
        "vals": uid
    }

    try:
        response = requests.post(
            API_URL, headers=headers, data=payload, timeout=15
        )
        response.raise_for_status()
        data = response.json()

        if data.get("result_code") != "00000":
            return jsonify({"error": "Profile not found"}), 404

        profiles = data.get("info", [])
        if not profiles:
            return jsonify({"error": "Profile not found"}), 404

        profile = profiles[0]
        if str(profile.get("vid", "")) != uid:
            return jsonify({"error": "UID mismatch"}), 404

        return jsonify({
            "uid": profile.get("vid"),
            "name": profile.get("nick"),
            "avatar": profile.get("avatar")
        })

    except requests.RequestException:
        return jsonify({"error": "Lookup service unavailable"}), 502
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid API response"}), 502

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    if not ADMIN_ID or not ADMIN_PASSWORD or not SECRET_KEY:
        return jsonify({"error": "Admin settings missing"}), 503

    data = request.get_json(silent=True) or {}
    admin_id = str(data.get("admin_id", ""))
    password = str(data.get("password", ""))

    if (
        hmac.compare_digest(admin_id, ADMIN_ID)
        and hmac.compare_digest(password, ADMIN_PASSWORD)
    ):
        token = make_serializer().dumps({"admin": ADMIN_ID})
        return jsonify({"success": True, "token": token})

    return jsonify({"error": "Invalid Admin ID or Password"}), 401

@app.route("/api/admin/settings", methods=["GET", "POST"])
def admin_settings():
    if not verify_admin():
        return jsonify({"error": "Unauthorized"}), 401

    if request.method == "GET":
        return jsonify({
            "website_enabled": True,
            "diamond_delivery": False,
            "message": "Delivery is disabled"
        })

    data = request.get_json(silent=True) or {}

    return jsonify({
        "success": True,
        "website_enabled": bool(data.get("website_enabled", True)),
        "diamond_delivery": False,
        "message": "Settings received. Delivery remains disabled."
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
