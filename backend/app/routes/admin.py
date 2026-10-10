from flask import Blueprint, jsonify, request
from sqlalchemy import func
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

    date_group = func.date_format(PaymentTransaction.CreatedAt, date_format_str)

    # 2. Gom nhóm doanh thu theo mốc thời gian (chỉ tính giao dịch SUCCESS)
    revenue_chart_query = db.session.query(
        date_group.label('timeline'),
        func.sum(PaymentTransaction.AmountVnd).label('revenue'),
        func.count(PaymentTransaction.TransactionId).label('transaction_count')
    ).filter(
        PaymentTransaction.Status == 'SUCCESS'
    ).group_by(
        date_group
    ).order_by(
        date_group.asc()
    ).all()

    revenue_chart = [
        {
            "timeline": row.timeline,
            "revenue": int(row.revenue or 0),
            "transactions": row.transaction_count
        }
        for row in revenue_chart_query
    ]

    # 3. Thống kê cơ cấu người dùng
    total_users = User.query.count()
    premium_users = User.query.filter_by(SubscriptionStatus='PREMIUM').count()
    free_users = total_users - premium_users

    # 4. Thống kê doanh thu lũy kế
    revenue_result = db.session.query(
        func.coalesce(func.sum(PaymentTransaction.AmountVnd), 0)
    ).filter(PaymentTransaction.Status == 'SUCCESS').scalar()

    total_revenue = int(revenue_result or 0)
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
                "total_revenue_vnd": total_revenue,
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