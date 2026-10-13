"""Safe one-time setup for PremiumManualDailyPlans; never drops existing data.

Run from NutriFit-NextUI: python setup/install_manual_meal_plans.py --apply
Without --apply prints the plan only. Uses the same .env as Flask.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    from app import create_app
    from app.extensions import db
    from app.models.premium_manual_plan import PremiumManualDailyPlan
    from sqlalchemy import inspect
    app = create_app()
    with app.app_context():
        table = PremiumManualDailyPlan.__table__
        exists = inspect(db.engine).has_table(table.name)
        print(f"Bảng {table.name}: {'đã tồn tại' if exists else 'chưa có'}")
        if not args.apply:
            print("Chỉ kiểm tra. Thêm --apply để tạo bảng nếu cần.")
            return
        table.create(bind=db.engine, checkfirst=True)
        print("Đã kiểm tra/tạo bảng; các dữ liệu khác không bị thay đổi.")


if __name__ == "__main__":
    main()
