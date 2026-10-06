import sys
import os

# Đảm bảo đường dẫn import app chính xác
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("NutriFit Backend đang chạy tại http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)