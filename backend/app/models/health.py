from datetime import datetime
from app.extensions import db

class UserProfile(db.Model):
    __tablename__ = 'UserProfiles'

    ProfileId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId', ondelete='CASCADE'), nullable=False)
    Gender = db.Column(db.String(10), nullable=False)
    Age = db.Column(db.Integer, nullable=False)
    HeightCm = db.Column(db.Float, nullable=False)
    WeightKg = db.Column(db.Float, nullable=False)
    ActivityLevel = db.Column(db.Float, nullable=False)
    Goal = db.Column(db.String(20), nullable=False)
    Bmr = db.Column(db.Float)
    Tdee = db.Column(db.Float)
    TargetKcal = db.Column(db.Float)
    TargetWaterMl = db.Column(db.Integer)
    UpdatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)