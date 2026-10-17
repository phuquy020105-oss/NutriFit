package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.model.WorkoutPlanDay;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

public class WorkoutPlanDayDAO {

    /** Trả về các ngày của lộ trình, sắp theo day_index (1..7). */
    public List<WorkoutPlanDay> findByPlanId(long planId) throws SQLException {
        String sql = "SELECT plan_day_id, plan_id, day_index, day_name, focus_area, rest_day "
                   + "FROM workoutplandays WHERE plan_id = ? ORDER BY day_index";
        List<WorkoutPlanDay> list = new ArrayList<>();
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, planId);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    WorkoutPlanDay d = mapRow(rs);
                    list.add(d);
                }
            }
        }
        return list;
    }

    public long insert(WorkoutPlanDay day) throws SQLException {
        try (Connection conn = DatabaseConfig.getConnection()) {
            return insert(conn, day);
        }
    }

    /** Dùng chung kết nối để nằm trong transaction của Service. */
    public long insert(Connection conn, WorkoutPlanDay day) throws SQLException {
        String sql = "INSERT INTO workoutplandays (plan_id, day_index, day_name, focus_area, rest_day) "
                   + "VALUES (?, ?, ?, ?, ?)";
        try (PreparedStatement ps = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            ps.setLong(1, day.getPlanId());
            ps.setInt(2, day.getDayIndex());
            ps.setString(3, day.getDayName());
            ps.setString(4, day.getFocusArea());
            ps.setBoolean(5, day.isRestDay());
            ps.executeUpdate();
            try (ResultSet keys = ps.getGeneratedKeys()) {
                if (keys.next()) {
                    return keys.getLong(1);
                }
                throw new SQLException("Không lấy được plan_day_id vừa tạo");
            }
        }
    }

    /** Trả về null nếu không tìm thấy. */
    public WorkoutPlanDay findById(long planDayId) throws SQLException {
        String sql = "SELECT plan_day_id, plan_id, day_index, day_name, focus_area, rest_day "
                   + "FROM workoutplandays WHERE plan_day_id = ?";
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, planDayId);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? mapRow(rs) : null;
            }
        }
    }

    private WorkoutPlanDay mapRow(ResultSet rs) throws SQLException {
        WorkoutPlanDay d = new WorkoutPlanDay();
        d.setPlanDayId(rs.getLong("plan_day_id"));
        d.setPlanId(rs.getLong("plan_id"));
        d.setDayIndex(rs.getInt("day_index"));
        d.setDayName(rs.getString("day_name"));
        d.setFocusArea(rs.getString("focus_area"));
        d.setRestDay(rs.getBoolean("rest_day"));
        return d;
    }
}
