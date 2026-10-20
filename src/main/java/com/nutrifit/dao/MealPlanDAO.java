package com.nutrifit.dao;

import com.nutrifit.model.MealPlan;
import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/** Persistence only. The caller owns the Connection and its transaction. */
public class MealPlanDAO {
    private static final String COLUMNS = "plan_id, user_id, plan_date, created_at";

    public Optional<MealPlan> findByUserAndDate(Connection connection, long userId, LocalDate date)
            throws SQLException {
        String sql = "SELECT " + COLUMNS + " FROM mealplans WHERE user_id = ? AND plan_date = ?";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setLong(1, userId);
            ps.setDate(2, Date.valueOf(date));
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? Optional.of(mapRow(rs)) : Optional.empty();
            }
        }
    }

    public long insert(Connection connection, long userId, LocalDate date) throws SQLException {
        try (PreparedStatement ps = connection.prepareStatement(
                "INSERT INTO mealplans(user_id, plan_date) VALUES(?, ?)",
                Statement.RETURN_GENERATED_KEYS)) {
            ps.setLong(1, userId);
            ps.setDate(2, Date.valueOf(date));
            if (ps.executeUpdate() != 1) throw new SQLException("Cannot insert meal plan");
            try (ResultSet keys = ps.getGeneratedKeys()) {
                if (keys.next()) return keys.getLong(1);
            }
            throw new SQLException("Inserted meal plan but no generated ID returned");
        }
    }

    /**
     * Atomically obtains the daily plan ID. Locking its parent row serializes
     * concurrent writes for one user/day and prevents duplicate meal entries.
     * Must run inside a transaction (autoCommit=false).
     */
    public long findOrCreateForUpdate(Connection connection, long userId, LocalDate date)
            throws SQLException {
        String upsert = "INSERT INTO mealplans(user_id,plan_date) VALUES(?,?) "
                + "ON DUPLICATE KEY UPDATE plan_id = LAST_INSERT_ID(plan_id)";
        try (PreparedStatement ps = connection.prepareStatement(upsert)) {
            ps.setLong(1, userId);
            ps.setDate(2, Date.valueOf(date));
            ps.executeUpdate();
        }
        try (PreparedStatement ps = connection.prepareStatement(
                "SELECT plan_id FROM mealplans WHERE user_id = ? AND plan_date = ? FOR UPDATE")) {
            ps.setLong(1, userId);
            ps.setDate(2, Date.valueOf(date));
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) return rs.getLong(1);
            }
        }
        throw new SQLException("Cannot find or create meal plan");
    }

    public List<MealPlan> findHistory(Connection connection, long userId, LocalDate before, int limit)
            throws SQLException {
        List<MealPlan> result = new ArrayList<>();
        String sql = "SELECT p.plan_id, p.user_id, p.plan_date, p.created_at FROM mealplans p "
                + "WHERE p.user_id = ? AND p.plan_date < ? "
                + "AND EXISTS (SELECT 1 FROM mealentries e WHERE e.plan_id = p.plan_id) "
                + "ORDER BY p.plan_date DESC LIMIT ?";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setLong(1, userId);
            ps.setDate(2, Date.valueOf(before));
            ps.setInt(3, limit);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) result.add(mapRow(rs));
            }
        }
        return result;
    }

    private MealPlan mapRow(ResultSet rs) throws SQLException {
        return new MealPlan(rs.getLong("plan_id"), rs.getLong("user_id"),
                rs.getDate("plan_date").toLocalDate(),
                rs.getTimestamp("created_at").toLocalDateTime());
    }
}
