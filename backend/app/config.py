import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Tìm chính xác thư mục gốc chứa file .env
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / '.env'
load_dotenv(dotenv_path=ENV_PATH)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'nutrifit-secret-key-2026')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASS = os.getenv('DB_PASS', '123456')
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'NutriFitDB')

    # Mã hóa ký tự đặc biệt như @ trong mật khẩu (Quy020105@ -> Quy020105%40)
    encoded_pass = quote_plus(DB_PASS) if DB_PASS else ''
    auth_part = f"{DB_USER}:{encoded_pass}" if encoded_pass else DB_USER

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{auth_part}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False