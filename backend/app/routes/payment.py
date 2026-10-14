from datetime import datetime, timedelta
import base64
from io import BytesIO
from pathlib import Path
from html import escape as html_escape
from urllib.parse import urlparse
import secrets

import qrcode
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app, render_template_string, make_response
from flask_mail import Message
from app.extensions import mail
import hashlib
import hmac
import os
from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models.user import User, PaymentTransaction, SubscriptionPlan
from app.services.payment_service import PaymentService
from app.module_auth import login_required, check_user_identity
from app.services.module_errors import api_errors

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

    if not PaymentService.bank_is_configured():
        return jsonify({
            "success": False,
            "message": "Chưa cấu hình tài khoản nhận thanh toán thật. Hiện chưa thể tạo đơn chuyển khoản."
        }), 503

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
    webhook_secret = os.getenv("PAYMENT_WEBHOOK_SECRET", "").strip()
    signature = request.headers.get("X-Payment-Signature", "").strip()
    if not webhook_secret:
        return jsonify({"success": False, "message": "Webhook chưa được cấu hình bí mật xác thực; không thể kích hoạt thanh toán tự động."}), 503
    expected = hmac.new(webhook_secret.encode("utf-8"), request.get_data(cache=True), hashlib.sha256).hexdigest()
    if not signature or not hmac.compare_digest(signature, expected):
        return jsonify({"success": False, "message": "Chữ ký webhook không hợp lệ."}), 401

    data = request.get_json(silent=True) or {}
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

# ---------- Demo-only QR payment: never creates a VietQR/bank transfer ----------
_DEMO_STATUS_PENDING = "DEMO_PENDING"
_DEMO_STATUS_SUCCESS = "DEMO_SUCCESS"
_DEMO_STATUS_EMAIL_FAILED = "DEMO_MAIL_ERROR"
_DEMO_TOKEN_TTL = 15 * 60
_DEMO_ACCOUNT = "NF-000123456"  # Not a real bank account
_DEMO_RECIPIENT = "NUTRIFIT"


def _demo_is_on():
    # Explicit, two-factor opt-in; production cannot activate the simulation.
    return (os.getenv("NUTRIFIT_ENV", "production").lower() == "development"
            and os.getenv("NUTRIFIT_PAYMENT_DEMO_MODE", "false").lower() in ("true", "1", "yes"))


def _demo_access():
    if not _demo_is_on():
        return jsonify(success=False, message="Chức năng thanh toán hiện chưa khả dụng."), 403
    return None


def _demo_signer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="nutrifit-demo-qr-confirm-v1")


def _demo_token(txn):
    return _demo_signer().dumps({"id": txn.TransactionId, "code": txn.TransactionCode})


def _demo_validate(token):
    try:
        payload = _demo_signer().loads(token, max_age=_DEMO_TOKEN_TTL)
    except (BadSignature, SignatureExpired):
        return None
    txn = db.session.get(PaymentTransaction, payload.get("id"))
    if not txn or txn.TransactionCode != payload.get("code") or txn.PaymentMethod != "DEMO_QR":
        return None
    return txn


def _demo_url(token):
    # For phone scanning provide a LAN-accessible address in .env.
    configured = os.getenv("NUTRIFIT_DEMO_QR_BASE_URL", "").strip().rstrip("/")
    if configured:
        url = urlparse(configured)
        if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.path not in ("", "/"):
            raise ValueError("NUTRIFIT_DEMO_QR_BASE_URL phải là http(s)://host:port, không kèm đường dẫn")
        base = configured
    else:
        base = request.host_url.rstrip("/")
    return base + "/api/payment/confirm/" + token


def _demo_qr_data_url(url):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=7, border=3)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#153f2b", back_color="#ffffff")
    output = BytesIO()
    img.save(output, format="PNG")
    return "data:image/png;base64," + base64.b64encode(output.getvalue()).decode("ascii")


