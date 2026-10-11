from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models.user import User, PaymentTransaction, SubscriptionPlan
from app.services.payment_service import PaymentService

payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')


@payment_bp.route('/plans', methods=['GET'])
def get_subscription_plans():
    """Xem danh sách các gói dịch vụ"""
    try:
        plans = SubscriptionPlan.query.all()
        result = [
            {
                "plan_id": p.PlanId,
                "plan_name": p.PlanName,
                "duration_days": p.DurationDays,
                "price_vnd": int(p.PriceVnd),
                "description": p.Description
            }
            for p in plans
        ]
        return jsonify({"success": True, "total": len(result), "data": result}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@payment_bp.route('/checkout', methods=['POST'])
def create_checkout():
    """
    Tạo đơn thanh toán, sinh mã VietQR và gửi email hướng dẫn kèm QR code
    Header: X-User-Id
    Body JSON: {"plan_id": 1, "payment_method": "BANK_TRANSFER"}
    """
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({"success": False, "message": "Vui lòng đăng nhập!"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "Người dùng không tồn tại!"}), 404

    data = request.get_json() or {}
    plan_id = data.get('plan_id')
    payment_method = data.get('payment_method', 'BANK_TRANSFER').upper()

    if not plan_id:
        return jsonify({"success": False, "message": "Vui lòng chọn gói dịch vụ (plan_id)!"}), 400

    plan = SubscriptionPlan.query.get(plan_id)
    if not plan:
        return jsonify({"success": False, "message": "Gói dịch vụ không tồn tại!"}), 404

    transaction_code = PaymentService.generate_transaction_code(user.UserId)
    qr_code_url = PaymentService.generate_vietqr_url(int(plan.PriceVnd), transaction_code)

    try:
        # Tạo giao dịch ở trạng thái PENDING
        new_txn = PaymentTransaction(
            UserId=user.UserId,
            PlanId=plan.PlanId,
            AmountVnd=plan.PriceVnd,
            PaymentMethod=payment_method,
            Status='PENDING',
            TransactionCode=transaction_code,
            CreatedAt=datetime.utcnow()
        )
        db.session.add(new_txn)
        db.session.commit()

        # Gửi email kèm QR cho người dùng qua luồng ngầm
        PaymentService.send_payment_pending_email(
            recipient_email=user.Email,
            user_name=user.FullName or "Quý khách",
            plan_name=plan.PlanName,
            amount=int(plan.PriceVnd),
            transaction_code=transaction_code,
            qr_url=qr_code_url
        )

        return jsonify({
            "success": True,
            "message": "Tạo đơn thanh toán thành công! Mã QR đã được gửi về email của bạn.",
            "data": {
                "transaction_id": new_txn.TransactionId,
                "transaction_code": transaction_code,
                "amount_vnd": int(new_txn.AmountVnd),
                "plan_name": plan.PlanName,
                "qr_code_url": qr_code_url
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Lỗi tạo giao dịch: {str(e)}"}), 500


@payment_bp.route('/webhook', methods=['POST'])
def payment_webhook():
    """
    Webhook kích hoạt khi chuyển khoản thành công.
    Tự động nâng hạn PREMIUM và gửi email thông báo thành công.
    Body JSON: {"transaction_code": "TXN_...", "status": "SUCCESS"}
    """
    data = request.get_json() or {}
    transaction_code = data.get('transaction_code')
    target_status = data.get('status', 'SUCCESS').upper()

    if not transaction_code:
        return jsonify({"success": False, "message": "Thiếu mã transaction_code!"}), 400

    txn = PaymentTransaction.query.filter_by(TransactionCode=transaction_code).first()
    if not txn:
        return jsonify({"success": False, "message": "Không tìm thấy giao dịch!"}), 404

    if txn.Status == 'SUCCESS':
        return jsonify({"success": True, "message": "Giao dịch đã được kích hoạt trước đó!"}), 200

    if target_status != 'SUCCESS':
        txn.Status = target_status
        db.session.commit()
        return jsonify({"success": True, "message": f"Cập nhật trạng thái: {target_status}"}), 200

    try:
        txn.Status = 'SUCCESS'

        user = User.query.get(txn.UserId)
        plan = SubscriptionPlan.query.get(txn.PlanId)
        days_to_add = plan.DurationDays if plan else 30

        now = datetime.utcnow()
        # Cộng dồn hạn nếu đang là Premium
        if user.SubscriptionStatus == 'PREMIUM' and user.PremiumExpiresAt and user.PremiumExpiresAt > now:
            user.PremiumExpiresAt = user.PremiumExpiresAt + timedelta(days=days_to_add)
        else:
            user.PremiumExpiresAt = now + timedelta(days=days_to_add)

        user.SubscriptionStatus = 'PREMIUM'
        db.session.commit()

        # Gửi email xác nhận nâng cấp Premium thành công
        PaymentService.send_payment_success_email(
            recipient_email=user.Email,
            user_name=user.FullName or "Quý khách",
            plan_name=plan.PlanName if plan else "Gói Premium",
            amount=int(txn.AmountVnd),
            expires_at=user.PremiumExpiresAt.strftime('%d/%m/%Y %H:%M'),
            transaction_code=txn.TransactionCode
        )

        return jsonify({
            "success": True,
            "message": "Nâng cấp Premium và gửi email hóa đơn thành công!",
            "data": {
                "transaction_code": txn.TransactionCode,
                "user_id": user.UserId,
                "subscription_status": user.SubscriptionStatus,
                "premium_expires_at": user.PremiumExpiresAt.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Lỗi kích hoạt: {str(e)}"}), 500


@payment_bp.route('/my-history', methods=['GET'])
def get_my_history():
    """Xem lịch sử giao dịch của người dùng đang đăng nhập"""
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({"success": False, "message": "Vui lòng đăng nhập!"}), 401

    txns = PaymentTransaction.query.filter_by(UserId=user_id).order_by(
        PaymentTransaction.CreatedAt.desc()
    ).all()

    return jsonify({
        "success": True,
        "total": len(txns),
        "data": [t.to_dict() for t in txns]
    }), 200