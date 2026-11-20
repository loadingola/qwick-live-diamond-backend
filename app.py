from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app)

API_URL = "https://uaas.kaixindou.net/service/batchQuery"

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
        response = requests.post(API_URL, headers=headers, data=payload, timeout=15)
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

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
