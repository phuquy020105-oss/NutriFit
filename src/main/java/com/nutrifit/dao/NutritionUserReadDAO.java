package com.nutrifit.dao;

import java.math.BigDecimal;
import com.nutrifit.dto.NutritionGoal;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.Optional;

/** Read-only bridge to Profile/Payment data until their shared services are integrated. */
public class NutritionUserReadDAO {
    /** Same active-subscription rule as PremiumAccessService; missing expiry grants no access. */
    public boolean hasPremiumAccess(Connection connection, long userId, LocalDateTime now)
            throws SQLException {
        String sql = "SELECT subscription_status,premium_expires_at FROM users WHERE user_id=?";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setLong(1, userId);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next() || !"PREMIUM".equals(rs.getString("subscription_status"))) return false;
                Timestamp expiry = rs.getTimestamp("premium_expires_at");
                return expiry != null && expiry.toLocalDateTime().isAfter(now);
            }
        }
    }

    public NutritionGoal findGoal(Connection connection, long userId) throws SQLException {
        try (PreparedStatement ps=connection.prepareStatement("SELECT goal FROM userprofiles WHERE user_id=?")) {
            ps.setLong(1,userId);
            try (ResultSet rs=ps.executeQuery()) {
                return NutritionGoal.fromProfile(rs.next()?rs.getString(1):null);
            }
        }
    }

    public Optional<BigDecimal> findTargetKcal(Connection connection, long userId) throws SQLException {
        try (PreparedStatement ps = connection.prepareStatement(
                "SELECT target_kcal FROM userprofiles WHERE user_id=?")) {
            ps.setLong(1, userId);
            try (ResultSet rs = ps.executeQuery()) {
                BigDecimal target = rs.next() ? rs.getBigDecimal(1) : null;
                return target != null && target.signum() > 0 ? Optional.of(target) : Optional.empty();
            }
        }
    }
}
