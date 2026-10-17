
package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;

import java.sql.*;
import java.time.LocalDateTime;
import java.util.Optional;

public class RegistrationOTPDAO {

    public record RegistrationOTP(
            String email,
            String fullName,
            String passwordHash,
            String otpHash,
            LocalDateTime expiresAt,
            LocalDateTime lastSentAt,
            int attempts,
            LocalDateTime windowStart,
            int sentInWindow
    ) {}

    public Optional<RegistrationOTP> findByEmail(String email)
            throws SQLException {

        String sql = """
            SELECT email, full_name, password_hash,
                   otp_hash, expires_at, last_sent_at,
                   attempts, window_start, sent_in_window
            FROM registrationotps
            WHERE email = ?
            """;

        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            ps.setString(1, email);

            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) {
                    return Optional.empty();
                }

                return Optional.of(mapRow(rs));
            }
        }
    }

    public void save(RegistrationOTP otp)
            throws SQLException {

        String sql = """
            INSERT INTO registrationotps (
                email, full_name, password_hash,
                otp_hash, expires_at, last_sent_at,
                attempts, window_start, sent_in_window
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON DUPLICATE KEY UPDATE
                full_name = VALUES(full_name),
                password_hash = VALUES(password_hash),
                otp_hash = VALUES(otp_hash),
                expires_at = VALUES(expires_at),
                last_sent_at = VALUES(last_sent_at),
                attempts = VALUES(attempts),
                window_start = VALUES(window_start),
                sent_in_window = VALUES(sent_in_window)
            """;

        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            ps.setString(1, otp.email());
            ps.setString(2, otp.fullName());
            ps.setString(3, otp.passwordHash());
            ps.setString(4, otp.otpHash());
            ps.setTimestamp(5, Timestamp.valueOf(otp.expiresAt()));
            ps.setTimestamp(6, Timestamp.valueOf(otp.lastSentAt()));
            ps.setInt(7, otp.attempts());
            ps.setTimestamp(8, Timestamp.valueOf(otp.windowStart()));
            ps.setInt(9, otp.sentInWindow());

            ps.executeUpdate();
        }
    }

    public void incrementAttempts(String email)
            throws SQLException {

        String sql = """
            UPDATE registrationotps
            SET attempts = attempts + 1
            WHERE email = ?
            """;

        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            ps.setString(1, email);
            ps.executeUpdate();
        }
    }

    public void deleteByEmail(String email)
            throws SQLException {

        String sql = """
            DELETE FROM registrationotps
            WHERE email = ?
            """;

        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            ps.setString(1, email);
            ps.executeUpdate();
        }
    }

    private RegistrationOTP mapRow(ResultSet rs)
            throws SQLException {

        return new RegistrationOTP(
                rs.getString("email"),
                rs.getString("full_name"),
                rs.getString("password_hash"),
                rs.getString("otp_hash"),
                rs.getTimestamp("expires_at").toLocalDateTime(),
                rs.getTimestamp("last_sent_at").toLocalDateTime(),
                rs.getInt("attempts"),
                rs.getTimestamp("window_start").toLocalDateTime(),
                rs.getInt("sent_in_window")
        );
    }

public Optional<RegistrationOTP> findByEmailForUpdate(
        Connection conn, String email) throws SQLException {

    String sql = """
        SELECT email, full_name, password_hash,
               otp_hash, expires_at, last_sent_at,
               attempts, window_start, sent_in_window
        FROM registrationotps
        WHERE email = ?
        FOR UPDATE
        """;

    try (PreparedStatement ps = conn.prepareStatement(sql)) {
        ps.setString(1, email);

        try (ResultSet rs = ps.executeQuery()) {
            if (!rs.next()) {
                return Optional.empty();
            }
            return Optional.of(mapRow(rs));
        }
    }
}

public void deleteByEmail(Connection conn, String email)
        throws SQLException {

    String sql = "DELETE FROM registrationotps WHERE email = ?";

    try (PreparedStatement ps = conn.prepareStatement(sql)) {
        ps.setString(1, email);
        ps.executeUpdate();
    }
}

}
