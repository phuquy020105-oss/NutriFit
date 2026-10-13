"""API Workout, Progress và Street Food (TV4).

Đăng ký trong create_app() (nhờ TV1 hoặc tự thêm ở nhánh của mình):
    from app.routes.workouts import workout_bp, progress_bp, street_food_bp
    app.register_blueprint(workout_bp, url_prefix='/api/workouts')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')
    app.register_blueprint(street_food_bp, url_prefix='/api/street-food')
"""
from flask import Blueprint, request, jsonify, current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.services import workout_service as ws
from app.services import progress_service as ps
from app.data import street_foods as sfs
from app.module_auth import login_required, check_user_identity
from app.services.module_errors import api_errors
from app.services.premium_access import PremiumAccess

workout_bp = Blueprint('workout_bp', __name__)
progress_bp = Blueprint('progress_bp', __name__)
street_food_bp = Blueprint('street_food_bp', __name__)


def _ok(data=None, message=None, status=200):
    body = {"success": True}
    if message:
        body["message"] = message
    if data is not None:
        body["data"] = data
    return jsonify(body), status


def _fail(message, status=400):
    return jsonify({"success": False, "message": message}), status


def _date_arg(name):
    """Đọc tham số ngày YYYY-MM-DD từ query string. Trả (giá_trị, lỗi)."""
    raw = request.args.get(name)
    try:
        return ws.parse_date(raw), None
    except ValueError:
        return None, f"Tham số {name} phải có dạng YYYY-MM-DD."


# Token xác nhận AI ký ở server; khách không thể tự chọn MET / kcal.
# Có hiệu lực trong 10 phút và ràng buộc vào user, tên bài, thời lượng.
_ESTIMATE_SALT = "nutrifit-workout-ai-estimate-v1"


def _estimate_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=_ESTIMATE_SALT)


def _verified_estimate(data):
    token = data.get("estimate_token")
    if not isinstance(token, str) or len(token) > 4000:
        return None, "Bạn cần xác minh bài tập với AI trước khi lưu."
    try:
        value = _estimate_serializer().loads(token, max_age=600)
    except (SignatureExpired, BadSignature, ValueError, TypeError):
        return None, "Kết quả AI đã hết hạn hoặc không hợp lệ. Vui lòng kiểm tra lại bài tập."
    if (not isinstance(value, dict) or
        str(value.get("user_id")) != str(data.get("user_id")) or
        value.get("name") != str(data.get("name") or "").strip() or
        value.get("minutes") != ws._valid_minutes(data.get("duration_minutes"))):
        return None, "Thông tin bài tập đã thay đổi. Vui lòng kiểm tra lại với AI."
    try:
        met = float(value["met"])
        if not 1 <= met <= 20:
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        return None, "Chỉ số AI không hợp lệ."
    return met, None


# ---------------- /api/workouts ----------------
@workout_bp.route('/catalog', methods=['GET'])
def catalog():
    user_id = request.args.get('user_id', type=int)
    return _ok(ws.list_catalog(user_id))


@workout_bp.route('/custom', methods=['POST'])
@api_errors
@login_required
def create_custom():
    data = request.get_json(silent=True) or {}
    user_id = check_user_identity(data)
    PremiumAccess.require(user_id)
    met, error = _verified_estimate(data)
    if error:
        return _fail(error)
    # BỎ QUA calories_burned / met do client gửi: luôn tính server-side.
    workout, error = ws.create_custom_workout(
        data['user_id'], data.get('name'), data.get('duration_minutes'),
        category_id=data.get('category_id'), met=met)
    if error:
        return _fail(error)
    return _ok(workout, "Đã tạo bài tập được AI xác minh!", 201)


@workout_bp.route('/estimate', methods=['POST'])
@api_errors
@login_required
def estimate():
    """AI kiểm tra tên bài và ước tính calo; kết quả ký để chống giả mạo khi lưu."""
    data = request.get_json(silent=True) or {}
    user_id = check_user_identity(data)
    PremiumAccess.require(user_id)
    result, error = ws.estimate_workout(data['user_id'], data.get('name'), data.get('duration_minutes'))
    if error:
        unavailable = "Không kết nối được dịch vụ AI" in error
        return _fail(error, 503 if unavailable else 400)
    result["estimate_token"] = _estimate_serializer().dumps({
        "user_id": str(data['user_id']), "name": result["name"],
        "minutes": result["duration_minutes"], "met": result["met"]})
    return _ok(result)


