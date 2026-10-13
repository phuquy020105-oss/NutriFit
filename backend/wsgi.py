import sys
import os

# Đảm bảo đường dẫn import app chính xác
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app

app = create_app()

if __name__ == '__main__':
    host = os.getenv('NUTRIFIT_BACKEND_HOST', '127.0.0.1')
    print(f'NutriFit Backend đang chạy tại http://{host}:5000')
    app.run(host=host, port=5000, debug=os.getenv('NUTRIFIT_FLASK_DEBUG', 'false').lower() == 'true')