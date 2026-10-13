r"""Chẩn đoán Chat AI và bóng rổ mà KHÔNG in hoặc gửi thông tin bí mật lên Terminal.

Chạy tại NutriFit-NextUI:
    ..\.venv\Scripts\python.exe backend\check_ai_connection.py --user-id 7
"""
import argparse
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=True)
BASE = os.getenv("NUTRIFIT_LOCAL_API", "http://127.0.0.1:5000").rstrip("/")


def probe_server(user_id):
    print("\n1) Kiểm tra Backend Flask:")
    try:
        resp = requests.get(BASE + "/api/health", timeout=5)
        data = resp.json()
        print("   HTTP:", resp.status_code, "| build:", data.get("build", "BẢN CŨ / CHƯA CẬP NHẬT"))
        if data.get("build") != "ai-workout-chat-20261014":
            print("   => Backend cổng 5000 vẫn có thể đang chạy bản cũ. Dừng Flask và chạy lại.")
    except (requests.RequestException, ValueError):
        print("   KHÔNG KẾT NỐI ĐƯỢC. Cần mở Backend Flask ở cổng 5000.")
        return

    print("\n2) Kiểm tra môn bóng rổ (không cần Gemini):")
    try:
        resp = requests.post(BASE + "/api/workouts/estimate", json={
            "user_id": user_id,
            "name": "bóng rổ",
            "duration_minutes": 30,
        }, timeout=15)
        data = resp.json()
        if resp.ok and data.get("success"):
            item = data.get("data") or {}
            print("   ĐẠT | nguồn:", item.get("source"), "| MET:", item.get("met"),
                  "| kcal:", item.get("calories_burned"))
        else:
            print("   LỖI | HTTP:", resp.status_code, "|", str(data.get("message", ""))[:180])
    except (requests.RequestException, ValueError) as exc:
        print("   LỖI KẾT NỐI/PHẢN HỒI:", type(exc).__name__)


def probe_gemini():
    print("\n3) Kiểm tra Gemini trực tiếp (tốn rất ít token):")
    key = (os.getenv("GEMINI_API_KEY") or "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()
    print("   API key:", "đã cấu hình" if key else "THIẾU", "| model:", model)
    if not key:
        return
    try:
        from google import genai
        from google.genai import types
        with genai.Client(api_key=key,
                          http_options=types.HttpOptions(timeout=20000)) as client:
            result = client.models.generate_content(
                model=model, contents="Chỉ trả lời: OK",
                config=types.GenerateContentConfig(max_output_tokens=64)
            )
        print("   ĐẠT | phản hồi:", (result.text or "(trống)").strip()[:40])
    except Exception as exc:
        status = getattr(exc, "code", None)
        if status is None:
            status = getattr(exc, "status_code", None)
        try:
            status = int(status)
        except (TypeError, ValueError):
            status = None
        print("   LỖI | status:", status, "| loại:", type(exc).__name__)
        if status == 429:
            print("   => Hết hạn mức hoặc quá nhiều yêu cầu Gemini; kiểm tra quota trong AI Studio.")
        elif status in (401, 403):
            print("   => Khóa API không có quyền hoặc đã bị thu hồi; cần tạo khóa mới.")
        elif status == 404:
            print("   => Model không khả dụng với khóa đang dùng.")
        elif status == 503:
            print("   => Gemini đang quá tải hoặc tạm thời gián đoạn; thử lại sau.")
        elif status == 400:
            print("   => Kiểm tra model và cấu hình SDK hoặc loại API key.")
        else:
            print("   => Kiểm tra mạng, thời gian chờ và cài đặt google-genai.")
        print("   (Không hiển thị nội dung lỗi để tránh lộ API key.)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, default=7)
    args = parser.parse_args()
    probe_server(args.user_id)
    probe_gemini()