@workout_bp.route('/categories', methods=['GET'])
def categories():
    return _ok(ws.list_categories())


@workout_bp.route('/custom/<int:workout_id>', methods=['PUT'])
@api_errors
@login_required
def update_custom(workout_id):
    data = request.get_json(silent=True) or {}
    user_id = check_user_identity(data)
    PremiumAccess.require(user_id)
    existing = ws._get_own_custom(data['user_id'], workout_id)
    if not existing:
        return _fail("Không tìm thấy bài tập tùy chỉnh của bạn.", 404)
    # Tên/thời lượng có thể thay đổi calo: luôn yêu cầu tính AI lại.
    name = str(data.get('name', existing.WorkoutName)).strip()
    minutes = data.get('duration_minutes', existing.DurationMinutes)
    validation_input = {**data, 'name': name, 'duration_minutes': minutes}
    met, error = _verified_estimate(validation_input)
    if error:
        return _fail(error)
    workout, error = ws.update_custom_workout(
        data['user_id'], workout_id, name=name,
        duration_minutes=minutes, category_id=data.get('category_id'), met=met)
    if error:
        return _fail(error, 404 if "Không tìm thấy" in error else 400)
    return _ok(workout, "Đã cập nhật bài tập!")


@workout_bp.route('/custom/<int:workout_id>', methods=['DELETE'])
def delete_custom(workout_id):
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return _fail("Thiếu user_id")
    done, error = ws.delete_custom_workout(user_id, workout_id)
    if error:
        return _fail(error, 404 if "Không tìm thấy" in error else 400)
    return _ok(message="Đã xóa bài tập.")


@workout_bp.route('/log', methods=['POST'])
def add_log():
    data = request.get_json() or {}
    if not data.get('user_id') or not data.get('workout_id'):
        return _fail("Thiếu user_id hoặc workout_id")
    log, error = ws.log_workout(data['user_id'], data['workout_id'],
                                data.get('duration_minutes'), data.get('date'))
    if error:
        return _fail(error)
    return _ok(log, "Đã ghi nhật ký luyện tập!", 201)


@workout_bp.route('/logs', methods=['GET'])
def list_logs():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return _fail("Thiếu user_id")
    start, err1 = _date_arg('from')
    end, err2 = _date_arg('to')
    if err1 or err2:
        return _fail(err1 or err2)
    return _ok(ws.get_logs(user_id, start, end))


@workout_bp.route('/log/<int:log_id>', methods=['DELETE'])
def remove_log(log_id):
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return _fail("Thiếu user_id")
    if not ws.delete_log(user_id, log_id):
        return _fail("Không tìm thấy bản ghi.", 404)
    return _ok(message="Đã xóa bản ghi.")


@workout_bp.route('/goal/<int:user_id>', methods=['GET'])
def get_goal(user_id):
    return _ok(ws.get_goal(user_id))


@workout_bp.route('/goal', methods=['POST'])
def save_goal():
    data = request.get_json() or {}
    if not data.get('user_id'):
        return _fail("Thiếu user_id")
    goal, error = ws.save_goal(data['user_id'], data.get('weekly_sessions_target'),
                               data.get('weekly_calories_target'))
    if error:
        return _fail(error)
    return _ok(goal, "Đã lưu mục tiêu tuần!")


# ---------------- /api/progress ----------------
@progress_bp.route('/weekly/<int:user_id>', methods=['GET'])
def weekly(user_id):
    end, error = _date_arg('end')
    if error:
        return _fail(error)
    return _ok(ps.weekly_stats(user_id, end))


# ---------------- /api/street-food ----------------
@street_food_bp.route('', methods=['GET'])
def list_street_food():
    meal_type = request.args.get('meal_type')
    if meal_type and meal_type not in sfs.VALID_MEAL_TYPES:
        return _fail("meal_type phải là all, breakfast, lunch hoặc dinner.")
    dishes = sfs.list_dishes(meal_type, request.args.get('max_price', type=int),
                             request.args.get('max_kcal', type=float), request.args.get('q'))
    return _ok({"count": len(dishes), "items": dishes})


@street_food_bp.route('/recommend', methods=['POST'])
def recommend_street_food():
    data = request.get_json() or {}
    result, error = sfs.recommend(data.get('budget'), data.get('max_kcal'),
                                  data.get('meal_type', 'all'), data.get('limit', 5))
    if error:
        return _fail(error)
    return _ok(result)
