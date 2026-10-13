from flask import Blueprint, jsonify, request
from sqlalchemy import func, and_, or_, case
from app.extensions import db
from app.models.user import User, PaymentTransaction, SubscriptionPlan
from app.security import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """Xem toàn bộ danh sách người dùng trong hệ thống"""
    users = User.query.order_by(User.UserId.asc()).all()
    user_list = [u.to_dict() for u in users]
    
    return jsonify({
        "success": True,
        "total": len(user_list),
        "data": user_list
    }), 200


@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard_stats():
    """Xem thống kê tổng quan và phân tích doanh thu theo ngày hoặc tháng"""
    # 1. Nhận query parameter: 'day' (mặc định) hoặc 'month'
    period = request.args.get('period', 'day').lower()

    if period == 'month':
        # Nhóm theo Tháng: YYYY-MM
        date_format_str = '%Y-%m'
    else:
        # Nhóm theo Ngày: YYYY-MM-DD
        date_format_str = '%Y-%m-%d'

    # Doanh thu THỰC chỉ từ phương thức thanh toán thực và trạng thái SUCCESS.
    # QR thử nghiệm được theo dõi như giá trị giao dịch đã xác nhận, không phải tiền thực thu.
    simulated_methods = ('DEMO', 'DEMO_QR')
    real_success = and_(PaymentTransaction.Status == 'SUCCESS',
                        ~PaymentTransaction.PaymentMethod.in_(simulated_methods))
    test_confirmed = and_(PaymentTransaction.PaymentMethod.in_(simulated_methods),
                          PaymentTransaction.Status.in_(('SUCCESS', 'DEMO_SUCCESS', 'DEMO_MAIL_ERROR')))
    confirmed = or_(real_success, test_confirmed)

    # MySQL khi chạy thật; SQLite được hỗ trợ cho bài kiểm thử tự động.
    date_group = (func.strftime(date_format_str, PaymentTransaction.CreatedAt)
                  if db.engine.dialect.name == 'sqlite'
                  else func.date_format(PaymentTransaction.CreatedAt, date_format_str))
    revenue_chart_query = db.session.query(
        date_group.label('timeline'),
        func.coalesce(func.sum(PaymentTransaction.AmountVnd), 0).label('revenue'),
        func.count(PaymentTransaction.TransactionId).label('transaction_count'),
        func.coalesce(func.sum(case((real_success, PaymentTransaction.AmountVnd), else_=0)), 0).label('real_revenue'),
        func.coalesce(func.sum(case((test_confirmed, PaymentTransaction.AmountVnd), else_=0)), 0).label('simulated_value'),
    ).filter(confirmed).group_by(date_group).order_by(date_group.asc()).all()

    revenue_chart = [
        {"timeline": row.timeline, "revenue": int(row.revenue or 0),
         "transactions": row.transaction_count,
         "real_revenue": int(row.real_revenue or 0),
         "simulated_value": int(row.simulated_value or 0)}
        for row in revenue_chart_query
    ]

    # 3. Thống kê cơ cấu người dùng
    total_users = User.query.count()
    premium_users = User.query.filter_by(SubscriptionStatus='PREMIUM').count()
    free_users = total_users - premium_users

    # 4. Tổng giá trị giao dịch được phân tách để không nhầm tiền giả lập với tiền thực.
    real_revenue = int(db.session.query(
        func.coalesce(func.sum(PaymentTransaction.AmountVnd), 0)
    ).filter(real_success).scalar() or 0)
    simulated_value = int(db.session.query(
        func.coalesce(func.sum(PaymentTransaction.AmountVnd), 0)
    ).filter(test_confirmed).scalar() or 0)
    confirmed_transactions = PaymentTransaction.query.filter(confirmed).count()
    total_transactions = PaymentTransaction.query.count()

    # 5. Lấy 5 giao dịch gần đây nhất
    recent_transactions = PaymentTransaction.query.order_by(
        PaymentTransaction.CreatedAt.desc()
    ).limit(5).all()

    return jsonify({
        "success": True,
        "data": {
            "period": period,
            "users": {
                "total": total_users,
                "free": free_users,
                "premium": premium_users
            },
            "financial": {
                "total_revenue_vnd": real_revenue,
                "real_revenue_vnd": real_revenue,
                "simulated_revenue_vnd": simulated_value,
                "total_confirmed_value_vnd": real_revenue + simulated_value,
                "confirmed_transactions": confirmed_transactions,
                "total_transactions": total_transactions
            },
            "revenue_chart": revenue_chart,
            "recent_transactions": [t.to_dict() for t in recent_transactions]
        }
    }), 200


@admin_bp.route('/transactions', methods=['GET'])
@admin_required
def get_all_transactions():
    """Xem danh sách toàn bộ lịch sử thanh toán / giao dịch"""
    transactions = PaymentTransaction.query.order_by(PaymentTransaction.CreatedAt.desc()).all()
    transaction_list = [t.to_dict() for t in transactions]

    return jsonify({
        "success": True,
        "total": len(transaction_list),
        "data": transaction_list
    }), 200