
package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.model.User;
import com.nutrifit.model.UserRole;
import com.nutrifit.model.SubscriptionStatus;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;

import java.util.ArrayList;
import java.util.List;

public class AdminDAO {

    // ==========================================
    // 1. THỐNG KÊ TÀI KHOẢN
    // ==========================================

    public long countUsers() throws SQLException {
        return countBySql("SELECT COUNT(*) FROM users");
    }

    public long countAdmins() throws SQLException {
        return countBySql(
                "SELECT COUNT(*) FROM users WHERE role = 'ADMIN'");
    }

    public long countPremiumUsers() throws SQLException {
        return countBySql("""
                SELECT COUNT(*)
                FROM users
                WHERE subscription_status = 'PREMIUM'
                """);
    }

    public long countNewUsersToday() throws SQLException {
        return countBySql("""
                SELECT COUNT(*)
                FROM users
                WHERE created_at >= CURRENT_DATE()
                  AND created_at < CURRENT_DATE()
                      + INTERVAL 1 DAY
                """);
    }

    private long countBySql(String sql) throws SQLException {

        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {

            return rs.next() ? rs.getLong(1) : 0;
        }
    }

    // ==========================================
    // 2. DANH SÁCH NGƯỜI DÙNG
    // ==========================================

    public List<User> findUsers(String keyword)
            throws SQLException {

        String search = keyword == null ? "" : keyword.trim();

        if (search.length() > 100) {
            throw new IllegalArgumentException(
                    "Từ khóa tìm kiếm quá dài.");
        }

        String sql = """
                SELECT user_id, email, full_name,
                       role, subscription_status,
                       premium_expires_at, created_at,
                       auth_version
                FROM users
                WHERE email LIKE ?
                   OR full_name LIKE ?
                ORDER BY created_at DESC, user_id DESC
                LIMIT 100
                """;

        List<User> users = new ArrayList<>();

        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            String pattern = "%" + search
                    .replace("\\", "\\\\")
                    .replace("%", "\\%")
                    .replace("_", "\\_") + "%";

            ps.setString(1, pattern);
            ps.setString(2, pattern);

            try (ResultSet rs = ps.executeQuery()) {

                while (rs.next()) {

                    User user = new User();

                    user.setUserId(rs.getLong("user_id"));
                    user.setEmail(rs.getString("email"));
                    user.setFullName(rs.getString("full_name"));

                    user.setRole(UserRole.valueOf(
                            rs.getString("role")));

                    user.setSubscriptionStatus(
                            SubscriptionStatus.valueOf(
                                    rs.getString("subscription_status")));

                    Timestamp expires =
                            rs.getTimestamp("premium_expires_at");

                    if (expires != null) {
                        user.setPremiumExpiresAt(
                                expires.toLocalDateTime());
                    }

                    Timestamp created =
                            rs.getTimestamp("created_at");

                    if (created != null) {
                        user.setCreatedAt(
                                created.toLocalDateTime());
                    }

                    user.setAuthVersion(
                            rs.getLong("auth_version"));

                    users.add(user);
                }
            }
        }

        return users;
    }

    // ==========================================
    // 3. THAY ĐỔI QUYỀN USER / ADMIN
    // ==========================================

    public boolean updateUserRole(
            long actorId,
            long targetUserId,
            UserRole newRole) throws SQLException {

        if (newRole == null) {
            throw new IllegalArgumentException(
                    "Vai trò không hợp lệ.");
        }

        if (actorId == targetUserId) {
            throw new IllegalArgumentException(
                    "Không thể tự thay đổi quyền của mình.");
        }

        try (Connection conn = DatabaseConfig.getConnection()) {

            conn.setAutoCommit(false);

            try {
                // Khóa hàng quản trị theo thứ tự nhất quán.
                // Bảo vệ việc kiểm tra và cập nhật quyền.
                try (PreparedStatement lock =
                             conn.prepareStatement("""
                                     SELECT user_id
                                     FROM users
                                     WHERE role = 'ADMIN'
                                     ORDER BY user_id
                                     FOR UPDATE
                                     """)) {
                    try (ResultSet ignored = lock.executeQuery()) {
                        while (ignored.next()) {
                            // Giữ khóa cho đến khi commit.
                        }
                    }
                }

                String actorRole = null;

                try (PreparedStatement ps =
                             conn.prepareStatement("""
                                     SELECT role
                                     FROM users
                                     WHERE user_id = ?
                                     FOR UPDATE
                                     """)) {

                    ps.setLong(1, actorId);

                    try (ResultSet rs = ps.executeQuery()) {
                        if (rs.next()) {
                            actorRole = rs.getString("role");
                        }
                    }
                }

                if (!"ADMIN".equals(actorRole)) {
                    throw new SecurityException(
                            "Bạn không có quyền quản trị.");
                }

                String oldRole = null;

                try (PreparedStatement ps =
                             conn.prepareStatement("""
                                     SELECT role
                                     FROM users
                                     WHERE user_id = ?
                                     FOR UPDATE
                                     """)) {

                    ps.setLong(1, targetUserId);

                    try (ResultSet rs = ps.executeQuery()) {
                        if (rs.next()) {
                            oldRole = rs.getString("role");
                        }
                    }
                }

                if (oldRole == null) {
                    throw new IllegalArgumentException(
                            "Không tìm thấy tài khoản.");
                }

                if (oldRole.equals(newRole.name())) {
                    conn.commit();
                    return false;
                }

                if ("ADMIN".equals(oldRole)
                        && newRole == UserRole.USER) {

                    long adminCount;

                    try (PreparedStatement ps =
                                 conn.prepareStatement("""
                                         SELECT COUNT(*)
                                         FROM users
                                         WHERE role = 'ADMIN'
                                         """);
                         ResultSet rs = ps.executeQuery()) {

                        rs.next();
                        adminCount = rs.getLong(1);
                    }

                    if (adminCount <= 1) {
                        throw new IllegalArgumentException(
                                "Không thể hạ quyền Admin cuối cùng.");
                    }
                }

                int affected;

                try (PreparedStatement ps =
                             conn.prepareStatement("""
                                     UPDATE users
                                     SET role = ?,
                                         auth_version = auth_version + 1
                                     WHERE user_id = ?
                                     """)) {

                    ps.setString(1, newRole.name());
                    ps.setLong(2, targetUserId);

                    affected = ps.executeUpdate();
                }

                conn.commit();
                return affected == 1;

            } catch (SQLException | RuntimeException e) {
                conn.rollback();
                throw e;
            }
        }
    }
}
