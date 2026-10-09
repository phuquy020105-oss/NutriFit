"""API Workout, Progress và Street Food (TV4).

Đăng ký trong create_app() (nhờ TV1 hoặc tự thêm ở nhánh của mình):
    from app.routes.workouts import workout_bp, progress_bp, street_food_bp
    app.register_blueprint(workout_bp, url_prefix='/api/workouts')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')
    app.register_blueprint(street_food_bp, url_prefix='/api/street-food')
"""
from flask import Blueprint, request, jsonify

from app.services import workout_service as ws
from app.services import progress_service as ps
from app.data import street_foods as sfs

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


# ---------------- /api/workouts ----------------
@workout_bp.route('/catalog', methods=['GET'])
def catalog():
    user_id = request.args.get('user_id', type=int)
    return _ok(ws.list_catalog(user_id))


@workout_bp.route('/custom', methods=['POST'])
def create_custom():
    data = request.get_json() or {}
    if not data.get('user_id'):
        return _fail("Thiếu user_id")
    workout, error = ws.create_custom_workout(
        data['user_id'], data.get('name'), data.get('duration_minutes'),
        category_id=data.get('category_id'), calories_burned=data.get('calories_burned'),
        met=data.get('met'))
    if error:
        return _fail(error)
    return _ok(workout, "Đã tạo bài tập tùy chỉnh!", 201)


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
