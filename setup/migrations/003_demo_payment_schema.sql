-- Demo Payment schema: apply only after backup + successful isolated restore rehearsal.
-- Source: backend/app/models/user.py and setup/upgrade_existing_database.sql.
-- User-approved safe Demo defaults: existing Users become FREE with NULL expiry.
-- Status defaults to PENDING in SQL and ORM; checkout already supplies PENDING.
-- User FK uses RESTRICT to preserve payment history; there is no account-delete API.
-- Only a confirmed webhook moves a transaction to SUCCESS. API JSON remains unchanged.
-- No plan seeds, no Nutrition DDL, no account grants, no destructive rollback.
--
-- BACKUP (Windows CMD; choose a NEW filename, do not overwrite an older backup):
-- mkdir D:\NutriFitBackups
-- mysqldump -h 127.0.0.1 -P 3306 -u root -p --single-transaction --routines --events --triggers --no-tablespaces --set-gtid-purged=OFF --result-file="D:\NutriFitBackups\NutriFitDB_before_demo_payment_20261013.sql" NutriFitDB
-- Check exit code, file size and SHA256. A nonempty file is NOT a tested restore.
-- Restore rehearsal needs separate approval and an isolated database.
-- Stop application writes and concurrent DDL before the backup/application.
--
-- PREFLIGHT ONLY (default; no schema changes):
-- mysql -h 127.0.0.1 -P 3306 -u root -p NutriFitDB < setup\migrations\003_demo_payment_schema.sql
-- APPLY ONLY AFTER APPROVAL + VERIFIED BACKUP + PREFLIGHT PASS:
-- mysql -h 127.0.0.1 -P 3306 -u root -p --init-command="SET @nutrifit_demo_payment_apply=1" NutriFitDB < setup\migrations\003_demo_payment_schema.sql
-- Never use --force. Stop on the first SQL error; MySQL DDL implicitly commits.
-- Any existing target object blocks ALL automatic DDL, including a partial run.
-- Re-running an applied migration skips DDL; inspect the schema before continuing.
-- Do not apply this script to another database or run create_database.sql/upgrade_existing_database.sql.
--
-- VERIFY after an approved apply:
-- SELECT DATABASE(); SHOW TABLES; SHOW CREATE TABLE Users;
-- SHOW CREATE TABLE SubscriptionPlans; SHOW CREATE TABLE PaymentTransactions;
-- Expected tables 18 -> 20; catalog active count 141; legacy template count 63.
-- Compare counts/IDs/snapshots against the pre-apply snapshot for every existing table.
-- Verify the new plan/payment tables are EMPTY; this migration contains no INSERT.
-- ROLLBACK: do not issue DROP/DROP COLUMN automatically. Preserve partial additions,
-- stop writes and review forward repair or approved recovery from the verified backup.

-- Target defaults to NutriFitDB. An isolated rehearsal must explicitly name its DB.
-- Example test connection init command (single SET statement):
-- SET @nutrifit_demo_payment_target_db='nutrifit_demo_payment_restore_UNIQUE', @nutrifit_demo_payment_apply=1;
-- Only the real target or this dedicated rehearsal prefix can pass the guard.
SET @demo_target = COALESCE(@nutrifit_demo_payment_target_db, 'NutriFitDB');
SET @demo_db_ok = COALESCE(LOWER(DATABASE()) = LOWER(@demo_target) AND
  (LOWER(@demo_target) = 'nutrifitdb' OR LOWER(@demo_target) REGEXP '^nutrifit_demo_payment_restore_[a-z0-9_]+$'), 0);
SET @demo_users_ok = (
  SELECT COUNT(*) = 1 FROM information_schema.TABLES
  WHERE TABLE_SCHEMA = DATABASE() AND LOWER(TABLE_NAME) = 'users'
    AND TABLE_TYPE = 'BASE TABLE' AND ENGINE = 'InnoDB'
    AND TABLE_COLLATION = 'utf8mb4_unicode_ci'
);
SET @demo_user_id_ok = (
  SELECT COUNT(*) = 1 FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND LOWER(TABLE_NAME) = 'users'
    AND COLUMN_NAME = 'UserId' AND DATA_TYPE = 'int'
    AND COLUMN_TYPE NOT LIKE '%unsigned%' AND IS_NULLABLE = 'NO'
    AND COLUMN_KEY = 'PRI' AND EXTRA LIKE '%auto_increment%'
);
SET @demo_table_count = (
  SELECT COUNT(*) FROM information_schema.TABLES
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE'
);
SET @demo_existing_premium_columns = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND LOWER(TABLE_NAME) = 'users'
    AND COLUMN_NAME IN ('SubscriptionStatus', 'PremiumExpiresAt')
);
SET @demo_existing_payment_tables = (
  SELECT COUNT(*) FROM information_schema.TABLES
  WHERE TABLE_SCHEMA = DATABASE() AND LOWER(TABLE_NAME) IN ('subscriptionplans', 'paymenttransactions')
);
SET @demo_fk_names_free = (
  SELECT COUNT(*) = 0 FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = DATABASE() AND CONSTRAINT_NAME IN ('FK_Payments_Users', 'FK_Payments_Plans')
);
SET @demo_nutrition_present = (
  SELECT COUNT(*) = 4 FROM information_schema.TABLES
  WHERE TABLE_SCHEMA = DATABASE() AND LOWER(TABLE_NAME) IN
    ('nutritionfoodcatalog', 'nutritionlegacymenus', 'nutritionfoodintake', 'nutritionmealdetails')
);
SET @demo_preflight_ok = (@demo_db_ok AND @demo_users_ok AND @demo_user_id_ok
  AND @demo_table_count = 18 AND @demo_existing_premium_columns = 0
  AND @demo_existing_payment_tables = 0 AND @demo_fk_names_free AND @demo_nutrition_present);
