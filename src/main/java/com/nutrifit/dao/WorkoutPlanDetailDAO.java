package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.model.WorkoutPlanDetail;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

public class WorkoutPlanDetailDAO {

    /** Các bài tập trong một ngày, sắp theo order_index. */
    public List<WorkoutPlanDetail> findByDayId(long planDayId) throws SQLException {
        String sql = "SELECT detail_id, plan_day_id, workout_id, duration_minutes, order_index "
                   + "FROM workoutplandetails WHERE plan_day_id = ? ORDER BY order_index";
        List<WorkoutPlanDetail> list = new ArrayList<>();
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, planDayId);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    WorkoutPlanDetail d = mapRow(rs);
                    list.add(d);
                }
            }
        }
        return list;
    }

    public long insert(WorkoutPlanDetail detail) throws SQLException {
        try (Connection conn = DatabaseConfig.getConnection()) {
            return insert(conn, detail);
        }
    }

    /** Dùng chung kết nối để nằm trong transaction của Service. */
    public long insert(Connection conn, WorkoutPlanDetail detail) throws SQLException {
        String sql = "INSERT INTO workoutplandetails (plan_day_id, workout_id, duration_minutes, order_index) "
                   + "VALUES (?, ?, ?, ?)";
        try (PreparedStatement ps = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            ps.setLong(1, detail.getPlanDayId());
            ps.setLong(2, detail.getWorkoutId());
            ps.setInt(3, detail.getDurationMinutes());
            ps.setInt(4, detail.getOrderIndex());
            ps.executeUpdate();
            try (ResultSet keys = ps.getGeneratedKeys()) {
                if (keys.next()) {
                    return keys.getLong(1);
                }
                throw new SQLException("Không lấy được detail_id vừa tạo");
            }
        }
    }

    public void updateDuration(long detailId, int minutes) throws SQLException {
        String sql = "UPDATE workoutplandetails SET duration_minutes = ? WHERE detail_id = ?";
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setInt(1, minutes);
            ps.setLong(2, detailId);
            ps.executeUpdate();
        }
    }

    public void deleteById(long detailId) throws SQLException {
        String sql = "DELETE FROM workoutplandetails WHERE detail_id = ?";
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, detailId);
            ps.executeUpdate();
        }
    }

    /** Trả về null nếu không tìm thấy. */
    public WorkoutPlanDetail findById(long detailId) throws SQLException {
        String sql = "SELECT detail_id, plan_day_id, workout_id, duration_minutes, order_index "
                   + "FROM workoutplandetails WHERE detail_id = ?";
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, detailId);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? mapRow(rs) : null;
            }
        }
    }

    private WorkoutPlanDetail mapRow(ResultSet rs) throws SQLException {
        WorkoutPlanDetail d = new WorkoutPlanDetail();
        d.setDetailId(rs.getLong("detail_id"));
        d.setPlanDayId(rs.getLong("plan_day_id"));
        d.setWorkoutId(rs.getLong("workout_id"));
        d.setDurationMinutes(rs.getInt("duration_minutes"));
        d.setOrderIndex(rs.getInt("order_index"));
        return d;
    }
}
