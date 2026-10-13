-- NutriFit - OTP migration for EXISTING database. Does not delete Users or data.
-- Select your current NutriFit database before executing this script.
-- MySQL Workbench: SET DEFAULT SCHEMA for NutriFitDB, or run USE NutriFitDB;
CREATE TABLE IF NOT EXISTS RegistrationOTPs (
  Email VARCHAR(100) NOT NULL PRIMARY KEY,
  FullName VARCHAR(100) NOT NULL,
  PasswordHash VARCHAR(255) NOT NULL,
  OTPHash CHAR(64) NOT NULL,
  ExpiresAt DATETIME NOT NULL,
  LastSentAt DATETIME NOT NULL,
  Attempts INT NOT NULL DEFAULT 0,
  WindowStart DATETIME NOT NULL,
  SentInWindow INT NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS RegistrationOTPIPQuota (
  IPHash CHAR(64) NOT NULL PRIMARY KEY,
  WindowStart DATETIME NOT NULL,
  SentInWindow INT NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
