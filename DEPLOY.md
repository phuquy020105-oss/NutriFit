# NutriFit - bản chuẩn bị deploy

Bản này đã được đổi từ SQL Server/pyodbc sang MySQL, frontend dùng `/api` cùng domain, Flask phục vụ luôn frontend, và port lấy từ biến môi trường `PORT`.

## Biến môi trường bắt buộc
- `MYSQL_HOST`
- `MYSQL_PORT` (thường 3306)
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

Tùy chọn: `GEMINI_API_KEY`.

## Database
Chạy `schema_cloud.sql` trên MySQL cloud một lần. File tạo 5 bảng và seed 18 workout mặc định.

## Chạy local
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export MYSQL_PASSWORD='...'
python server.py
```
Mở `http://localhost:5000` (không cần chạy thêm HTTP server port 8000 ở bản deploy này).

## Production
Start command:
```bash
gunicorn --bind 0.0.0.0:$PORT server:app
```

Không commit `.env`, mật khẩu database hoặc Gemini API key lên GitHub.
