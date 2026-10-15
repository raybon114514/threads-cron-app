import os
import sys
import time
from datetime import datetime, date
from zoneinfo import ZoneInfo

import requests

THREADS_USER_ID = os.environ.get("THREADS_USER_ID")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")

# 基準點：2026-10-07 為 DAY 127
BASE_DATE = date(2026, 10, 7)
BASE_DAY_COUNT = 127


def calculate_today_day_count() -> int:
    today_taipei = datetime.now(ZoneInfo("Asia/Taipei")).date()
    delta_days = (today_taipei - BASE_DATE).days
    return BASE_DAY_COUNT + delta_days


def post_to_threads(content: str):
    create_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    create_payload = {
        "media_type": "TEXT",
        "text": content,
        "access_token": ACCESS_TOKEN,
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
        "access_token": ACCESS_TOKEN,
    }

    try:
        pub_res = requests.post(publish_url, data=publish_payload, timeout=15).json()
    except Exception as e:
        return False, {"error_step": "publish_container", "detail": str(e)}

    if "id" in pub_res:
        return True, pub_res
    return False, pub_res


def main():
    if not THREADS_USER_ID or not ACCESS_TOKEN:
        print("缺少環境變數 THREADS_USER_ID 或 ACCESS_TOKEN")
        sys.exit(1)

    current_day = calculate_today_day_count()
    post_text = f"每天支持富邦悍將直到邦邦x邦邦\nDAY{current_day}"
    print(f"準備發文：\n{post_text}")

    success, result = post_to_threads(post_text)

    if success:
        print(f"發布成功！貼文 ID：{result.get('id')}")
    else:
        print(f"發布失敗：{result}")
        sys.exit(1)  # 讓 GitHub Actions 顯示紅色失敗，並寄信通知你


if __name__ == "__main__":
    main()