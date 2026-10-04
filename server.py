import sys
import os

# Đảm bảo in console UTF-8 trên Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
import re
from werkzeug.security import generate_password_hash, check_password_hash
import json
import requests
import random
from datetime import date, datetime, timedelta

app = Flask(__name__)
CORS(app)

# Kết nối MySQL bằng biến môi trường (phù hợp local + cloud).
# Không hard-code mật khẩu hoặc API key vào source code.
DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DATABASE", "NutriFitDB"),
}

class CompatCursor:
    """Lớp tương thích nhỏ để giữ nguyên phần lớn SQL cũ khi chuyển pyodbc -> MySQL."""
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql, *params):
        sql = sql.strip()
        top = re.match(r"(?is)^SELECT\s+TOP\s+(\d+)\s+", sql)
        limit = None
        if top:
            limit = int(top.group(1))
            sql = re.sub(r"(?is)^SELECT\s+TOP\s+\d+\s+", "SELECT ", sql, count=1)
        sql = sql.replace("GETDATE()", "NOW()")
        sql = sql.replace("SELECT @@IDENTITY", "SELECT LAST_INSERT_ID()")
        sql = sql.replace("?", "%s")
        if limit is not None:
            sql = sql.rstrip().rstrip(";") + f" LIMIT {limit}"
        if len(params) == 0:
            return self._cursor.execute(sql)
        if len(params) == 1 and isinstance(params[0], (tuple, list, dict)):
            bind = params[0]
        else:
            bind = params
        return self._cursor.execute(sql, bind)

    def __getattr__(self, name):
        return getattr(self._cursor, name)

class CompatConnection:
    def __init__(self, connection):
        self._connection = connection
    def cursor(self):
        return CompatCursor(self._connection.cursor())
    def __getattr__(self, name):
        return getattr(self._connection, name)

def get_db():
    return CompatConnection(mysql.connector.connect(**DB_CONFIG, autocommit=True))

# Lấy Gemini API Key từ biến môi trường hoặc file config nếu có
GEMINI_API_KEY_ENV = os.environ.get("GEMINI_API_KEY", "")

# ============================================================================
# LOGIC GỢI Ý MÓN ĂN VIỆT NAM (ĐA DẠNG 7 NGÀY & AI GEMINI FLASH)
# ============================================================================
from vietnamese_menus import (
    WEEKDAY_NAMES_VI,
    WEEKLY_VIETNAMESE_MENUS,
    generate_expert_fallback_meals,
    build_gemini_prompt
)

def call_gemini_api(prompt, user_api_key=None):
    """
    Gọi Gemini API (thử các model mới nhất gemini-2.5-flash, gemini-2.0-flash, gemini-1.5-flash)
    Nhiệt độ 0.85 giúp món ăn mỗi ngày phong phú, không lặp lại!
    """
    api_key = user_api_key or GEMINI_API_KEY_ENV
    if not api_key:
        return None

    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash"
    ]

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.85,
                "topP": 0.9,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json"
            }
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data['candidates'][0]['content']['parts'][0]['text']
                # Clean up if markdown fences exist
                cleaned = raw_text.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                parsed = json.loads(cleaned.strip())
                if isinstance(parsed, list) and len(parsed) >= 3:
                    return parsed[:3]
        except Exception as e:
            print(f"Lỗi khi gọi model {model}: {e}")
            continue

    return None

# ============================================================================
# API ENDPOINTS
# ============================================================================

# 1. API Kiểm tra kết nối MySQL
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        cnxn = get_db()
        cursor = cnxn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Users")
        user_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM Workouts")
        workout_count = cursor.fetchone()[0]
        cnxn.close()
        return jsonify({
            "status": "connected",
            "database": "NutriFitDB",
            "server": "MySQL",
            "usersCount": user_count,
            "workoutsCount": workout_count,
            "hasGeminiKey": bool(GEMINI_API_KEY_ENV),
            "message": "Kết nối MySQL thành công!"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Lỗi kết nối MySQL: {str(e)}"
        }), 500