def _demo_email(txn):
    """Notify account owner of activated benefits, not of a real bank transfer."""
    if current_app.config.get('MAIL_SUPPRESS_SEND'):
        raise RuntimeError('MAIL_SUPPRESS_SEND is enabled')
    user = db.session.get(User, txn.UserId)
    plan = db.session.get(SubscriptionPlan, txn.PlanId)
    if not user or not user.Email:
        raise ValueError("Không tìm thấy email tài khoản")
    plan_name = plan.PlanName if plan else "Premium"
    amount = f"{int(txn.AmountVnd):,}".replace(",", ".")
    name = html_escape(user.FullName or "Bạn")
    safe_plan = html_escape(plan_name)
    display_code = txn.TransactionCode.replace('DEMO_', 'NF_', 1) if txn.TransactionCode.startswith('DEMO_') else txn.TransactionCode
    safe_code = html_escape(display_code)
    expires_at = (user.PremiumExpiresAt.strftime('%d/%m/%Y')
                  if user.PremiumExpiresAt else "Xem trong hồ sơ")
    mail.send(Message(
        subject="[NutriFit] Đăng ký Premium thành công",
        recipients=[user.Email],
        sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
        body=(f"Xin chào {user.FullName or 'Bạn'},\n"
              f"Gói {plan_name} của bạn đã được kích hoạt thành công.\n"
              f"Giá gói: {amount} VND. Mã đăng ký: {display_code}.\n"
              f"Thời hạn Premium đến: {expires_at}.\n"
              "Bạn có thể sử dụng các tính năng Premium trong NutriFit ngay bây giờ."),
        html=(f'<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#244334">'
              f'<h2 style="color:#277a50">NutriFit Premium đã được kích hoạt!</h2>'
              f'<p>Xin chào <b>{name}</b>,</p>'
              f'<p>Bạn đã hoàn tất đăng ký <b>{safe_plan}</b>.</p>'
              f'<p>Giá gói: <b>{amount} đ</b><br>Mã đăng ký: <b>{safe_code}</b><br>'
              f'Thời hạn: <b>{html_escape(expires_at)}</b></p>'
              f'<p>Chúc bạn có trải nghiệm tuyệt vời cùng NutriFit!</p></div>'),
    ))


# NutriFit-branded checkout portal. Render from a bundled HTML template instead of
# impersonating a third-party payment gateway. All transactions remain internal.
_PAYMENT_GATEWAY_TEMPLATE = (Path(__file__).resolve().parents[1] / 'templates' / 'payment_gateway.html').read_text(encoding='utf-8')


def _demo_page(txn, title, message, can_confirm=False, http_status=200):
    plan = db.session.get(SubscriptionPlan, txn.PlanId) if txn else None
    nonce = secrets.token_urlsafe(18)
    qr_src = _demo_qr_data_url(_demo_url(_demo_token(txn))) if can_confirm and txn else ''
    page = render_template_string(
        _PAYMENT_GATEWAY_TEMPLATE,
        title=title,
        message=message,
        account=_DEMO_ACCOUNT,
        plan=plan.PlanName if plan else '—',
        amount=f"{int(txn.AmountVnd):,} đ".replace(',', '.') if txn else '—',
        code=(txn.TransactionCode.replace('DEMO_', 'NF_', 1)
              if txn and txn.TransactionCode.startswith('DEMO_')
              else txn.TransactionCode if txn else '—'),
        can_confirm=can_confirm,
        outcome=('pending' if can_confirm else 'success' if (txn and txn.Status in (_DEMO_STATUS_SUCCESS, _DEMO_STATUS_EMAIL_FAILED)) else 'info'),
        qr_src=qr_src,
        back_url='http://127.0.0.1:5500/frontend/index.html#premium',
        script_nonce=nonce,
    )
    resp = make_response(page, http_status)
    resp.headers['Cache-Control'] = 'no-store, private'
    resp.headers['X-Robots-Tag'] = 'noindex, nofollow'
    resp.headers['Referrer-Policy'] = 'no-referrer'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['Content-Security-Policy'] = (
        "default-src 'none'; img-src data:; style-src 'unsafe-inline'; "
        f"script-src 'nonce-{nonce}'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
    )
    return resp


