
package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.model.User;
import com.nutrifit.model.UserRole;
import com.nutrifit.model.SubscriptionStatus;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
import java.util.Optional;

public class UserDAO {

    // =====================================================
    // 1. TÌM USER THEO EMAIL
    // =====================================================

    public Optional<User> findByEmail(String email)
            throws SQLException {

        try (Connection conn = DatabaseConfig.getConnection()) {
            return findByEmail(conn, email);
        }
    }

    // Sử dụng khi đang có transaction
    public Optional<User> findByEmail(
            Connection conn, String email) throws SQLException {

        String sql = """
                SELECT user_id, email, password_hash,
                       full_name, role, subscription_status,
                       premium_expires_at, created_at,
                       auth_version
                FROM users
                WHERE email = ?
                """;

        try (PreparedStatement ps = conn.prepareStatement(sql)) {

            ps.setString(1, email);

            try (ResultSet rs = ps.executeQuery()) {

                if (rs.next()) {
                    return Optional.of(mapUser(rs));
                }
            }
        }

        return Optional.empty();
    }

    // =====================================================
    // 2. TÌM USER THEO ID
    // =====================================================

    public Optional<User> findById(Long userId)
            throws SQLException {

        String sql = """
                SELECT user_id, email, password_hash,
                       full_name, role, subscription_status,
                       premium_expires_at, created_at,
                       auth_version
                FROM users
                WHERE user_id = ?
                """;

        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            ps.setLong(1, userId);

            try (ResultSet rs = ps.executeQuery()) {

                if (rs.next()) {
                    return Optional.of(mapUser(rs));
                }
            }
        }

        return Optional.empty();
    }

    // =====================================================
    // 3. TẠO TÀI KHOẢN
    // =====================================================

    public Long create(User user) throws SQLException {

        try (Connection conn = DatabaseConfig.getConnection()) {
            return create(conn, user);
        }
    }

    // Không tự commit hoặc đóng connection
    public Long create(Connection conn, User user)
            throws SQLException {

        String sql = """
                INSERT INTO users
                    (email, password_hash, full_name)
                VALUES (?, ?, ?)
                """;

        try (PreparedStatement ps = conn.prepareStatement(
                sql, Statement.RETURN_GENERATED_KEYS)) {

            ps.setString(1, user.getEmail());
            ps.setString(2, user.getPasswordHash());
            ps.setString(3, user.getFullName());

            int affected = ps.executeUpdate();

            if (affected != 1) {
                throw new SQLException("Cannot create user");
            }

            try (ResultSet keys = ps.getGeneratedKeys()) {

                if (keys.next()) {
                    return keys.getLong(1);
                }
            }
        }

        throw new SQLException("Cannot retrieve user ID");
    }

    // =====================================================
    // 4. CẬP NHẬT HỌ TÊN
    // =====================================================

    public boolean updateFullName(
            Long userId, String fullName) throws SQLException {

        String sql = """
                UPDATE users
                SET full_name = ?
                WHERE user_id = ?
                """;

        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            ps.setString(1, fullName);
            ps.setLong(2, userId);

            return ps.executeUpdate() == 1;
        }
    }

    // =====================================================
    // 5. ĐỔI MẬT KHẨU THEO USER ID
    // =====================================================

    /**
     * Được ProfileService sử dụng.
     *
     * Cập nhật password_hash và tăng auth_version
     * trong cùng một câu lệnh SQL.
     */
    public boolean updatePasswordById(
            Long userId, String passwordHash) throws SQLException {

        if (userId == null) {
            throw new IllegalArgumentException(
                    "User ID cannot be null");
        }

        if (passwordHash == null || passwordHash.isBlank()) {
            throw new IllegalArgumentException(
                    "Password hash cannot be empty");
        }

        String sql = """
                UPDATE users
                SET password_hash = ?,
                    auth_version = auth_version + 1
                WHERE user_id = ?
                """;

        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            ps.setString(1, passwordHash);
            ps.setLong(2, userId);

            return ps.executeUpdate() == 1;
        }
    }

    // =====================================================
    // 6. ĐẶT LẠI MẬT KHẨU THEO EMAIL
    // =====================================================

    /**
     * Được Service xử lý quên mật khẩu sử dụng.
     *
     * Không tự commit hoặc đóng connection.
     * Cập nhật mật khẩu và tăng auth_version
     * trong cùng transaction của Service.
     */
    public boolean updatePassword(
            Connection conn,
            String email,
            String passwordHash) throws SQLException {

        if (email == null || email.isBlank()) {
            throw new IllegalArgumentException(
                    "Email cannot be empty");
        }

        if (passwordHash == null || passwordHash.isBlank()) {
            throw new IllegalArgumentException(
                    "Password hash cannot be empty");
        }

        String sql = """
                UPDATE users
                SET password_hash = ?,
                    auth_version = auth_version + 1
                WHERE email = ?
                """;

        try (PreparedStatement ps = conn.prepareStatement(sql)) {

            ps.setString(1, passwordHash);
            ps.setString(2, email);

            return ps.executeUpdate() == 1;
        }
    }

    // =====================================================
    // 7. LẤY AUTH VERSION THEO USER ID
    // =====================================================

    /**
     * Dùng cho AuthFilter kiểm tra phiên đăng nhập.
     */
    public Optional<Long> findAuthVersionById(Long userId)
            throws SQLException {

        String sql = """
                SELECT auth_version
                FROM users
                WHERE user_id = ?
                """;

        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            ps.setLong(1, userId);

            try (ResultSet rs = ps.executeQuery()) {

                if (rs.next()) {
                    return Optional.of(
                            rs.getLong("auth_version"));
                }
            }
        }

        return Optional.empty();
    }

    // =====================================================
    // 8. CHUYỂN MYSQL RESULTSET THÀNH USER OBJECT
    // =====================================================

    private User mapUser(ResultSet rs) throws SQLException {

        User user = new User();

        user.setUserId(rs.getLong("user_id"));
        user.setEmail(rs.getString("email"));
        user.setPasswordHash(rs.getString("password_hash"));
        user.setFullName(rs.getString("full_name"));

        user.setRole(UserRole.valueOf(
                rs.getString("role")));

        user.setSubscriptionStatus(
                SubscriptionStatus.valueOf(
                        rs.getString("subscription_status")));

        Timestamp premiumExpires =
                rs.getTimestamp("premium_expires_at");

        if (premiumExpires != null) {
            user.setPremiumExpiresAt(
                    premiumExpires.toLocalDateTime());
        }

        Timestamp createdAt =
                rs.getTimestamp("created_at");

        if (createdAt != null) {
            user.setCreatedAt(
                    createdAt.toLocalDateTime());
        }

        user.setAuthVersion(rs.getLong("auth_version"));

        return user;
    }
}
