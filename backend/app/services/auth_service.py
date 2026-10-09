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
    def register(email, password, full_name):
        email = email.strip().lower()

        # 1. Kiểm tra định dạng cú pháp email
        if not AuthService.validate_email_format(email):
            return None, "Định dạng email không hợp lệ!"

        # 2. Kiểm tra email đã có trong hệ thống chưa
        if User.query.filter_by(Email=email).first():
            return None, "Email này đã được sử dụng!"

        # 3. Gửi email xác nhận đến email thật
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

        # 4. Khi gửi mail thành công -> Lưu người dùng mới vào Database
        new_user = User(
            Email=email,
            PasswordHash=generate_password_hash(password),
            FullName=full_name,
            Role='MEMBER'
        )
        db.session.add(new_user)
        db.session.commit()

        return new_user.to_dict(), None

    @staticmethod
    def login(email, password):
        email = email.strip().lower()
        user = User.query.filter_by(Email=email).first()

        if not user or not check_password_hash(user.PasswordHash, password):
            return None, "Email hoặc mật khẩu không chính xác!"

        return user.to_dict(), None