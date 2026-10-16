
package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.HexFormat;

public class RegistrationOTPIPQuotaDAO {

    private static final int MAX_REQUESTS = 10;

    public boolean tryConsumeQuota(String clientIp)
            throws SQLException {

        if (clientIp == null || clientIp.isBlank()) {
            throw new IllegalArgumentException(
                    "Client IP is required"
            );
        }

        String ipHash = hashIp(clientIp);
        LocalDateTime now = LocalDateTime.now();

        try (Connection conn = DatabaseConfig.getConnection()) {
            conn.setAutoCommit(false);

            try {
                // Tạo hàng quota nếu IP chưa có.
                String insertSql = """
                    INSERT IGNORE INTO registrationotpipquota
                    (ip_hash, window_start, sent_in_window)
                    VALUES (?, ?, 0)
                    """;

                try (PreparedStatement ps =
                             conn.prepareStatement(insertSql)) {
                    ps.setString(1, ipHash);
                    ps.setTimestamp(2, Timestamp.valueOf(now));
                    ps.executeUpdate();
                }

                String selectSql = """
                    SELECT window_start, sent_in_window
                    FROM registrationotpipquota
                    WHERE ip_hash = ?
                    FOR UPDATE
                    """;

                LocalDateTime windowStart;
                int count;

                try (PreparedStatement ps =
                             conn.prepareStatement(selectSql)) {
                    ps.setString(1, ipHash);

                    try (ResultSet rs = ps.executeQuery()) {
                        if (!rs.next()) {
                            throw new SQLException(
                                    "IP quota record not found"
                            );
                        }

                        windowStart = rs.getTimestamp(
                                "window_start").toLocalDateTime();
                        count = rs.getInt("sent_in_window");
                    }
                }

                if (windowStart.isBefore(now.minusHours(1))) {
                    windowStart = now;
                    count = 0;
                }

                if (count >= MAX_REQUESTS) {
                    conn.commit();
                    return false;
                }

                String updateSql = """
                    UPDATE registrationotpipquota
                    SET window_start = ?,
                        sent_in_window = ?
                    WHERE ip_hash = ?
                    """;

                try (PreparedStatement ps =
                             conn.prepareStatement(updateSql)) {
                    ps.setTimestamp(
                            1, Timestamp.valueOf(windowStart));
                    ps.setInt(2, count + 1);
                    ps.setString(3, ipHash);
                    ps.executeUpdate();
                }

                conn.commit();
                return true;

            } catch (SQLException | RuntimeException e) {
                conn.rollback();
                throw e;
            }
        }
    }

    private String hashIp(String ip) {
        String secret = System.getenv("NUTRIFIT_IP_HASH_SECRET");

        if (secret == null || secret.isBlank()) {
            throw new IllegalStateException(
                    "Missing NUTRIFIT_IP_HASH_SECRET"
            );
        }

        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(
                    secret.getBytes(StandardCharsets.UTF_8),
                    "HmacSHA256"
            ));

            return HexFormat.of().formatHex(
                    mac.doFinal(ip.getBytes(StandardCharsets.UTF_8))
            );

        } catch (Exception e) {
            throw new IllegalStateException(
                    "Unable to hash client IP", e
            );
        }
    }
}
