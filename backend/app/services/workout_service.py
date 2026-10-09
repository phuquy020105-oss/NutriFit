"""Nghiệp vụ Workout (TV4): danh mục, bài tập tùy chỉnh, nhật ký, mục tiêu tuần.

Dùng SQL thô qua db.session nên không phụ thuộc models/. Các hàm ghi dữ liệu trả về
(kết_quả, lỗi) giống AuthService của TV1.
"""
from datetime import date, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

CUSTOM_CATEGORY_ID = 5        # 'Tự chọn'
DEFAULT_WEIGHT_KG = 60.0      # dùng khi user chưa có hồ sơ thể trạng
MAX_MINUTES = 600
DEFAULT_GOAL = {"weekly_sessions_target": 4, "weekly_calories_target": 1200.0}


# ---------- Hàm thuần (dễ test) ----------
def calc_calories_met(met, weight_kg, minutes):
    """Calo tiêu hao = MET x cân nặng (kg) x giờ."""
    return round(float(met) * float(weight_kg) * float(minutes) / 60.0, 1)


def scale_calories(base_kcal, base_minutes, minutes):
    """Quy đổi calo theo thời lượng thực tế so với thời lượng chuẩn của bài tập."""
    if not base_minutes or base_minutes <= 0:
        return 0.0
    return round(float(base_kcal) * float(minutes) / float(base_minutes), 1)


def parse_date(value, default=None):
    """Nhận date/datetime/chuỗi 'YYYY-MM-DD'. Sai định dạng -> ValueError."""
    if value in (None, ""):
        return default
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _valid_minutes(value):
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        return None
    return minutes if 1 <= minutes <= MAX_MINUTES else None


# ---------- Danh mục ----------
def get_user_weight(user_id):
    row = db.session.execute(
        text("SELECT WeightKg FROM UserProfiles WHERE UserId = :uid"), {"uid": user_id}
    ).first()
    return float(row[0]) if row and row[0] else None


def list_catalog(user_id=None):
    """Danh mục bài tập chuẩn + bài tùy chỉnh của user, gom theo nhóm."""
    rows = db.session.execute(text(
        "SELECT w.WorkoutId, w.CategoryId, c.CategoryName, c.IconName, w.WorkoutName, "
        "w.DurationMinutes, w.CaloriesBurned, w.IsCustom "
        "FROM Workouts w LEFT JOIN WorkoutCategories c ON c.CategoryId = w.CategoryId "
        "WHERE w.IsCustom = 0 OR w.CreatedBy = :uid "
        "ORDER BY w.CategoryId, w.WorkoutId"
    ), {"uid": user_id}).fetchall()

    groups, order = {}, []
    for r in rows:
        key = r.CategoryId
        if key not in groups:
            groups[key] = {"category_id": key, "name": r.CategoryName or "Khác",
                           "icon": r.IconName, "workouts": []}
            order.append(key)
        groups[key]["workouts"].append({
            "id": r.WorkoutId, "name": r.WorkoutName,
            "duration_minutes": r.DurationMinutes,
            "calories_burned": float(r.CaloriesBurned),
            "is_custom": bool(r.IsCustom),
        })
    return [groups[k] for k in order]


def create_custom_workout(user_id, name, duration_minutes, category_id=None,
                          calories_burned=None, met=None):
    name = (name or "").strip()
    if not name or len(name) > 150:
        return None, "Tên bài tập không hợp lệ (1-150 ký tự)."
    minutes = _valid_minutes(duration_minutes)
    if minutes is None:
        return None, f"Thời lượng phải từ 1 đến {MAX_MINUTES} phút."

    if calories_burned is not None:
        try:
            kcal = float(calories_burned)
        except (TypeError, ValueError):
            return None, "Calo tiêu hao không hợp lệ."
        if kcal < 0:
            return None, "Calo tiêu hao không được âm."
    elif met is not None:
        try:
            met_value = float(met)
        except (TypeError, ValueError):
            return None, "Chỉ số MET không hợp lệ."
        if not 0 < met_value <= 25:
            return None, "MET phải trong khoảng (0, 25]."
        kcal = calc_calories_met(met_value, get_user_weight(user_id) or DEFAULT_WEIGHT_KG, minutes)
    else:
        return None, "Cần nhập calo tiêu hao hoặc chỉ số MET."

    try:
        result = db.session.execute(text(
            "INSERT INTO Workouts (CategoryId, WorkoutName, DurationMinutes, CaloriesBurned, IsCustom, CreatedBy) "
            "VALUES (:c, :n, :d, :k, 1, :uid)"
        ), {"c": category_id or CUSTOM_CATEGORY_ID, "n": name, "d": minutes, "k": kcal, "uid": user_id})
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return None, "Không thể tạo bài tập (kiểm tra user_id và category_id)."

    return {"id": result.lastrowid, "name": name, "duration_minutes": minutes,
            "calories_burned": kcal, "is_custom": True}, None


