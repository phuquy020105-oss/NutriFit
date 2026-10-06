from datetime import datetime
from app.extensions import db

class User(db.Model):
    __tablename__ = 'Users'

    UserId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(255), nullable=False)
    FullName = db.Column(db.String(100), nullable=False)
    Role = db.Column(db.String(20), default='MEMBER')
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade="all, delete-orphan")