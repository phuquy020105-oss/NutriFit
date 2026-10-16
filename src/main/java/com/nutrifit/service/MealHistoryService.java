package com.nutrifit.service;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.MealPlanDAO;
import com.nutrifit.dto.DaySummary;
import com.nutrifit.model.MealPlan;
import java.sql.Connection;
import java.sql.SQLException;
import java.time.LocalDate;
import java.util.List;

/** History is read-only by design. */
public class MealHistoryService {
    private final MealPlanDAO plans = new MealPlanDAO();
    private final MealPlannerService planner = new MealPlannerService();

    public List<MealPlan> listHistory(long userId, int limit) throws SQLException {
        if (userId <= 0) throw new SecurityException("Login required");
        if (limit < 1 || limit > 100) throw new IllegalArgumentException("History limit must be 1..100");
        try (Connection c = DatabaseConfig.getConnection()) {
            return plans.findHistory(c, userId, planner.today(), limit);
        }
    }

    public DaySummary getPastDay(long userId, LocalDate day) throws SQLException {
        return planner.getPastDay(userId, day);
    }
}
