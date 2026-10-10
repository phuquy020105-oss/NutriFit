import re
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, mail
from app.models.user import User

class AuthService:
    @staticmethod
    def validate_email_format(email):
        # Kiểm tra đúng định dạng email tiêu chuẩn
        regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(regex, email) is not None

    @staticmethod
    def _format_user(user):
        """Hàm chuẩn hóa dictionary của user để dùng chung thống nhất"""
        return {
            "id": user.UserId,
            "email": user.Email,
            "full_name": user.FullName,
            "role": user.Role
        }

    @staticmethod
    def register(email, password, full_name):
        email = (email or '').strip().lower()
        full_name = (full_name or '').strip()

        # 1. Kiểm tra đầu vào cơ bản
        if not email or not password or not full_name:
            return None, "Vui lòng nhập đầy đủ họ tên, email và mật khẩu!"

        if len(password) < 6:
            return None, "Mật khẩu phải có độ dài tối thiểu 6 ký tự!"

        # 2. Kiểm tra định dạng cú pháp email
        if not AuthService.validate_email_format(email):
            return None, "Định dạng email không hợp lệ!"

        # 3. Kiểm tra email đã có trong hệ thống chưa
        if User.query.filter_by(Email=email).first():
            return None, "Email này đã được sử dụng!"

        # 4. Gửi email xác nhận đến email thật
        try:
            msg = Message(
                subject="[NutriFit] Chào mừng bạn gia nhập NutriFit!",
                recipients=[email]
            )
            msg.body = f"""Xin chào {full_name},

Chúc mừng bạn đã tạo tài khoản thành công tại NutriFit!

Thông tin đăng ký của bạn:
- Họ tên: {full_name}
- Email: {email}
- Vai trò mặc định: Thành viên (MEMBER)

Hãy bắt đầu thiết lập thông số thể trạng (chiều cao, cân nặng, mục tiêu) để nhận lộ trình dinh dưỡng phù hợp nhất nhé!

Thân ái,
Đội ngũ hỗ trợ NutriFit.
"""
            mail.send(msg)
        except Exception as e:
            # Nếu email sai tên miền hoặc tài khoản không tồn tại, máy chủ SMTP từ chối gửi
            return None, "Không thể gửi thư xác nhận đến email này. Vui lòng kiểm tra lại email có thật hay không!"

        # 5. Lưu người dùng mới vào Database
        try:
            new_user = User(
                Email=email,
                PasswordHash=generate_password_hash(password),
                FullName=full_name,
                Role='MEMBER'
            )
            db.session.add(new_user)
            db.session.commit()
            return AuthService._format_user(new_user), None
        except Exception as e:
            db.session.rollback()
            return None, f"Lỗi lưu trữ dữ liệu: {str(e)}"

    @staticmethod
    def login(email, password):
        email = (email or '').strip().lower()
        if not email or not password:
            return None, "Vui lòng nhập email và mật khẩu!"

        user = User.query.filter_by(Email=email).first()

        # Dùng phương thức check_password nếu có trong model, fallback sang check_password_hash
        has_valid_password = False
        if user:
            if hasattr(user, 'check_password'):
                has_valid_password = user.check_password(password)
            else:
                has_valid_password = check_password_hash(user.PasswordHash, password)

        if not user or not has_valid_password:
            return None, "Email hoặc mật khẩu không chính xác!"

        return AuthService._format_user(user), None