package com.nutrifit.dao;
import com.nutrifit.config.DatabaseConfig;
import java.sql.*;
import java.util.*;

/** Independent aggregates avoid multiplying water/workout rows through a many-to-many join. */
public final class DashboardReadDAO {
    public Map<String,Object> find(long userId)throws SQLException {
        try(Connection c=DatabaseConfig.getConnection()){return find(c,userId);}
    }
    public Map<String,Object> find(Connection c,long userId)throws SQLException {
        String sql="""
            SELECT p.target_kcal,p.target_water_ml,p.weight_kg,p.height_cm,
                   water.total AS water_today,w.sessions,w.minutes,w.calories,
                   metric.weight_kg AS latest_weight,metric.recorded_date
            FROM (SELECT 1) anchor
            LEFT JOIN userprofiles p ON p.user_id=?
            LEFT JOIN (SELECT COALESCE(SUM(amount_ml),0) AS total FROM waterintakelog
                       WHERE user_id=? AND logged_date=CURRENT_DATE()) water ON TRUE
            LEFT JOIN (SELECT COUNT(*) AS sessions,COALESCE(SUM(duration_minutes),0) AS minutes,
                              COALESCE(SUM(estimated_calories),0) AS calories FROM workoutlogs
                       WHERE user_id=? AND logged_date=CURRENT_DATE()) w ON TRUE
            LEFT JOIN (SELECT weight_kg,recorded_date FROM bodymetriclog WHERE user_id=?
                       ORDER BY recorded_date DESC,metric_id DESC LIMIT 1) metric ON TRUE
            """;
        try(PreparedStatement s=c.prepareStatement(sql)) {
            for(int i=1;i<=4;i++)s.setLong(i,userId);
            try(ResultSet row=s.executeQuery()) {
                if(!row.next())throw new SQLException("Missing dashboard aggregate");
                Map<String,Object> data=new LinkedHashMap<>();
                data.put("targetCalories",row.getObject("target_kcal"));data.put("targetWater",row.getObject("target_water_ml"));
                data.put("profileWeight",row.getObject("weight_kg"));data.put("height",row.getObject("height_cm"));
                data.put("waterToday",row.getLong("water_today"));data.put("workoutSessions",row.getLong("sessions"));
                data.put("workoutMinutes",row.getLong("minutes"));data.put("workoutCalories",row.getBigDecimal("calories"));
                data.put("latestWeight",row.getBigDecimal("latest_weight"));data.put("weightDate",row.getDate("recorded_date"));
                return data;
            }
        }
    }
}
