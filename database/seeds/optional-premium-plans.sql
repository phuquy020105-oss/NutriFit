-- OPTIONAL sample prices for local / VNPay sandbox development. Do not run for real pricing.
-- Review the prices and ensure these plans do not already exist before executing.
USE NutriFitDB_Java;
INSERT INTO subscriptionplans(plan_name, price_vnd, duration_days, description, is_active)
SELECT 'Premium 30 ngày', 49000, 30, 'Truy cập quyền lợi Premium trong 30 ngày', 1
WHERE NOT EXISTS (SELECT 1 FROM subscriptionplans WHERE duration_days = 30 AND is_active = 1);
INSERT INTO subscriptionplans(plan_name, price_vnd, duration_days, description, is_active)
SELECT 'Premium dài hạn', 399000, 365, 'Truy cập quyền lợi Premium trong 365 ngày', 1
WHERE NOT EXISTS (SELECT 1 FROM subscriptionplans WHERE duration_days = 365 AND is_active = 1);
