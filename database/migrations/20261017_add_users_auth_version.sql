-- Run in MySQL Workbench with DBA/root permission, in the application DB.
-- The source schema.sql does not include auth_version, but UserDAO/AuthFilter require it.
-- Idempotent: adds column only if missing. Does NOT drop any table or data.
USE NutriFitDB_Java;
SET @has_column := (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'users' AND column_name = 'auth_version'
);
SET @migration_sql := IF(
  @has_column = 0,
  'ALTER TABLE users ADD COLUMN auth_version BIGINT NOT NULL DEFAULT 0',
  'SELECT ''users.auth_version already exists'' AS message'
);
PREPARE statement_from_sql FROM @migration_sql;
EXECUTE statement_from_sql;
DEALLOCATE PREPARE statement_from_sql;
SHOW COLUMNS FROM users LIKE 'auth_version';
