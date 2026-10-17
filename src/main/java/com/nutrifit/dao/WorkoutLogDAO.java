package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.model.WorkoutLog;

import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Types;
import java.util.ArrayList;
import java.util.List;

public class WorkoutLogDAO {

    /** Trả về log_id vừa tạo. plan_detail_id có thể null (tập ngoài lộ trình). */
    public long insert(WorkoutLog log) throws SQLException {
        String sql = "INSERT INTO workoutlogs "
                   + "(user_id, workout_id, plan_detail_id, logged_date, duration_minutes, met_value, estimated_calories) "
                   + "VALUES (?, ?, ?, ?, ?, ?, ?)";
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            ps.setLong(1, log.getUserId());
            ps.setLong(2, log.getWorkoutId());
            if (log.getPlanDetailId() == null) {
                ps.setNull(3, Types.BIGINT);
            } else {
                ps.setLong(3, log.getPlanDetailId());
            }
            ps.setDate(4, Date.valueOf(log.getLoggedDate()));
            ps.setInt(5, log.getDurationMinutes());
            ps.setDouble(6, log.getMetValue());
            ps.setDouble(7, log.getEstimatedCalories());
            ps.executeUpdate();
            try (ResultSet keys = ps.getGeneratedKeys()) {
                if (keys.next()) {
                    return keys.getLong(1);
                }
                throw new SQLException("Không lấy được log_id vừa tạo");
            }
        }
    }

    /** Log mới nhất đứng đầu. */
    public List<WorkoutLog> findByUserId(long userId) throws SQLException {
        String sql = "SELECT log_id, user_id, workout_id, plan_detail_id, logged_date, "
                   + "duration_minutes, met_value, estimated_calories "
                   + "FROM workoutlogs WHERE user_id = ? ORDER BY logged_date DESC, log_id DESC";
        List<WorkoutLog> list = new ArrayList<>();
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, userId);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    WorkoutLog l = new WorkoutLog();
                    l.setLogId(rs.getLong("log_id"));
                    l.setUserId(rs.getLong("user_id"));
                    l.setWorkoutId(rs.getLong("workout_id"));
                    long detailId = rs.getLong("plan_detail_id");
                    l.setPlanDetailId(rs.wasNull() ? null : detailId);
                    l.setLoggedDate(rs.getDate("logged_date").toLocalDate());
                    l.setDurationMinutes(rs.getInt("duration_minutes"));
                    l.setMetValue(rs.getDouble("met_value"));
                    l.setEstimatedCalories(rs.getDouble("estimated_calories"));
                    list.add(l);
                }
            }
        }
        return list;
    }
}
