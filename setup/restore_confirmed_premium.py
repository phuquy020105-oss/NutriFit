"""Inspect/repair ONE historical QR confirmation that didn't grant Premium.

From NutriFit-NextUI:
  ..\\.venv\\Scripts\\python.exe setup\\restore_confirmed_premium.py --user-id 6 --transaction-id 19
  ..\\.venv\\Scripts\\python.exe setup\\restore_confirmed_premium.py --user-id 6 --transaction-id 19 --apply

A past confirmed transaction is never restored automatically. This command can
be intentionally run for a historical purchase after inspecting its owner.
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.user import User, SubscriptionPlan, PaymentTransaction  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description='Restore one confirmed purchase for its owner only.')
    parser.add_argument('--user-id', type=int, required=True, help='UserId of the account owner')
    parser.add_argument('--transaction-id', type=int, required=True, help='TransactionId of a confirmed QR purchase')
    parser.add_argument('--apply', action='store_true', help='Actually grant Premium. Default is preview only.')
    args = parser.parse_args()
    app = create_app()
    with app.app_context():
        if db.engine.dialect.name != 'mysql':
            raise SystemExit('Only run against the configured MySQL database; no changes made.')
        user = db.session.get(User, args.user_id)
        txn = db.session.get(PaymentTransaction, args.transaction_id)
        if not user or not txn or txn.UserId != args.user_id:
            raise SystemExit('Account/transaction not found for the SAME UserId. No changes made.')
        plan = db.session.get(SubscriptionPlan, txn.PlanId)
        if not plan or not plan.DurationDays or plan.DurationDays <= 0:
            raise SystemExit('Premium plan is missing or invalid. No changes made.')
        if txn.PaymentMethod != 'DEMO_QR' or txn.Status not in ('DEMO_SUCCESS', 'DEMO_MAIL_ERROR'):
            raise SystemExit('Transaction is not a confirmed QR purchase. No changes made.')
        now = datetime.utcnow()
        active = (user.SubscriptionStatus == 'PREMIUM' and user.PremiumExpiresAt is not None
                  and user.PremiumExpiresAt > now)
        print(f'Account UserId={user.UserId}: {user.FullName} ({user.Email})')
        print(f'Transaction #{txn.TransactionId}: plan={plan.PlanName}, amount={txn.AmountVnd} VND, status={txn.Status}')
        print(f'Existing: {user.SubscriptionStatus}, expires={user.PremiumExpiresAt}; active={active}')
        if active:
            print('Premium is already active; no additional time granted. No changes made.')
            return
        new_expiry = now + timedelta(days=plan.DurationDays)
        if not args.apply:
            print(f'PREVIEW ONLY: will grant Premium until {new_expiry:%Y-%m-%d %H:%M:%S} UTC')
            print('Run again with --apply only after verifying account and transaction IDs.')
            return
        user.SubscriptionStatus = 'PREMIUM'
        user.PremiumExpiresAt = new_expiry
        db.session.commit()
        print(f'APPLIED: UserId={user.UserId} Premium until {new_expiry:%Y-%m-%d %H:%M:%S} UTC.')
        print('Transaction type remains unchanged; this does not record bank income.')


if __name__ == '__main__':
    main()