@payment_bp.route('/demo-checkout', methods=['POST'])
@api_errors
@login_required
def demo_checkout():
    disabled = _demo_access()
    if disabled:
        return disabled
    user_id = check_user_identity(request.get_json(silent=True) or {})
    browser_user_id = request.headers.get('X-User-Id', '').strip()
    if browser_user_id:
        if not browser_user_id.isdecimal() or int(browser_user_id) != user_id:
            return jsonify(success=False, message='Phiên đăng nhập không khớp tài khoản. Vui lòng đăng xuất rồi đăng nhập lại.'), 403
    user = db.session.get(User, user_id)
    if not user:
        return jsonify(success=False, message="Không tìm thấy tài khoản."), 404
    data = request.get_json(silent=True) or {}
    try:
        plan_id = int(data.get("plan_id"))
    except (ValueError, TypeError):
        return jsonify(success=False, message="Gói không hợp lệ."), 400
    plan = db.session.get(SubscriptionPlan, plan_id)
    if not plan or not plan.IsActive:
        return jsonify(success=False, message="Gói Premium không tồn tại hoặc ngừng bán."), 404

    # Basic local rate limit; this is not a substitute for real authentication.
    recent = PaymentTransaction.query.filter(
        PaymentTransaction.UserId == user.UserId,
        PaymentTransaction.PaymentMethod == 'DEMO_QR',
        PaymentTransaction.CreatedAt >= datetime.utcnow() - timedelta(minutes=15)
    ).count()
    if recent >= 3:
        return jsonify(success=False, message="Bạn đã tạo tối đa 3 yêu cầu thanh toán trong 15 phút. Hãy thử lại sau."), 429

    txn = PaymentTransaction(UserId=user.UserId, PlanId=plan.PlanId, AmountVnd=plan.PriceVnd,
                             PaymentMethod='DEMO_QR', Status=_DEMO_STATUS_PENDING,
                             TransactionCode='NF_' + secrets.token_hex(14).upper(),
                             CreatedAt=datetime.utcnow())
    try:
        db.session.add(txn)
        db.session.commit()
        url = _demo_url(_demo_token(txn))
        qr_image = _demo_qr_data_url(url)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Lỗi tạo mã QR thanh toán")
        return jsonify(success=False, message="Không thể tạo mã QR. Kiểm tra địa chỉ LAN và thư viện qrcode."), 500
    return jsonify(success=True, message="Đã tạo yêu cầu thanh toán. Vui lòng quét QR để xác nhận.", data={
        "transaction_id": txn.TransactionId, "transaction_code": txn.TransactionCode,
        "plan_name": plan.PlanName, "amount_vnd": int(plan.PriceVnd),
        "recipient_name": _DEMO_RECIPIENT, "account_number": _DEMO_ACCOUNT,
        "confirm_url": url, "qr_data_url": qr_image, "status": txn.Status,
        "is_demo": True
    }), 201


@payment_bp.route('/demo-status/<int:transaction_id>', methods=['GET'])
@api_errors
@login_required
def demo_status(transaction_id):
    disabled = _demo_access()
    if disabled:
        return disabled
    user_id = check_user_identity()
    browser_user_id = request.headers.get('X-User-Id', '').strip()
    if browser_user_id:
        if not browser_user_id.isdecimal() or int(browser_user_id) != user_id:
            return jsonify(success=False, message='Phiên đăng nhập không khớp tài khoản. Vui lòng đăng xuất rồi đăng nhập lại.'), 403
    txn = db.session.get(PaymentTransaction, transaction_id)
    if not txn or txn.UserId != user_id or txn.PaymentMethod != 'DEMO_QR':
        return jsonify(success=False, message="Không tìm thấy giao dịch."), 404
    # Authoritative entitlement from MySQL, not a cached browser flag.
    customer = db.session.get(User, user_id)
    premium_active = bool(customer and customer.SubscriptionStatus == 'PREMIUM'
                          and customer.PremiumExpiresAt
                          and customer.PremiumExpiresAt > datetime.utcnow())
    return jsonify(success=True, data={
        "status": txn.Status, "transaction_code": txn.TransactionCode,
        "user_id": user_id,
        "premium_active": premium_active,
        "subscription_status": customer.SubscriptionStatus if customer else 'FREE',
        "premium_expires_at": customer.PremiumExpiresAt.isoformat() if customer and customer.PremiumExpiresAt else None,
        "email_sent": txn.Status == _DEMO_STATUS_SUCCESS,
        "is_demo": True  # Internal accounting marker; never used as a UI label.
    }), 200


