
package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;

import java.sql.*;
import java.time.LocalDateTime;

public class PasswordResetOTPDAO {

    public record PasswordResetOTP(
            String email,
            String otpHash,
            LocalDateTime expiresAt,
            int attempts,
            LocalDateTime lastSentAt,
            LocalDateTime windowStart,
            int sentInWindow
    ) {}

    public PasswordResetOTP findByEmail(String email)
            throws SQLException {
        try (Connection conn = DatabaseConfig.getConnection()) {
            return findByEmail(conn, email);
        }
    }

    public PasswordResetOTP findByEmail(Connection conn, String email)
            throws SQLException {

        String sql = """
                SELECT email, otp_hash, expires_at, attempts,
                       last_sent_at, window_start, sent_in_window
                FROM password_reset_otps
                WHERE email = ?
                """;

        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, email);

            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? mapRow(rs) : null;
            }
        }
    }

    public PasswordResetOTP findByEmailForUpdate(
            Connection conn, String email) throws SQLException {

        String sql = """
                SELECT email, otp_hash, expires_at, attempts,
                       last_sent_at, window_start, sent_in_window
                FROM password_reset_otps
                WHERE email = ?
                FOR UPDATE
                """;

        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, email);

            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? mapRow(rs) : null;
            }
        }
    }

    public void save(PasswordResetOTP otp) throws SQLException {
        try (Connection conn = DatabaseConfig.getConnection()) {
            save(conn, otp);
        }
    }

    public void save(Connection conn, PasswordResetOTP otp)
            throws SQLException {

        String sql = """
                INSERT INTO password_reset_otps
                    (email, otp_hash, expires_at, attempts,
                     last_sent_at, window_start, sent_in_window)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON DUPLICATE KEY UPDATE
                    otp_hash = VALUES(otp_hash),
                    expires_at = VALUES(expires_at),
                    attempts = VALUES(attempts),
                    last_sent_at = VALUES(last_sent_at),
                    window_start = VALUES(window_start),
                    sent_in_window = VALUES(sent_in_window)
                """;

        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, otp.email());
            ps.setString(2, otp.otpHash());
            ps.setTimestamp(3, Timestamp.valueOf(otp.expiresAt()));
            ps.setInt(4, otp.attempts());
            ps.setTimestamp(5, Timestamp.valueOf(otp.lastSentAt()));
            ps.setTimestamp(6, Timestamp.valueOf(otp.windowStart()));
            ps.setInt(7, otp.sentInWindow());
            ps.executeUpdate();
        }
    }

    public void incrementAttempts(Connection conn, String email)
            throws SQLException {

        String sql = """
                UPDATE password_reset_otps
                SET attempts = attempts + 1
                WHERE email = ?
                """;

        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, email);
            ps.executeUpdate();
        }
    }

    public void deleteByEmail(Connection conn, String email)
            throws SQLException {

        String sql = """
                DELETE FROM password_reset_otps
                WHERE email = ?
                """;

        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, email);
            ps.executeUpdate();
        }
    }

    public void deleteByEmail(String email) throws SQLException {
        try (Connection conn = DatabaseConfig.getConnection()) {
            deleteByEmail(conn, email);
        }
    }

    private PasswordResetOTP mapRow(ResultSet rs)
            throws SQLException {

        return new PasswordResetOTP(
                rs.getString("email"),
                rs.getString("otp_hash"),
                rs.getTimestamp("expires_at").toLocalDateTime(),
                rs.getInt("attempts"),
                rs.getTimestamp("last_sent_at").toLocalDateTime(),
                rs.getTimestamp("window_start").toLocalDateTime(),
                rs.getInt("sent_in_window")
        );
    }
}
