-- Local/upgrade DDL only; select the intended database before running.
-- Existing data is retained. MySQL DDL is not transactionally reversible.
CREATE TABLE IF NOT EXISTS password_reset_otps (
 email VARCHAR(255) NOT NULL PRIMARY KEY,
 otp_hash VARCHAR(255) NOT NULL,
 expires_at DATETIME NOT NULL,
 attempts INT UNSIGNED NOT NULL DEFAULT 0,
 last_sent_at DATETIME NOT NULL,
 window_start DATETIME NOT NULL,
 sent_in_window INT UNSIGNED NOT NULL DEFAULT 0,
 CONSTRAINT fk_password_reset_email FOREIGN KEY (email) REFERENCES users(email) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
