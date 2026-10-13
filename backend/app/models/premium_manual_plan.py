"""One manually composed Premium meal plan per user and local calendar day."""
from datetime import datetime
from app.extensions import db


class PremiumManualDailyPlan(db.Model):
    __tablename__ = "PremiumManualDailyPlans"
    UserId = db.Column(db.Integer, db.ForeignKey("Users.UserId", ondelete="CASCADE"), primary_key=True)
    PlanDate = db.Column(db.Date, primary_key=True)
    PlanData = db.Column(db.Text, nullable=False)
    UpdatedAt = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
