"""Current integrated contracts; disposable SQLite only, gateway/mail are mocked."""
import hashlib,hmac,json,os,secrets,sys,unittest
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import text
from app.extensions import db
from app.models.user import User,SubscriptionPlan,PaymentTransaction
from app.services.profile_service import ProfileService
from app.services.nutrition_service import NutritionService
from app.services.payment_service import PaymentService
import test_meal_api as fixtures
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"setup"))
from init_demo_test_database import schema_statements, reference_statements


class ReleaseContracts(unittest.TestCase):
    setUp=fixtures.ApiTests.setUp
    tearDown=fixtures.ApiTests.tearDown
    login_headers=fixtures.ApiTests.login_headers

    def plan(self):
        plan=SubscriptionPlan(PlanName="Synthetic test plan",PriceVnd=100000,DurationDays=30,IsActive=True)
        db.session.add(plan);db.session.commit();return plan

    def test_core_profile_activity_fallback_matches_nutrition_adapter(self):
        for activity in ("unknown","MODERATE","1.4"):
            payload={"user_id":1,"gender":"male","age":22,"height":172,"weight":65,"activity_level":activity,"goal":"maintain"}
            saved=self.client.post("/save",json=payload,headers=self.headers)
            self.assertEqual(saved.status_code,200,saved.json)
            calculated=NutritionService.calculate(payload)
            for key in ("bmr","tdee","target_kcal","target_water_ml"):
                self.assertEqual(saved.json["data"][key],calculated[key])
            self.assertEqual(self.client.get("/api/nutrition/me",headers=self.headers).json["data"]["target_kcal"],calculated["target_kcal"])

    def test_fresh_schema_has_twenty_tables_and_safe_payment_defaults(self):
        statements=schema_statements();payment=next(s for s in statements if s.startswith("CREATE TABLE PaymentTransactions"))
        self.assertIn("DEFAULT 'PENDING'",payment)
        self.assertIn("REFERENCES Users(UserId) ON DELETE RESTRICT",payment)
        self.assertFalse(any(s.startswith(("DROP","ALTER","INSERT")) for s in statements))
        refs=reference_statements();self.assertEqual(len(refs),4)
        self.assertTrue(all("INSERT INTO Users" not in s and "CreatedBy" not in s for s in refs))

    def test_mock_checkout_pending_then_signed_webhook_is_idempotent(self):
        plan=self.plan()
        with patch.object(PaymentService,"bank_is_configured",return_value=True),patch.object(PaymentService,"generate_vietqr_url",return_value="about:blank#mock-payment"),patch.object(PaymentService,"send_payment_pending_email") as mail:
            response=self.client.post("/api/payment/checkout",json={"plan_id":plan.PlanId},headers={"X-User-Id":"1"})
        self.assertEqual(response.status_code,201,response.json);mail.assert_called_once()
        transaction=PaymentTransaction.query.one();self.assertEqual(transaction.Status,"PENDING")
        self.assertEqual(db.session.get(User,1).SubscriptionStatus,"FREE")
        payload=json.dumps({"transaction_code":transaction.TransactionCode,"status":"SUCCESS"}).encode()
        secret=secrets.token_urlsafe(32);signature=hmac.new(secret.encode(),payload,hashlib.sha256).hexdigest()
        with patch.dict(os.environ,{"PAYMENT_WEBHOOK_SECRET":secret}),patch.object(PaymentService,"send_payment_success_email") as sent:
            self.assertEqual(self.client.post("/api/payment/webhook",data=payload,content_type="application/json",headers={"X-Payment-Signature":"invalid-signature"}).status_code,401)
            good=self.client.post("/api/payment/webhook",data=payload,content_type="application/json",headers={"X-Payment-Signature":signature})
            self.assertEqual(good.status_code,200,good.json)
            expires=db.session.get(User,1).PremiumExpiresAt
            again=self.client.post("/api/payment/webhook",data=payload,content_type="application/json",headers={"X-Payment-Signature":signature})
            self.assertEqual(again.status_code,200);self.assertEqual(db.session.get(User,1).PremiumExpiresAt,expires);sent.assert_called_once()
        self.assertEqual(PaymentTransaction.query.one().Status,"SUCCESS")
        self.assertEqual(db.session.get(User,1).SubscriptionStatus,"PREMIUM")

    def test_unconfigured_bank_does_not_create_transaction(self):
        plan=self.plan()
        with patch.object(PaymentService,"bank_is_configured",return_value=False),patch.object(PaymentService,"send_payment_pending_email") as mail:
            response=self.client.post("/api/payment/checkout",json={"plan_id":plan.PlanId},headers={"X-User-Id":"1"})
        self.assertEqual(response.status_code,503);self.assertEqual(PaymentTransaction.query.count(),0);mail.assert_not_called()
