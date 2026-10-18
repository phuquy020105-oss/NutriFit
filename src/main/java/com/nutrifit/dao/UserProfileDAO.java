package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;
import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class UserProfileDAO {
    public boolean isComplete(long userId) throws SQLException {
        String sql = """
            SELECT 1 FROM userprofiles WHERE user_id=?
              AND gender IN ('male','female') AND age BETWEEN 13 AND 100
              AND height_cm > 0 AND weight_kg > 0
              AND activity_level IS NOT NULL AND goal IS NOT NULL
              AND bmr > 0 AND tdee > 0 AND target_kcal > 0
              AND target_water_ml > 0 LIMIT 1
            """;
        try (Connection c = DatabaseConfig.getConnection();
             PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setLong(1, userId);
            try (ResultSet rs = ps.executeQuery()) { return rs.next(); }
        }
    }

    public void save(long userId, String gender, int age, BigDecimal height,
                     BigDecimal weight, String activity, String goal,
                     BigDecimal bmr, BigDecimal tdee, BigDecimal targetKcal,
                     int waterMl) throws SQLException {
        String sql = """
            INSERT INTO userprofiles (user_id,gender,age,height_cm,weight_kg,
              activity_level,goal,bmr,tdee,target_kcal,target_water_ml)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ON DUPLICATE KEY UPDATE gender=VALUES(gender),age=VALUES(age),
              height_cm=VALUES(height_cm),weight_kg=VALUES(weight_kg),
              activity_level=VALUES(activity_level),goal=VALUES(goal),
              bmr=VALUES(bmr),tdee=VALUES(tdee),
              target_kcal=VALUES(target_kcal),target_water_ml=VALUES(target_water_ml)
            """;
        try (Connection c = DatabaseConfig.getConnection();
             PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setLong(1,userId); ps.setString(2,gender); ps.setInt(3,age);
            ps.setBigDecimal(4,height); ps.setBigDecimal(5,weight);
            ps.setString(6,activity); ps.setString(7,goal);
            ps.setBigDecimal(8,bmr); ps.setBigDecimal(9,tdee);
            ps.setBigDecimal(10,targetKcal); ps.setInt(11,waterMl);
            ps.executeUpdate();
        }
    }

    public java.util.Map<String, String> findBodyProfile(long userId) throws SQLException {
        String sql = """
            SELECT gender, age, height_cm, weight_kg, activity_level, goal,
                   bmr, tdee, target_kcal, target_water_ml
            FROM userprofiles WHERE user_id = ?
            """;
        try (Connection c = DatabaseConfig.getConnection();
             PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setLong(1, userId);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) return java.util.Collections.emptyMap();
                java.util.Map<String, String> data = new java.util.HashMap<>();
                for (String col : new String[]{"gender", "age", "height_cm", "weight_kg",
                        "activity_level", "goal", "bmr", "tdee", "target_kcal", "target_water_ml"}) {
                    String value = rs.getString(col);
                    data.put(col, value == null ? "" : value);
                }
                return data;
            }
        }
    }
}
