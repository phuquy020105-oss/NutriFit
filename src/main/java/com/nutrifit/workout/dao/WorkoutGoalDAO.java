package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.model.WorkoutGoal;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class WorkoutGoalDAO {

    /** Mỗi user chỉ có 1 mục tiêu (user_id UNIQUE). Trả về null nếu chưa đặt. */
    public WorkoutGoal findByUserId(long userId) throws SQLException {
        String sql = "SELECT goal_id, user_id, weekly_sessions_target, weekly_duration_target "
                   + "FROM workoutgoals WHERE user_id = ?";
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, userId);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) {
                    return null;
                }
                WorkoutGoal g = new WorkoutGoal();
                g.setGoalId(rs.getLong("goal_id"));
                g.setUserId(rs.getLong("user_id"));
                g.setWeeklySessionsTarget(rs.getInt("weekly_sessions_target"));
                g.setWeeklyDurationTarget(rs.getInt("weekly_duration_target"));
                return g;
            }
        }
    }

    /** Thêm mới hoặc cập nhật nếu user đã có mục tiêu. */
    public void save(WorkoutGoal goal) throws SQLException {
        String sql = "INSERT INTO workoutgoals (user_id, weekly_sessions_target, weekly_duration_target) "
                   + "VALUES (?, ?, ?) "
                   + "ON DUPLICATE KEY UPDATE "
                   + "weekly_sessions_target = VALUES(weekly_sessions_target), "
                   + "weekly_duration_target = VALUES(weekly_duration_target)";
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, goal.getUserId());
            ps.setInt(2, goal.getWeeklySessionsTarget());
            ps.setInt(3, goal.getWeeklyDurationTarget());
            ps.executeUpdate();
        }
    }
}
