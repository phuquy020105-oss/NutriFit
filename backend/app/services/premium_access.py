"""Read Quy's entitlement contract without requiring his newer ORM model."""
from datetime import datetime, timezone
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.services.module_errors import ModuleError


class PremiumAccess:
    @staticmethod
    def is_active(user_id):
        try:
            columns = {c["name"] for c in inspect(db.session.connection()).get_columns("Users")}
            if not {"SubscriptionStatus", "PremiumExpiresAt"} <= columns:
                raise ModuleError("Chưa thể kiểm tra quyền Premium. Vui lòng thử lại sau.",
                                  "PREMIUM_UNAVAILABLE", 503)
            row = db.session.execute(text(
                "SELECT SubscriptionStatus, PremiumExpiresAt FROM Users WHERE UserId=:uid"
            ), {"uid": user_id}).mappings().first()
        except SQLAlchemyError:
            raise ModuleError("Chưa thể kiểm tra quyền Premium. Vui lòng thử lại sau.",
                              "PREMIUM_UNAVAILABLE", 503) from None
        if row is None or row["SubscriptionStatus"] != "PREMIUM" or row["PremiumExpiresAt"] is None:
            return False
        expiry = row["PremiumExpiresAt"]
        try:
            if isinstance(expiry, str):
                expiry = datetime.fromisoformat(expiry)
            # Quy's Payment route stores datetime.utcnow() in a timezone-free DATETIME.
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            return expiry > datetime.now(timezone.utc)
        except (ValueError, TypeError, AttributeError):
            raise ModuleError("Chưa thể kiểm tra quyền Premium. Vui lòng thử lại sau.",
                              "PREMIUM_UNAVAILABLE", 503) from None

    @staticmethod
    def require(user_id):
        if not PremiumAccess.is_active(user_id):
            raise ModuleError("Chức năng này cần Premium còn hiệu lực.", "PREMIUM_REQUIRED", 403)
