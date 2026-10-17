package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.model.Workout;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class WorkoutDAO {

    private static final String SELECT_ALL_COLUMNS =
        "SELECT workout_id, category_id, created_by, workout_name, is_custom, "
        + "access_level, description, instructions, muscle_group, difficulty_level, "
        + "equipment, target_goal, video_url, met_value, default_duration_minutes "
        + "FROM workouts ";

    /** Trả về null nếu không tìm thấy. */
    public Workout findById(long id) throws SQLException {
        String sql = SELECT_ALL_COLUMNS + "WHERE workout_id = ?";
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, id);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? mapRow(rs) : null;
            }
        }
    }

    /** level: "FREE" hoặc "PREMIUM". */
    public List<Workout> findByAccessLevel(String level) throws SQLException {
        String sql = SELECT_ALL_COLUMNS + "WHERE access_level = ? ORDER BY workout_name";
        List<Workout> list = new ArrayList<>();
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, level);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    list.add(mapRow(rs));
                }
            }
        }
        return list;
    }

    public List<Workout> findAll() throws SQLException {
        String sql = SELECT_ALL_COLUMNS + "ORDER BY workout_name";
        List<Workout> list = new ArrayList<>();
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {
            while (rs.next()) {
                list.add(mapRow(rs));
            }
        }
        return list;
    }

    private Workout mapRow(ResultSet rs) throws SQLException {
        Workout w = new Workout();
        w.setWorkoutId(rs.getLong("workout_id"));
        w.setCategoryId(rs.getLong("category_id"));
        long createdBy = rs.getLong("created_by");
        w.setCreatedBy(rs.wasNull() ? null : createdBy);   // cột cho phép NULL
        w.setWorkoutName(rs.getString("workout_name"));
        w.setCustom(rs.getBoolean("is_custom"));
        w.setAccessLevel(rs.getString("access_level"));
        w.setDescription(rs.getString("description"));
        w.setInstructions(rs.getString("instructions"));
        w.setMuscleGroup(rs.getString("muscle_group"));
        w.setDifficultyLevel(rs.getString("difficulty_level"));
        w.setEquipment(rs.getString("equipment"));
        w.setTargetGoal(rs.getString("target_goal"));
        w.setVideoUrl(rs.getString("video_url"));
        w.setMetValue(rs.getDouble("met_value"));
        w.setDefaultDurationMinutes(rs.getInt("default_duration_minutes"));
        return w;
    }
}
