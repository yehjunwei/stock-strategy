"""
Line Messaging API Sender
用於發送 Line Push Message
"""
import os
import requests

LINE_API_URL = "https://api.line.me/v2/bot/message/push"


def send_line_message(message: str):
    """
    發送 Line 推播訊息

    Args:
        message (str): 要發送的訊息內容
    """
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.getenv("LINE_USER_ID")

    if not token or not user_id:
        print("⚠️  Line Token 或 User ID 未設定，無法發送通知")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    try:
        response = requests.post(LINE_API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        print("✓ Line 通知已發送")
    except requests.exceptions.RequestException as e:
        print(f"❌ Line 通知發送失敗: {e}")
        # 列印部分錯誤資訊，幫助排查
        if e.response is not None:
            print(f"   - Status Code: {e.response.status_code}")
            print(f"   - Response: {e.response.text}")