@payment_bp.route('/demo-confirm/<token>', methods=['GET', 'POST'])  # Legacy QR links
@payment_bp.route('/confirm/<token>', methods=['GET', 'POST'])
def demo_confirm(token):
    if not _demo_is_on():
        return "Hệ thống thanh toán tạm thời không khả dụng.", 403
    txn = _demo_validate(token)
    if not txn:
        return "Mã QR đã hết hạn hoặc không hợp lệ. Vui lòng tạo giao dịch mới.", 410
    if txn.Status == _DEMO_STATUS_SUCCESS:
        return _demo_page(txn, "Premium đã kích hoạt", "Gói Premium đã được kích hoạt cho tài khoản đăng ký.")
    if txn.Status == _DEMO_STATUS_EMAIL_FAILED:
        return _demo_page(txn, "Premium đã kích hoạt", "Gói đã được kích hoạt. Thông báo qua email đang gặp sự cố.")
    if txn.Status != _DEMO_STATUS_PENDING:
        return _demo_page(txn, "Đang xử lý", "Giao dịch đang được xử lý, vui lòng kiểm tra lại sau.")
    if request.method == 'GET':
        return _demo_page(txn, "Xác nhận thanh toán Premium", "Vui lòng kiểm tra thông tin gói trước khi xác nhận.", True)
    if request.form.get('agree') != 'yes':
        return _demo_page(txn, "Chưa xác nhận", "Vui lòng đánh dấu đồng ý trước khi tiếp tục.", True, 400)
    # Method choice changes presentation only. Real banking/card details are never collected.
    if request.form.get('payment_method', 'QR') not in {'QR', 'BANK', 'CARD', 'WALLET'}:
        return _demo_page(txn, 'Phương thức không hợp lệ',
                          'Vui lòng chọn lại phương thức thanh toán.', True, 400)

    # Claim the transaction once; a duplicate scan or click cannot grant twice.
    claimed = PaymentTransaction.query.filter_by(
        TransactionId=txn.TransactionId,
        PaymentMethod='DEMO_QR',
        Status=_DEMO_STATUS_PENDING,
    ).update({"Status": "DEMO_CONFIRMING"}, synchronize_session=False)
    db.session.commit()
    if claimed != 1:
        return _demo_page(txn, "Đang xử lý", "Giao dịch đã được xác nhận hoặc đang xử lý.")

    try:
        # Transaction and entitlement succeed together, before attempting SMTP.
        customer = db.session.get(User, txn.UserId)
        purchased = db.session.get(SubscriptionPlan, txn.PlanId)
        if not customer or not purchased or purchased.DurationDays <= 0:
            raise ValueError("Thiếu người dùng hoặc gói Premium hợp lệ")
        now = datetime.utcnow()
        current_expiry = customer.PremiumExpiresAt
        start = (current_expiry if customer.SubscriptionStatus == 'PREMIUM'
                 and current_expiry and current_expiry > now else now)
        customer.PremiumExpiresAt = start + timedelta(days=purchased.DurationDays)
        customer.SubscriptionStatus = 'PREMIUM'
        txn.Status = _DEMO_STATUS_SUCCESS
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Không thể kích hoạt quyền Premium")
        # The pending state must be recoverable for an owner to retry.
        txn = db.session.get(PaymentTransaction, txn.TransactionId)
        if txn and txn.Status == "DEMO_CONFIRMING":
            txn.Status = _DEMO_STATUS_PENDING
            db.session.commit()
        return _demo_page(txn, "Lỗi kích hoạt", "Chưa thể kích hoạt gói. Vui lòng thử lại.", True, 500)

    try:
        _demo_email(txn)
        return _demo_page(txn, "Premium đã kích hoạt!", "Đăng ký thành công. Email xác nhận đã được gửi đến tài khoản của bạn.")
    except Exception:
        current_app.logger.exception("Không gửi được email xác nhận đăng ký Premium")
        db.session.rollback()
        txn = db.session.get(PaymentTransaction, txn.TransactionId)
        txn.Status = _DEMO_STATUS_EMAIL_FAILED
        db.session.commit()
        return _demo_page(txn, "Premium đã kích hoạt!", "Gói Premium đã được kích hoạt. Email xác nhận chưa thể gửi.")
