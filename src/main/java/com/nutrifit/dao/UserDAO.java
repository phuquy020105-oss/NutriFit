
package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.model.User;
import com.nutrifit.model.UserRole;
import com.nutrifit.model.SubscriptionStatus;

import java.sql.*;
import java.util.Optional;

public class UserDAO {

    public Optional<User> findByEmail(String email)
            throws SQLException {

        String sql = """
            SELECT user_id, email, password_hash,
                   full_name, role, subscription_status,
                   premium_expires_at, created_at
            FROM users
            WHERE email = ?
            """;

        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            ps.setString(1, email);

            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    return Optional.of(mapUser(rs));
                }
            }
        }

        return Optional.empty();
    }

    public Optional<User> findById(Long userId)
            throws SQLException {

        String sql = """
            SELECT user_id, email, password_hash,
                   full_name, role, subscription_status,
                   premium_expires_at, created_at
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

    public Long create(User user) throws SQLException {

        String sql = """
            INSERT INTO users
                (email, password_hash, full_name)
            VALUES (?, ?, ?)
            """;

        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(
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

        Timestamp createdAt = rs.getTimestamp("created_at");

        if (createdAt != null) {
            user.setCreatedAt(
                    createdAt.toLocalDateTime());
        }

        return user;
    }
}
