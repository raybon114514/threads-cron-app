import os
import time
import traceback
import requests
from datetime import datetime, date
import pytz
from flask import Flask, request, jsonify

app = Flask(__name__)

THREADS_USER_ID = os.environ.get("THREADS_USER_ID")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
CRON_SECRET = os.environ.get("CRON_SECRET", "default_secret")

# 基準點：2026-10-07 為 DAY 127
BASE_DATE = date(2026, 10, 7)
BASE_DAY_COUNT = 127

def calculate_today_day_count() -> int:
    taipei_tz = pytz.timezone("Asia/Taipei")
    today_taipei = datetime.now(taipei_tz).date()
    delta_days = (today_taipei - BASE_DATE).days
    return BASE_DAY_COUNT + delta_days

def post_to_threads(content: str):
    create_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    create_payload = {
        "media_type": "TEXT",
        "text": content,
        "access_token": ACCESS_TOKEN
    }
    
    try:
        create_res = requests.post(create_url, data=create_payload, timeout=15).json()
    except Exception as e:
        return False, {"error_step": "create_container", "detail": str(e)}
    
    if "id" not in create_res:
        return False, create_res
        
    creation_id = create_res["id"]
    time.sleep(5)
    
    publish_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
    publish_payload = {
        "creation_id": creation_id,
        "access_token": ACCESS_TOKEN
    }
    
    try:
        pub_res = requests.post(publish_url, data=publish_payload, timeout=15).json()
    except Exception as e:
        return False, {"error_step": "publish_container", "detail": str(e)}
    
    if "id" in pub_res:
        return True, pub_res
    else:
        return False, pub_res

@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "running"}), 200

@app.route("/trigger-post", methods=["GET", "POST"])
def trigger_post():
    try:
        # 1. 驗證金鑰
        auth_header = request.headers.get("X-Cron-Secret")
        if auth_header != CRON_SECRET:
            return jsonify({"status": "unauthorized"}), 401

        # 2. 發文處理
        current_day = calculate_today_day_count()
        post_text = f"每天支持富邦悍將直到邦邦x邦邦\nDAY{current_day}"
        
        success, result = post_to_threads(post_text)
        
        if success:
            return jsonify({"status": "ok", "day": current_day, "id": result.get("id")}), 200
        else:
            # 即使失敗，也只傳簡短 JSON，不爆 Response 大小
            return jsonify({"status": "failed", "detail": result}), 500

    except Exception as e:
        # 捕捉所有未知的 Crash，回傳精簡 JSON
        error_msg = str(e)
        print(f"CRASH ERROR: {error_msg}")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": error_msg[:200]}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))