import os
import time
import requests
from datetime import datetime, date
import pytz
from flask import Flask, request, jsonify

app = Flask(__name__)

THREADS_USER_ID = os.environ.get("THREADS_USER_ID")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
CRON_SECRET = os.environ.get("CRON_SECRET", "default_secret")

# 定義基準點：2026-10-07 為 DAY 127
BASE_DATE = date(2026, 10, 7)
BASE_DAY_COUNT = 127

def calculate_today_day_count() -> int:
    """根據當前台灣時間算今天是第幾天"""
    taipei_tz = pytz.timezone("Asia/Taipei")
    today_taipei = datetime.now(taipei_tz).date()
    
    # 計算距離基準日過幾天
    delta_days = (today_taipei - BASE_DATE).days
    return BASE_DAY_COUNT + delta_days

def post_to_threads(content: str):
    # 1. 建立貼文容器
    create_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    create_payload = {
        "media_type": "TEXT",
        "text": content,
        "access_token": ACCESS_TOKEN
    }
    create_res = requests.post(create_url, data=create_payload).json()
    
    if "id" not in create_res:
        print(f"建立容器失敗: {create_res}")
        return False, create_res
        
    creation_id = create_res["id"]
    time.sleep(5)
    
    # 2. 正式發布貼文
    publish_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
    publish_payload = {
        "creation_id": creation_id,
        "access_token": ACCESS_TOKEN
    }
    pub_res = requests.post(publish_url, data=publish_payload).json()
    
    if "id" in pub_res:
        print(f"發布成功！貼文 ID: {pub_res['id']}")
        return True, pub_res
    else:
        print(f"發布失敗: {pub_res}")
        return False, pub_res

@app.route("/", methods=["GET"])
def index():
    current_day = calculate_today_day_count()
    return jsonify({"status": "running", "next_day_count": current_day}), 200

@app.route("/trigger-post", methods=["GET", "POST"])
def trigger_post():
    # 驗證認證金鑰
    auth_header = request.headers.get("X-Cron-Secret")
    if auth_header != CRON_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    # 自動計算今天的天數數字
    current_day = calculate_today_day_count()
    
    # 組成發文內容
    post_text = f"每天支持富邦悍將直到邦邦x邦邦\nDAY{current_day}"
    
    success, result = post_to_threads(post_text)
    if success:
        return jsonify({
            "message": "Successfully posted to Threads", 
            "posted_content": post_text,
            "result": result
        }), 200
    else:
        return jsonify({"error": "Failed to post", "detail": result}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))