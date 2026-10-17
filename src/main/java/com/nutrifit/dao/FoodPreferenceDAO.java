package com.nutrifit.dao;

import com.nutrifit.model.FoodPreference;
import com.nutrifit.dto.FoodPreferenceView;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class FoodPreferenceDAO {
    public List<FoodPreferenceView> findViewsByUser(Connection connection, long userId) throws SQLException {
        List<FoodPreferenceView> result = new ArrayList<>();
        String sql = "SELECT p.food_id,f.name,f.active,p.type,p.updated_at FROM foodpreferences p "
                + "JOIN foods f ON f.food_id=p.food_id WHERE p.user_id=? "
                + "ORDER BY p.updated_at DESC,p.preference_id DESC";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setLong(1, userId);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) result.add(new FoodPreferenceView(rs.getLong("food_id"),
                        rs.getString("name"), FoodPreference.PreferenceType.valueOf(rs.getString("type")),
                        rs.getTimestamp("updated_at").toLocalDateTime(), rs.getBoolean("active")));
            }
        }
        return result;
    }

    public List<FoodPreference> findByUser(Connection connection, long userId) throws SQLException {
        List<FoodPreference> result = new ArrayList<>();
        String sql = "SELECT preference_id,user_id,food_id,type,updated_at "
                + "FROM foodpreferences WHERE user_id=? ORDER BY updated_at DESC,preference_id DESC";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setLong(1, userId);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) result.add(new FoodPreference(
                        rs.getLong("preference_id"), rs.getLong("user_id"), rs.getLong("food_id"),
                        FoodPreference.PreferenceType.valueOf(rs.getString("type")),
                        rs.getTimestamp("updated_at").toLocalDateTime()));
            }
        }
        return result;
    }

    public void upsert(Connection connection, long userId, long foodId,
            FoodPreference.PreferenceType type) throws SQLException {
        String sql = "INSERT INTO foodpreferences(user_id,food_id,type) VALUES(?,?,?) "
                + "ON DUPLICATE KEY UPDATE type=VALUES(type)";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setLong(1, userId);
            ps.setLong(2, foodId);
            ps.setString(3, type.name());
            ps.executeUpdate();
        }
    }

    public void delete(Connection connection, long userId, long foodId) throws SQLException {
        try (PreparedStatement ps = connection.prepareStatement(
                "DELETE FROM foodpreferences WHERE user_id=? AND food_id=?")) {
            ps.setLong(1, userId);
            ps.setLong(2, foodId);
            ps.executeUpdate();
        }
    }

    public boolean isActiveFood(Connection connection, long foodId) throws SQLException {
        try (PreparedStatement ps = connection.prepareStatement(
                "SELECT 1 FROM foods WHERE food_id=? AND active=TRUE")) {
            ps.setLong(1, foodId);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next();
            }
        }
    }
}