SET @demo_go = (@demo_preflight_ok AND COALESCE(@nutrifit_demo_payment_apply, 0) = 1);
SELECT DATABASE() AS selected_database, @demo_preflight_ok AS preflight_pass,
  @demo_go AS apply_enabled, @demo_table_count AS current_table_count,
  @demo_existing_premium_columns AS existing_premium_columns,
  @demo_existing_payment_tables AS existing_payment_tables,
  CASE WHEN NOT @demo_preflight_ok THEN 'BLOCKED: unexpected/existing/partial schema; inspect before applying'
       WHEN NOT @demo_go THEN 'PREFLIGHT PASS: DDL disabled; explicit approval/apply flag required'
       ELSE 'APPLY ENABLED: four additive schema operations only' END AS status;
SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY, EXTRA
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE() AND LOWER(TABLE_NAME) IN ('users', 'subscriptionplans', 'paymenttransactions')
ORDER BY TABLE_NAME, ORDINAL_POSITION;

SET @demo_ddl = IF(@demo_go, 'ALTER TABLE Users ADD COLUMN SubscriptionStatus VARCHAR(20) DEFAULT ''FREE''', 'SELECT ''SKIPPED operation 1: apply disabled or preflight blocked'' AS status');
PREPARE demo_stmt FROM @demo_ddl;
EXECUTE demo_stmt;
DEALLOCATE PREPARE demo_stmt;

SET @demo_ddl = IF(@demo_go, 'ALTER TABLE Users ADD COLUMN PremiumExpiresAt DATETIME NULL', 'SELECT ''SKIPPED operation 2: apply disabled or preflight blocked'' AS status');
PREPARE demo_stmt FROM @demo_ddl;
EXECUTE demo_stmt;
DEALLOCATE PREPARE demo_stmt;

SET @demo_ddl = IF(@demo_go, 'CREATE TABLE IF NOT EXISTS SubscriptionPlans (
  PlanId INT AUTO_INCREMENT PRIMARY KEY,
  PlanName VARCHAR(100) NOT NULL,
  PriceVnd INT NOT NULL,
  DurationDays INT NOT NULL,
  Description VARCHAR(255) NULL,
  IsActive BOOLEAN DEFAULT TRUE,
  CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci', 'SELECT ''SKIPPED operation 3: apply disabled or preflight blocked'' AS status');
PREPARE demo_stmt FROM @demo_ddl;
EXECUTE demo_stmt;
DEALLOCATE PREPARE demo_stmt;

SET @demo_ddl = IF(@demo_go, 'CREATE TABLE IF NOT EXISTS PaymentTransactions (
  TransactionId INT AUTO_INCREMENT PRIMARY KEY,
  UserId INT NOT NULL,
  PlanId INT NOT NULL,
  AmountVnd INT NOT NULL,
  PaymentMethod VARCHAR(50) NOT NULL,
  TransactionCode VARCHAR(100) UNIQUE NOT NULL,
  Status VARCHAR(20) DEFAULT ''PENDING'',
  CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT FK_Payments_Users FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE RESTRICT,
  CONSTRAINT FK_Payments_Plans FOREIGN KEY (PlanId) REFERENCES SubscriptionPlans(PlanId) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci', 'SELECT ''SKIPPED operation 4: apply disabled or preflight blocked'' AS status');
PREPARE demo_stmt FROM @demo_ddl;
EXECUTE demo_stmt;
DEALLOCATE PREPARE demo_stmt;

SELECT CASE WHEN @demo_go THEN 'Four schema operations completed; verify metadata and unchanged data now' ELSE 'No schema operations executed' END AS result;
