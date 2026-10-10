from app.extensions import db

class User(db.Model):
    __tablename__ = 'Users'

    UserId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(255), nullable=False)
    FullName = db.Column(db.String(100), nullable=False)
    Role = db.Column(db.String(20), default='MEMBER', nullable=True)
    SubscriptionStatus = db.Column(db.String(20), default='FREE', nullable=True)
    PremiumExpiresAt = db.Column(db.DateTime, nullable=True)
    CreatedAt = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            "id": self.UserId,
            "email": self.Email,
            "full_name": self.FullName,
            "role": self.Role or 'MEMBER',
            "subscription_status": self.SubscriptionStatus or 'FREE',
            "premium_expires_at": self.PremiumExpiresAt.strftime('%Y-%m-%d %H:%M:%S') if self.PremiumExpiresAt else None,
            "created_at": self.CreatedAt.strftime('%Y-%m-%d %H:%M:%S') if self.CreatedAt else None
        }


class SubscriptionPlan(db.Model):
    __tablename__ = 'SubscriptionPlans'

    PlanId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PlanName = db.Column(db.String(100), nullable=False)
    PriceVnd = db.Column(db.Integer, nullable=False)
    DurationDays = db.Column(db.Integer, nullable=False)
    Description = db.Column(db.String(255), nullable=True)
    IsActive = db.Column(db.Boolean, default=True)
    CreatedAt = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            "id": self.PlanId,
            "name": self.PlanName,
            "price": self.PriceVnd,
            "duration_days": self.DurationDays,
            "description": self.Description,
            "is_active": self.IsActive
        }


class PaymentTransaction(db.Model):
    __tablename__ = 'PaymentTransactions'

    TransactionId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'), nullable=False)
    PlanId = db.Column(db.Integer, db.ForeignKey('SubscriptionPlans.PlanId'), nullable=False)
    AmountVnd = db.Column(db.Integer, nullable=False)
    PaymentMethod = db.Column(db.String(50), nullable=False)
    TransactionCode = db.Column(db.String(100), unique=True, nullable=False)
    Status = db.Column(db.String(20), default='SUCCESS')
    CreatedAt = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('User', backref='transactions')
    plan = db.relationship('SubscriptionPlan', backref='transactions')

    def to_dict(self):
        return {
            "transaction_id": self.TransactionId,
            "user_id": self.UserId,
            "user_name": self.user.FullName if self.user else None,
            "user_email": self.user.Email if self.user else None,
            "plan_name": self.plan.PlanName if self.plan else None,
            "amount": self.AmountVnd,
            "payment_method": self.PaymentMethod,
            "transaction_code": self.TransactionCode,
            "status": self.Status,
            "created_at": self.CreatedAt.strftime('%Y-%m-%d %H:%M:%S') if self.CreatedAt else None
        }