from app.extensions import db
from app.models.user import User
from app.security import hash_password, verify_password

class AuthService:
    @staticmethod
    def register(email, password, full_name):
        if User.query.filter_by(Email=email).first():
            return None, "Email đã được sử dụng."
        
        user = User(
            Email=email,
            PasswordHash=hash_password(password),
            FullName=full_name
        )
        db.session.add(user)
        db.session.commit()
        return user, None

    @staticmethod
    def login(email, password):
        user = User.query.filter_by(Email=email).first()
        if not user or not verify_password(password, user.PasswordHash):
            return None, "Email hoặc mật khẩu không chính xác."
        return user, None