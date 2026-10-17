package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.model.WorkoutCategory;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class WorkoutCategoryDAO {

    private static final String SQL_FIND_ALL =
        "SELECT category_id, category_name, icon_name "
        + "FROM workoutcategories ORDER BY category_name";

    public List<WorkoutCategory> findAll() throws SQLException {
        List<WorkoutCategory> list = new ArrayList<>();
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement ps = conn.prepareStatement(SQL_FIND_ALL);
             ResultSet rs = ps.executeQuery()) {
            while (rs.next()) {
                list.add(mapRow(rs));
            }
        }
        return list;
    }

    private WorkoutCategory mapRow(ResultSet rs) throws SQLException {
        WorkoutCategory c = new WorkoutCategory();
        c.setCategoryId(rs.getLong("category_id"));
        c.setCategoryName(rs.getString("category_name"));
        c.setIconName(rs.getString("icon_name"));
        return c;
    }
}
