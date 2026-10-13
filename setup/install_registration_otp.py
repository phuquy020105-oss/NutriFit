"""One-time, non-destructive OTP tables migration for your configured MySQL DB.

Run from NutriFit project root:
  ..\\.venv\\Scripts\\python.exe setup\\install_registration_otp.py
This never creates/modifies/drops Users or any existing tables.
"""
from pathlib import Path
import sys
from sqlalchemy import inspect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.registration_otp import RegistrationOTP, RegistrationOTPIPQuota  # noqa: E402


def main():
    app = create_app()
    with app.app_context():
        engine = db.engine
        inspector = inspect(engine)
        if engine.dialect.name != 'mysql':
            raise SystemExit('Stopped: .env is not pointing at MySQL. Check your DB_* settings.')
        if not inspector.has_table('Users'):
            raise SystemExit('Stopped: Users table not found. Check DB_NAME; no changes made.')
        # Create ONLY these two new tables; safe to rerun (checkfirst).
        for model in (RegistrationOTP, RegistrationOTPIPQuota):
            model.__table__.create(bind=engine, checkfirst=True)
            print(f'OK: {model.__tablename__}')
        print('OTP migration complete. Existing accounts and health records untouched.')


if __name__ == '__main__':
    main()