# 2. API Đăng nhập
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"success": False, "message": "Vui lòng nhập email và mật khẩu."}), 400

    try:
        cnxn = get_db()
        cursor = cnxn.cursor()
        cursor.execute("""
            SELECT UserId, Email, PasswordHash, FullName 
            FROM Users 
            WHERE LOWER(RTRIM(LTRIM(Email))) = LOWER(?) 
               OR LOWER(RTRIM(LTRIM(FullName))) = LOWER(?)
        """, (email, email))
        row = cursor.fetchone()
        
        if not row:
            cnxn.close()
            return jsonify({"success": False, "message": "Tài khoản không tồn tại trên CSDL!"}), 404
        
        user_id, user_email, pwd_hash, fullname = row
        stored = (pwd_hash or '').strip()
        is_hashed = stored.startswith(('scrypt:', 'pbkdf2:'))
        password_ok = check_password_hash(stored, password) if is_hashed else (stored == password.strip())
        if not password_ok:
            cnxn.close()
            return jsonify({"success": False, "message": "Mật khẩu không chính xác!"}), 401
        # Tự nâng cấp tài khoản cũ đang lưu plain-text sang password hash sau lần đăng nhập hợp lệ.
        if not is_hashed:
            cursor.execute("UPDATE Users SET PasswordHash = ? WHERE UserId = ?", generate_password_hash(password), user_id)

        cursor.execute("SELECT TOP 1 * FROM UserProfiles WHERE UserId = ?", user_id)
        profile_row = cursor.fetchone()
        profile = None
        if profile_row:
            cols = [col[0] for col in cursor.description]
            profile = dict(zip(cols, profile_row))

        cnxn.close()
        return jsonify({
            "success": True,
            "message": "Đăng nhập thành công!",
            "user": {
                "id": user_id,
                "email": user_email,
                "fullname": fullname
            },
            "profile": profile
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 3. API Đăng ký
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')
    fullname = data.get('fullname', '').strip() or "Thành viên NutriFit"

    if not email or len(password) < 6:
        return jsonify({"success": False, "message": "Email hợp lệ và mật khẩu tối thiểu 6 ký tự."}), 400

    try:
        cnxn = get_db()
        cursor = cnxn.cursor()
        cursor.execute("SELECT UserId FROM Users WHERE Email = ?", email)
        if cursor.fetchone():
            cnxn.close()
            return jsonify({"success": False, "message": "Email này đã được đăng ký trên CSDL!"}), 400

        cursor.execute("INSERT INTO Users (Email, PasswordHash, FullName) VALUES (?, ?, ?)", email, generate_password_hash(password), fullname)
        cursor.execute("SELECT @@IDENTITY")
        new_id = int(cursor.fetchone()[0])
        cnxn.close()

        return jsonify({
            "success": True,
            "message": "Đăng ký tài khoản thành công!",
            "user": {
                "id": new_id,
                "email": email,
                "fullname": fullname
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 4. API Lưu hồ sơ thể trạng
@app.route('/api/profile/save', methods=['POST'])
def save_profile():
    data = request.json or {}
    user_id = data.get('userId')
    if not user_id:
        return jsonify({"success": False, "message": "Thiếu UserId."}), 400

    try:
        height = float(data.get('height', 172))
        weight = float(data.get('weight', 68))
        age = int(data.get('age', 24))
        if height < 100 or height > 250:
            return jsonify({"success": False, "message": "Chiều cao không hợp lý (từ 100 đến 250 cm)."}), 400
        if weight < 30 or weight > 250:
            return jsonify({"success": False, "message": "Cân nặng không hợp lý (từ 30 đến 250 kg)."}), 400
        if age < 12 or age > 95:
            return jsonify({"success": False, "message": "Độ tuổi không hợp lý (từ 12 đến 95 tuổi)."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Số liệu thể trạng không đúng định dạng số."}), 400

    try:
        cnxn = get_db()
        cursor = cnxn.cursor()
        cursor.execute("SELECT ProfileId FROM UserProfiles WHERE UserId = ?", user_id)
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE UserProfiles
                SET Gender=?, Age=?, HeightCm=?, WeightKg=?, ActivityLevel=?, Goal=?,
                    Bmr=?, Tdee=?, TargetKcal=?, TargetCarbs=?, TargetProtein=?, TargetFat=?,
                    TargetFiber=?, TargetWaterMl=?, UpdatedAt=GETDATE()
                WHERE UserId = ?
            """, data.get('gender'), data.get('age'), data.get('height'), data.get('weight'),
                 data.get('activity'), data.get('goal'), data.get('bmr'), data.get('tdee'),
                 data.get('targetKcal'), data.get('carbs'), data.get('protein'), data.get('fat'),
                 data.get('fiber'), data.get('waterTarget'), user_id)
        else:
            cursor.execute("""
                INSERT INTO UserProfiles (UserId, Gender, Age, HeightCm, WeightKg, ActivityLevel, Goal,
                                          Bmr, Tdee, TargetKcal, TargetCarbs, TargetProtein, TargetFat,
                                          TargetFiber, TargetWaterMl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, user_id, data.get('gender'), data.get('age'), data.get('height'), data.get('weight'),
                 data.get('activity'), data.get('goal'), data.get('bmr'), data.get('tdee'),
                 data.get('targetKcal'), data.get('carbs'), data.get('protein'), data.get('fat'),
                 data.get('fiber'), data.get('waterTarget'))
        
        cnxn.close()
        return jsonify({"success": True, "message": "Đã lưu hồ sơ thể trạng vào MySQL!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 5. API DANH MỤC BÀI TẬP VÀ LẬP LỊCH TẬP (WORKOUT PLANNING & TRACKING)
# ============================================================================

# 5.1. Lấy danh sách bài tập (Có sẵn + Tùy chỉnh của người dùng)
@app.route('/api/workouts', methods=['GET'])
def get_workouts():
    user_id = request.args.get('userId', type=int)
    try:
        cnxn = get_db()
        cursor = cnxn.cursor()
        if user_id:
            cursor.execute("""
                SELECT WorkoutId, WorkoutName, DurationMinutes, CaloriesBurned, Category, IsCustom, CreatedBy 
                FROM Workouts 
                WHERE IsCustom = 0 OR CreatedBy = ? 
                ORDER BY IsCustom ASC, WorkoutId DESC
            """, user_id)
        else:
            cursor.execute("""
                SELECT WorkoutId, WorkoutName, DurationMinutes, CaloriesBurned, Category, IsCustom, CreatedBy 
                FROM Workouts 
                WHERE IsCustom = 0 
                ORDER BY WorkoutName ASC
            """)

        workouts = []
        for row in cursor.fetchall():
            workouts.append({
                "id": row[0],
                "name": row[1],
                "durationMinutes": int(row[2]),
                "caloriesBurned": float(row[3]),
                "category": row[4] or "Khác",
                "isCustom": bool(row[5]),
                "createdBy": row[6]
            })
        cnxn.close()
        return jsonify({"success": True, "workouts": workouts})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 5.2. Thêm hoạt động tùy chỉnh do người dùng tự nhập (Đáp ứng yêu cầu feature.txt)
@app.route('/api/workouts', methods=['POST'])
def create_custom_workout():
    data = request.json or {}
    user_id = data.get('userId')
    name = (data.get('name') or '').strip()
    duration = data.get('durationMinutes')
    calories = data.get('caloriesBurned')
    category = (data.get('category') or 'Tự chọn').strip()

    if not user_id:
        return jsonify({"success": False, "message": "Thiếu UserId."}), 400
    if not name:
        return jsonify({"success": False, "message": "Vui lòng nhập tên hoạt động tập luyện."}), 400
    
    try:
        duration = int(duration)
        if duration <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Thời gian tập luyện phải là số nguyên phút lớn hơn 0."}), 400

    try:
        calories = float(calories)
        if calories <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Lượng calo đốt được phải là số dương lớn hơn 0."}), 400

    try:
        cnxn = get_db()
        cursor = cnxn.cursor()
        cursor.execute("""
            INSERT INTO Workouts (WorkoutName, DurationMinutes, CaloriesBurned, Category, IsCustom, CreatedBy)
            VALUES (?, ?, ?, ?, 1, ?)
        """, name, duration, calories, category, user_id)
        cursor.execute("SELECT @@IDENTITY")
        new_id = int(cursor.fetchone()[0])
        cnxn.close()

        return jsonify({
            "success": True,
            "message": f"Đã thêm hoạt động '{name}' vào danh mục bài tập thành công!",
            "workout": {
                "id": new_id,
                "name": name,
                "durationMinutes": duration,
                "caloriesBurned": calories,
                "category": category,
                "isCustom": True,
                "createdBy": user_id
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 5.2.1. Xóa hoạt động tùy chỉnh do người dùng tự tạo
@app.route('/api/workouts/<int:workout_id>', methods=['DELETE'])
def delete_custom_workout(workout_id):
    user_id = request.args.get('userId', type=int)
    if not user_id:
        return jsonify({"success": False, "message": "Thiếu UserId."}), 400

    try:
        cnxn = get_db()
        cursor = cnxn.cursor()
        # Chỉ cho phép xóa hoạt động do chính user đó tạo
        cursor.execute("SELECT WorkoutName FROM Workouts WHERE WorkoutId = ? AND IsCustom = 1 AND CreatedBy = ?", workout_id, user_id)
        row = cursor.fetchone()
        if not row:
            cnxn.close()
            return jsonify({"success": False, "message": "Không tìm thấy hoạt động tùy chỉnh này hoặc bạn không có quyền xóa."}), 404
        
        name = row[0]
        # Xóa các lịch sử ghi nhận liên quan trước
        cursor.execute("DELETE FROM WorkoutLogs WHERE WorkoutId = ? AND UserId = ?", workout_id, user_id)
        # Xóa bài tập
        cursor.execute("DELETE FROM Workouts WHERE WorkoutId = ? AND IsCustom = 1 AND CreatedBy = ?", workout_id, user_id)
        cnxn.close()

        return jsonify({
            "success": True,
            "message": f"Đã xóa hoạt động '{name}' khỏi danh mục thành công!"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 5.3. Ghi nhận một buổi tập vào CSDL (WorkoutLogs)
@app.route('/api/workouts/log', methods=['POST'])
def log_workout():
    data = request.json or {}
    user_id = data.get('userId')
    workout_id = data.get('workoutId')
    duration = data.get('durationMinutes')
    calories = data.get('caloriesBurned')
    logged_date = data.get('loggedDate') or date.today().isoformat()

    if not user_id or not workout_id:
        return jsonify({"success": False, "message": "Thiếu UserId hoặc WorkoutId."}), 400

    try:
        cnxn = get_db()
        cursor = cnxn.cursor()

        # Nếu không truyền duration hoặc calories, lấy mặc định từ bảng Workouts
        if duration is None or calories is None:
            cursor.execute("SELECT DurationMinutes, CaloriesBurned, WorkoutName FROM Workouts WHERE WorkoutId = ?", workout_id)
            w_row = cursor.fetchone()
            if not w_row:
                cnxn.close()
                return jsonify({"success": False, "message": "Bài tập không tồn tại!"}), 404
            if duration is None:
                duration = w_row[0]
            if calories is None:
                calories = w_row[1]
            workout_name = w_row[2]
        else:
            cursor.execute("SELECT WorkoutName FROM Workouts WHERE WorkoutId = ?", workout_id)
            w_row = cursor.fetchone()
            workout_name = w_row[0] if w_row else "Bài tập"

        cursor.execute("""
            INSERT INTO WorkoutLogs (UserId, WorkoutId, LoggedDate, DurationMinutes, CaloriesBurned)
            VALUES (?, ?, ?, ?, ?)
        """, user_id, workout_id, logged_date, int(duration), float(calories))
        cursor.execute("SELECT @@IDENTITY")
        new_log_id = int(cursor.fetchone()[0])
        cnxn.close()

        return jsonify({
            "success": True,
            "message": f"Đã ghi nhận buổi tập '{workout_name}' thành công!",
            "logId": new_log_id,
            "data": {
                "logId": new_log_id,
                "workoutId": workout_id,
                "workoutName": workout_name,
                "loggedDate": logged_date,
                "durationMinutes": int(duration),
                "caloriesBurned": float(calories)
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 5.4. Lấy lịch sử các buổi tập đã ghi nhận
@app.route('/api/workouts/logs', methods=['GET'])
def get_workout_logs():
    user_id = request.args.get('userId', type=int, default=1)
    limit = request.args.get('limit', type=int, default=50)

    try:
        cnxn = get_db()
        cursor = cnxn.cursor()
        cursor.execute(f"""
            SELECT TOP {limit} l.LogId, l.LoggedDate, l.DurationMinutes, l.CaloriesBurned, l.CreatedAt,
                   w.WorkoutName, w.Category, w.IsCustom, w.WorkoutId
            FROM WorkoutLogs l
            JOIN Workouts w ON l.WorkoutId = w.WorkoutId
            WHERE l.UserId = ?
            ORDER BY l.LoggedDate DESC, l.LogId DESC
        """, user_id)

        logs = []
        for row in cursor.fetchall():
            logs.append({
                "logId": row[0],
                "date": str(row[1]),
                "durationMinutes": int(row[2]),
                "caloriesBurned": float(row[3]),
                "createdAt": row[4].strftime("%H:%M %d/%m/%Y") if row[4] else "",
                "workoutName": row[5],
                "category": row[6] or "Khác",
                "isCustom": bool(row[7]),
                "workoutId": row[8]
            })
        cnxn.close()
        return jsonify({"success": True, "logs": logs})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 5.5. Xóa 1 bản ghi lịch sử tập luyện
@app.route('/api/workouts/log/<int:log_id>', methods=['DELETE'])
def delete_workout_log(log_id):
    user_id = request.args.get('userId', type=int, default=1)
    try:
        cnxn = get_db()
        cursor = cnxn.cursor()
        cursor.execute("DELETE FROM WorkoutLogs WHERE LogId = ? AND UserId = ?", log_id, user_id)
        cnxn.close()
        return jsonify({"success": True, "message": "Đã xóa bản ghi tập luyện."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 5.6. Thống kê tần suất tập luyện 7 ngày gần nhất để vẽ biểu đồ trực quan hóa (feature.txt)
@app.route('/api/workouts/stats', methods=['GET'])
def get_workout_stats():
    user_id = request.args.get('userId', type=int, default=1)
    try:
        today = date.today()
        start_date = today - timedelta(days=6)
        
        cnxn = get_db()
        cursor = cnxn.cursor()
        cursor.execute("""
            SELECT LoggedDate, COUNT(*) as SessionCount, SUM(DurationMinutes) as TotalDuration, SUM(CaloriesBurned) as TotalCalories
            FROM WorkoutLogs
            WHERE UserId = ? AND LoggedDate >= ? AND LoggedDate <= ?
            GROUP BY LoggedDate
        """, user_id, start_date.isoformat(), today.isoformat())

        stats_map = {}
        for row in cursor.fetchall():
            d_str = str(row[0])
            stats_map[d_str] = {
                "count": int(row[1]),
                "duration": int(row[2] or 0),
                "calories": float(row[3] or 0)
            }
        cnxn.close()

        weekday_names = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
        days = []
        total_sessions = 0
        total_minutes = 0
        total_calories = 0
        active_days = 0

        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            d_str = d.isoformat()
            label = f"{weekday_names[d.weekday()]} {d.strftime('%d/%m')}"
            data = stats_map.get(d_str, {"count": 0, "duration": 0, "calories": 0.0})
            
            if data["count"] > 0:
                active_days += 1
            total_sessions += data["count"]
            total_minutes += data["duration"]
            total_calories += data["calories"]

            days.append({
                "date": d_str,
                "label": label,
                "count": data["count"],
                "duration": data["duration"],
                "calories": round(data["calories"], 1)
            })

        return jsonify({
            "success": True,
            "stats": {
                "days": days,
                "summary": {
                    "totalSessions": total_sessions,
                    "totalMinutes": total_minutes,
                    "totalCalories": round(total_calories, 1),
                    "activeDays": active_days
                }
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ============================================================================
# 6. API GỢI Ý MÓN ĂN (MEAL SUGGESTIONS) - ĐÁP ỨNG TRỌN VẸN FEATURE.TXT & 3 YÊU CẦU
# ============================================================================

def clean_meal_options(options):
    """Xóa bỏ hoàn toàn tiền tố 'Mâm cơm' khỏi tiêu đề món ăn"""
    if not options or not isinstance(options, list):
        return options
    for opt in options:
        if isinstance(opt, dict) and "title" in opt:
            title = str(opt["title"]).strip()
            for prefix in ["Mâm cơm ", "mâm cơm ", "Mâm Cơm ", "MÂM CƠM ", "Mâm cơm: ", "Mâm Cơm: "]:
                if title.startswith(prefix):
                    title = title[len(prefix):].strip()
            opt["title"] = title
    return options

@app.route('/api/meals/today', methods=['GET'])
def get_today_meals():
    """
    Lấy thực đơn gợi ý hôm nay (trưa + tối) của người dùng từ CSDL SQL Server
    """
    user_id = request.args.get('userId', type=int, default=1)
    today = date.today().isoformat()

    try:
        cnxn = get_db()
        cursor = cnxn.cursor()
        cursor.execute("""
            SELECT SuggestionId, MealType, OptionsJson, SelectedOption, Status, SuggestionDate
            FROM MealSuggestions
            WHERE UserId = ? AND SuggestionDate = ?
        """, user_id, today)
        rows = cursor.fetchall()

        results = {'lunch': None, 'dinner': None}
        for row in rows:
            m_type = row[1]
            options = clean_meal_options(json.loads(row[2]))
            results[m_type] = {
                "suggestionId": row[0],
                "mealType": m_type,
                "options": options,
                "selectedOption": row[3],
                "status": row[4],
                "date": str(row[5])
            }
        cnxn.close()
        return jsonify({"success": True, "todayMeals": results})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/meals/generate', methods=['POST'])
def generate_meal():
    """
    Sinh 3 options món ăn bằng Gemini Flash AI (hoặc fallback chuyên gia).
    Nếu ngày hôm đó đã có gợi ý cho bữa này rồi thì trả về dữ liệu cũ, không sinh thêm!
    """
    data = request.json or {}
    user_id = data.get('userId', 1)
    meal_type = data.get('mealType', 'lunch') # 'lunch' hoặc 'dinner'
    api_key = data.get('apiKey', '').strip() or GEMINI_API_KEY_ENV
    force_refresh = data.get('forceRefresh', False)
    today = date.today().isoformat()

    try:
        cnxn = get_db()
        cursor = cnxn.cursor()

        # 1. Kiểm tra xem hôm nay đã có gợi ý cho bữa này chưa
        cursor.execute("""
            SELECT SuggestionId, OptionsJson, SelectedOption, Status
            FROM MealSuggestions
            WHERE UserId = ? AND SuggestionDate = ? AND MealType = ?
        """, user_id, today, meal_type)
        existing = cursor.fetchone()

        if existing and not force_refresh:
            cnxn.close()
            return jsonify({
                "success": True,
                "isNew": False,
                "message": f"Đã nạp thực đơn {meal_type} cố định trong ngày từ CSDL.",
                "data": {
                    "suggestionId": existing[0],
                    "mealType": meal_type,
                    "options": clean_meal_options(json.loads(existing[1])),
                    "selectedOption": existing[2],
                    "status": existing[3]
                }
            })

        # 2. Lấy hồ sơ thể trạng của user để cung cấp context cho AI
        cursor.execute("SELECT TOP 1 * FROM UserProfiles WHERE UserId = ?", user_id)
        profile_row = cursor.fetchone()
        user_profile = {}
        if profile_row:
            cols = [col[0] for col in cursor.description]
            user_profile = dict(zip(cols, profile_row))

        # 3. Lấy các món đã gợi ý trong những ngày gần đây để tránh trùng lặp
        cursor.execute("""
            SELECT TOP 5 OptionsJson FROM MealSuggestions 
            WHERE UserId = ? AND MealType = ? 
            ORDER BY SuggestionDate DESC
        """, user_id, meal_type)
        recent_rows = cursor.fetchall()
        recent_titles = []
        for r_row in recent_rows:
            try:
                parsed_opts = json.loads(r_row[0])
                for p_opt in parsed_opts:
                    if p_opt.get('title'):
                        recent_titles.append(f"• {p_opt['title']}")
            except Exception:
                pass
        recent_meals_str = "\n".join(recent_titles[:10]) if recent_titles else ""

        # 4. Tạo prompt và gọi Gemini Flash AI
        prompt = build_gemini_prompt(user_profile, meal_type, target_date_str=today, recent_meals_str=recent_meals_str)
        options = None
        source = "AI Gemini Flash (Đa Dạng Hóa Từng Ngày)"

        if api_key:
            options = call_gemini_api(prompt, api_key)

        if not options:
            shift_days = random.randint(1, 6) if force_refresh else 0
            options = generate_expert_fallback_meals(user_profile, meal_type, target_date=today, shift_days=shift_days)
            source = "Chuyên gia Dinh dưỡng NutriFit (Thực đơn 7 ngày xoay vòng)"

        options = clean_meal_options(options)
        options_json = json.dumps(options, ensure_ascii=False)

        # 4. Lưu vào bảng MealSuggestions trong SQL Server
        if existing:
            cursor.execute("""
                UPDATE MealSuggestions
                SET OptionsJson = ?, Status = 'pending', SelectedOption = NULL, UpdatedAt = GETDATE()
                WHERE SuggestionId = ?
            """, options_json, existing[0])
            sug_id = existing[0]
        else:
            cursor.execute("""
                INSERT INTO MealSuggestions (UserId, SuggestionDate, MealType, OptionsJson, SelectedOption, Status)
                VALUES (?, ?, ?, ?, NULL, 'pending')
            """, user_id, today, meal_type, options_json)
            cursor.execute("SELECT @@IDENTITY")
            sug_id = int(cursor.fetchone()[0])

        cnxn.close()
        return jsonify({
            "success": True,
            "isNew": True,
            "source": source,
            "message": f"Gợi ý 3 thực đơn bữa {meal_type} thành công!",
            "data": {
                "suggestionId": sug_id,
                "mealType": meal_type,
                "options": options,
                "selectedOption": None,
                "status": "pending"
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/meals/select', methods=['POST'])
def select_meal_option():
    """
    Xử lý việc người dùng chọn 1 trong 3 option HOẶC chọn NÚT THỨ 4 (Suy nghĩ / Quyết định sau).
    Yêu cầu: Không thêm bất kỳ lựa chọn nào ngoài 3 lựa chọn ban đầu.
    """
    data = request.json or {}
    user_id = data.get('userId', 1)
    meal_type = data.get('mealType', 'lunch')
    selected_option = data.get('selectedOption') # 1, 2, 3 hoặc null / 'think_later'
    today = date.today().isoformat()

    try:
        cnxn = get_db()
        cursor = cnxn.cursor()

        # Nút thứ 4: Để tôi suy nghĩ / Quyết định sau
        if selected_option is None or str(selected_option).lower() in ['think_later', 'null', '0', '']:
            new_status = 'pending'
            sel_opt = None
            msg = "Đã lưu trạng thái: 'Đang cân nhắc'. 3 lựa chọn ban đầu vẫn được giữ nguyên cho bạn!"
        else:
            new_status = 'decided'
            sel_opt = int(selected_option)
            msg = f"Đã chốt lựa chọn {sel_opt} cho bữa {meal_type}!"

        cursor.execute("""
            UPDATE MealSuggestions
            SET SelectedOption = ?, Status = ?, UpdatedAt = GETDATE()
            WHERE UserId = ? AND SuggestionDate = ? AND MealType = ?
        """, sel_opt, new_status, user_id, today, meal_type)

        cnxn.close()
        return jsonify({
            "success": True,
            "status": new_status,
            "selectedOption": sel_opt,
            "message": msg
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/meals/history', methods=['GET'])
def get_meal_history():
    """
    Lấy lịch sử các lựa chọn thực đơn theo ngày để tra cứu lại
    """
    user_id = request.args.get('userId', type=int, default=1)
    try:
        cnxn = get_db()
        cursor = cnxn.cursor()
        cursor.execute("""
            SELECT SuggestionId, SuggestionDate, MealType, OptionsJson, SelectedOption, Status
            FROM MealSuggestions
            WHERE UserId = ?
            ORDER BY SuggestionDate DESC, MealType DESC
        """, user_id)

        history = []
        for row in cursor.fetchall():
            options = clean_meal_options(json.loads(row[3]))
            chosen_meal = None
            if row[4] and 1 <= row[4] <= len(options):
                chosen_meal = options[row[4] - 1]

            history.append({
                "suggestionId": row[0],
                "date": str(row[1]),
                "mealType": row[2],
                "selectedOption": row[4],
                "status": row[5],
                "chosenMeal": chosen_meal,
                "allOptions": options
            })
        cnxn.close()
        return jsonify({"success": True, "history": history})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ============================================================================
# KHỞI CHẠY SERVER
# ============================================================================
# ============================================================================
# FRONTEND: phục vụ cùng domain với API để deploy chỉ cần 1 Web Service
# ============================================================================
@app.route('/')
def serve_frontend():
    return send_from_directory(app.root_path, 'index.html')

@app.route('/<path:path>')
def serve_frontend_files(path):
    return send_from_directory(app.root_path, path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    print(f"NutriFit Backend Server is running on port {port} ...")
    app.run(host='0.0.0.0', port=port, debug=False)
