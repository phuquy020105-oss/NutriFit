import hashlib
import hmac
import os
from datetime import datetime
from threading import Thread
from urllib.parse import quote
from flask import current_app
from flask_mail import Message
from app.extensions import mail


class PaymentService:
    # Cấu hình tài khoản ngân hàng nhận tiền chuyển khoản VietQR
    # Bạn có thể thay đổi số tài khoản và ngân hàng thực tế của bạn tại đây:
    # 970422: MB Bank | 970436: Vietcombank | 970407: Techcombank | 970415: Vietinbank
    # Must be configured with the real receiving account in local .env.
    BANK_BIN = os.getenv("NUTRIFIT_BANK_BIN", "").strip()
    BANK_ACCOUNT_NO = os.getenv("NUTRIFIT_BANK_ACCOUNT_NO", "").strip()
    BANK_ACCOUNT_NAME = os.getenv("NUTRIFIT_BANK_ACCOUNT_NAME", "").strip()

    @classmethod
    def bank_is_configured(cls) -> bool:
        return bool(cls.BANK_BIN and cls.BANK_ACCOUNT_NO and cls.BANK_ACCOUNT_NAME)

    @staticmethod
    def generate_transaction_code(user_id: int) -> str:
        """Sinh mã giao dịch duy nhất: TXN_<thời_gian>_<user_id>"""
        time_str = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        return f"TXN_{time_str}_{user_id}"

    @classmethod
    def generate_vietqr_url(cls, amount: int, transaction_code: str) -> str:
        """
        Tạo URL mã VietQR tự động điền sẵn số tài khoản, số tiền và nội dung chuyển khoản.
        Frontend chỉ cần đưa link này vào thẻ <img src="..." /> là hiện mã QR chuẩn.
        """
        if not cls.bank_is_configured():
            raise RuntimeError("Chưa cấu hình tài khoản nhận thanh toán thật. Hãy thiết lập NUTRIFIT_BANK_BIN, NUTRIFIT_BANK_ACCOUNT_NO và NUTRIFIT_BANK_ACCOUNT_NAME trong .env.")
        encoded_memo = quote(transaction_code)
        account_name_encoded = quote(cls.BANK_ACCOUNT_NAME)
        return (
            f"https://img.vietqr.io/image/{cls.BANK_BIN}-{cls.BANK_ACCOUNT_NO}-compact2.png"
            f"?amount={amount}&addInfo={encoded_memo}&accountName={account_name_encoded}"
        )

    @staticmethod
    def _send_async_email(app, msg):
        """Hàm chạy ngầm (Background Thread) gửi email để API phản hồi ngay lập tức"""
        with app.app_context():
            try:
                mail.send(msg)
            except Exception as e:
                print(f"[Email Error] Lỗi gửi email: {e}")

    @classmethod
    def send_payment_pending_email(cls, recipient_email: str, user_name: str, plan_name: str, amount: int, transaction_code: str, qr_url: str):
        """Gửi email hướng dẫn thanh toán kèm ảnh mã QR cho người dùng"""
        app = current_app._get_current_object()
        subject = f"[NutriFit] Yêu cầu thanh toán đơn hàng {transaction_code}"
        formatted_amount = f"{amount:,.0f} VNĐ"

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; color: #1e293b;">
            <h2 style="color: #2563eb; text-align: center;">Yêu Cầu Nâng Cấp Gói Dịch Vụ</h2>
            <p>Xin chào <strong>{user_name}</strong>,</p>
            <p>Bạn vừa khởi tạo yêu cầu nâng cấp gói <strong>{plan_name}</strong> trên NutriFit.</p>
            
            <div style="text-align: center; margin: 25px 0;">
                <p style="font-weight: bold; margin-bottom: 8px;">Quét mã VietQR bằng ứng dụng Ngân hàng:</p>
                <img src="{qr_url}" alt="Mã VietQR Thanh Toán" style="max-width: 280px; border: 1px solid #cbd5e1; border-radius: 8px; padding: 6px;" />
            </div>

            <table style="width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 14px;">
                <tr style="background-color: #f8fafc;">
                    <td style="padding: 10px; border: 1px solid #e2e8f0;"><strong>Số tiền cần thanh toán</strong></td>
                    <td style="padding: 10px; border: 1px solid #e2e8f0; color: #dc2626; font-weight: bold;">{formatted_amount}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #e2e8f0;"><strong>Nội dung chuyển khoản (bắt buộc)</strong></td>
                    <td style="padding: 10px; border: 1px solid #e2e8f0; font-weight: bold; color: #2563eb;">{transaction_code}</td>
                </tr>
            </table>

            <p style="font-size: 13px; color: #64748b;">Hệ thống sẽ tự động kích hoạt tài khoản Premium ngay sau khi nhận được tiền.</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
            <p style="font-size: 12px; color: #64748b; text-align: center;">NutriFit Team • Hỗ trợ: phuquy020105@gmail.com</p>
        </div>
        """

        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            html=html_body,
            sender=app.config.get('MAIL_DEFAULT_SENDER')
        )
        Thread(target=cls._send_async_email, args=(app, msg)).start()

    @classmethod
    def send_payment_success_email(cls, recipient_email: str, user_name: str, plan_name: str, amount: int, expires_at: str, transaction_code: str):
        """Gửi email hóa đơn xác nhận thanh toán và kích hoạt Premium thành công"""
        app = current_app._get_current_object()
        subject = f"[NutriFit] Nâng cấp thành công gói {plan_name}"
        formatted_amount = f"{amount:,.0f} VNĐ"

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; color: #1e293b;">
            <h2 style="color: #16a34a; text-align: center;">🎉 Thanh Toán Thành Công!</h2>
            <p>Xin chào <strong>{user_name}</strong>,</p>
            <p>Tài khoản của bạn tại <strong>NutriFit</strong> đã được kích hoạt gói <strong>PREMIUM</strong> thành công.</p>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
                <tr style="background-color: #f8fafc;">
                    <td style="padding: 10px; border: 1px solid #e2e8f0;"><strong>Mã giao dịch</strong></td>
                    <td style="padding: 10px; border: 1px solid #e2e8f0;">{transaction_code}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #e2e8f0;"><strong>Gói dịch vụ</strong></td>
                    <td style="padding: 10px; border: 1px solid #e2e8f0;">{plan_name}</td>
                </tr>
                <tr style="background-color: #f8fafc;">
                    <td style="padding: 10px; border: 1px solid #e2e8f0;"><strong>Số tiền đã trả</strong></td>
                    <td style="padding: 10px; border: 1px solid #e2e8f0; color: #16a34a; font-weight: bold;">{formatted_amount}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #e2e8f0;"><strong>Hạn dùng dịch vụ đến</strong></td>
                    <td style="padding: 10px; border: 1px solid #e2e8f0;">{expires_at}</td>
                </tr>
            </table>

            <p>Bây giờ bạn có thể trải nghiệm toàn bộ tính năng cao cấp không giới hạn!</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
            <p style="font-size: 12px; color: #64748b; text-align: center;">NutriFit Team • Hỗ trợ: phuquy020105@gmail.com</p>
        </div>
        """

        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            html=html_body,
            sender=app.config.get('MAIL_DEFAULT_SENDER')
        )
        Thread(target=cls._send_async_email, args=(app, msg)).start()