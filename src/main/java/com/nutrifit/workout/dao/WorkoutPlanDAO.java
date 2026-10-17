package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.model.WorkoutPlan;

import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

public class WorkoutPlanDAO {

    private static final String SELECT =
        "SELECT plan_id, user_id, plan_name, start_date, end_date, active FROM workoutplans ";

    /** Tự mở kết nối riêng. Trả về plan_id vừa tạo. */
    public long insert(WorkoutPlan plan) throws SQLException {
        try (Connection conn = DatabaseConfig.getConnection()) {
            return insert(conn, plan);
        }
    }

    /** Dùng chung kết nối để Service gom nhiều bảng vào 1 transaction. */
    public long insert(Connection conn, WorkoutPlan plan) throws SQLException {
        String sql = "INSERT INTO workoutplans (user_id, plan_name, start_date, end_date, active) "
                   + "VALUES (?, ?, ?, ?, ?)";
        try (PreparedStatement ps = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            ps.setLong(1, plan.getUserId());
            ps.setString(2, plan.getPlanName());
            ps.setDate(3, Date.valueOf(plan.getStartDate()));
            ps.setDate(4, Date.valueOf(plan.getEndDate()));
            ps.setBoolean(5, plan.isActive());
            ps.executeUpdate();
            try (ResultSet keys = ps.getGeneratedKeys()) {
                if (keys.next()) {
                    return keys.getLong(1);
                }
                throw new SQLException("Không lấy được plan_id vừa tạo");
            }
        }
    }

    /** Lộ trình mới nhất đứng đầu. */
    public List<WorkoutPlan> findByUserId(long userId) throws SQLException {
        String sql = SELECT + "WHERE user_id = ? ORDER BY plan_id DESC";
        List<WorkoutPlan> list = new ArrayList<>();
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, userId);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    list.add(mapRow(rs));
                }
            }
        }
        return list;
    }

    /** Trả về null nếu không tìm thấy. */
    public WorkoutPlan findById(long id) throws SQLException {
        String sql = SELECT + "WHERE plan_id = ?";
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, id);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? mapRow(rs) : null;
            }
        }
    }

    private WorkoutPlan mapRow(ResultSet rs) throws SQLException {
        WorkoutPlan p = new WorkoutPlan();
        p.setPlanId(rs.getLong("plan_id"));
        p.setUserId(rs.getLong("user_id"));
        p.setPlanName(rs.getString("plan_name"));
        p.setStartDate(rs.getDate("start_date").toLocalDate());
        p.setEndDate(rs.getDate("end_date").toLocalDate());
        p.setActive(rs.getBoolean("active"));
        return p;
    }
}