# ---------- Nhật ký ----------
def log_workout(user_id, workout_id, duration_minutes=None, logged_date=None):
    row = db.session.execute(text(
        "SELECT WorkoutName, DurationMinutes, CaloriesBurned FROM Workouts "
        "WHERE WorkoutId = :wid AND (IsCustom = 0 OR CreatedBy = :uid)"
    ), {"wid": workout_id, "uid": user_id}).first()
    if not row:
        return None, "Không tìm thấy bài tập."

    minutes = row.DurationMinutes if duration_minutes in (None, "") else _valid_minutes(duration_minutes)
    if minutes is None:
        return None, f"Thời lượng phải từ 1 đến {MAX_MINUTES} phút."

    try:
        day = parse_date(logged_date, default=date.today())
    except ValueError:
        return None, "Ngày không hợp lệ (định dạng YYYY-MM-DD)."
    if day > date.today():
        return None, "Không thể ghi nhật ký cho ngày trong tương lai."

    kcal = scale_calories(row.CaloriesBurned, row.DurationMinutes, minutes)
    try:
        result = db.session.execute(text(
            "INSERT INTO WorkoutLogs (UserId, WorkoutId, LoggedDate, DurationMinutes, CaloriesBurned) "
            "VALUES (:uid, :wid, :d, :m, :k)"
        ), {"uid": user_id, "wid": workout_id, "d": day.isoformat(), "m": minutes, "k": kcal})
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return None, "Không thể ghi nhật ký (kiểm tra user_id)."

    return {"log_id": result.lastrowid, "workout_id": workout_id, "workout_name": row.WorkoutName,
            "date": day.isoformat(), "duration_minutes": minutes, "calories_burned": kcal}, None


def get_logs(user_id, start=None, end=None, limit=200):
    end = end or date.today()
    start = start or (end - timedelta(days=29))
    rows = db.session.execute(text(
        "SELECT l.LogId, l.WorkoutId, w.WorkoutName, l.LoggedDate, l.DurationMinutes, l.CaloriesBurned "
        "FROM WorkoutLogs l JOIN Workouts w ON w.WorkoutId = l.WorkoutId "
        "WHERE l.UserId = :uid AND l.LoggedDate BETWEEN :s AND :e "
        "ORDER BY l.LoggedDate DESC, l.LogId DESC LIMIT :lim"
    ), {"uid": user_id, "s": start.isoformat(), "e": end.isoformat(), "lim": limit}).fetchall()
    return [{"log_id": r.LogId, "workout_id": r.WorkoutId, "workout_name": r.WorkoutName,
             "date": parse_date(r.LoggedDate).isoformat(), "duration_minutes": r.DurationMinutes,
             "calories_burned": float(r.CaloriesBurned)} for r in rows]


def delete_log(user_id, log_id):
    result = db.session.execute(
        text("DELETE FROM WorkoutLogs WHERE LogId = :lid AND UserId = :uid"),
        {"lid": log_id, "uid": user_id})
    db.session.commit()
    return result.rowcount > 0


# ---------- Mục tiêu tuần ----------
def get_goal(user_id):
    row = db.session.execute(
        text("SELECT WeeklySessionsTarget, WeeklyCaloriesTarget FROM WorkoutGoals WHERE UserId = :uid"),
        {"uid": user_id}).first()
    if not row:
        return dict(DEFAULT_GOAL)
    return {"weekly_sessions_target": int(row[0]), "weekly_calories_target": float(row[1])}


def save_goal(user_id, sessions_target, calories_target):
    try:
        sessions = int(sessions_target)
        kcal = float(calories_target)
    except (TypeError, ValueError):
        return None, "Mục tiêu không hợp lệ."
    if not 1 <= sessions <= 21:
        return None, "Số buổi mỗi tuần phải từ 1 đến 21."
    if not 0 < kcal <= 50000:
        return None, "Calo mục tiêu mỗi tuần phải lớn hơn 0."

    params = {"uid": user_id, "s": sessions, "k": kcal}
    try:
        exists = db.session.execute(
            text("SELECT 1 FROM WorkoutGoals WHERE UserId = :uid"), {"uid": user_id}).first()
        if exists:
            db.session.execute(text(
                "UPDATE WorkoutGoals SET WeeklySessionsTarget = :s, WeeklyCaloriesTarget = :k "
                "WHERE UserId = :uid"), params)
        else:
            db.session.execute(text(
                "INSERT INTO WorkoutGoals (UserId, WeeklySessionsTarget, WeeklyCaloriesTarget) "
                "VALUES (:uid, :s, :k)"), params)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return None, "Không thể lưu mục tiêu (kiểm tra user_id)."
    return {"weekly_sessions_target": sessions, "weekly_calories_target": kcal}, None
