package com.nutrifit.dao;

import com.nutrifit.model.MealEntry;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/** All mutation methods must be invoked by services enforcing ownership/day restrictions. */
public class MealEntryDAO {
    private static final String COLUMNS = "e.entry_id,e.plan_id,e.recipe_id,e.recipe_name_snapshot,"
            + "e.meal_type,e.servings,e.calories_kcal,e.protein_g,e.carbs_g,e.fat_g,e.fiber_g,e.recorded_at";

    public List<MealEntry> findByPlan(Connection connection, long planId) throws SQLException {
        List<MealEntry> result = new ArrayList<>();
        String sql = "SELECT " + COLUMNS + " FROM mealentries e WHERE e.plan_id = ? "
                + "ORDER BY FIELD(e.meal_type, 'BREAKFAST','LUNCH','DINNER'),e.recorded_at,e.entry_id";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setLong(1, planId);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) result.add(mapRow(rs));
            }
        }
        return result;
    }

    public Optional<MealEntry> findByIdAndUser(Connection connection, long entryId, long userId)
            throws SQLException {
        String sql = "SELECT " + COLUMNS + " FROM mealentries e "
                + "JOIN mealplans p ON p.plan_id=e.plan_id "
                + "WHERE e.entry_id=? AND p.user_id=? FOR UPDATE";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setLong(1, entryId);
            ps.setLong(2, userId);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? Optional.of(mapRow(rs)) : Optional.empty();
            }
        }
    }

    public Optional<MealEntry> findByPlanMealRecipe(Connection connection, long planId,
            MealEntry.MealType type, long recipeId) throws SQLException {
        String sql = "SELECT " + COLUMNS + " FROM mealentries e "
                + "WHERE e.plan_id=? AND e.meal_type=? AND e.recipe_id=? FOR UPDATE";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setLong(1, planId);
            ps.setString(2, type.name());
            ps.setLong(3, recipeId);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? Optional.of(mapRow(rs)) : Optional.empty();
            }
        }
    }

    public long insert(Connection connection, MealEntry e) throws SQLException {
        String sql = "INSERT INTO mealentries(plan_id,recipe_id,recipe_name_snapshot,meal_type,servings,"
                + "calories_kcal,protein_g,carbs_g,fat_g,fiber_g) VALUES (?,?,?,?,?,?,?,?,?,?)";
        try (PreparedStatement ps = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            bindEntry(ps, e);
            if (ps.executeUpdate() != 1) throw new SQLException("Cannot insert meal entry");
            try (ResultSet keys = ps.getGeneratedKeys()) {
                if (keys.next()) return keys.getLong(1);
            }
            throw new SQLException("Inserted meal entry but no generated ID returned");
        }
    }

    public void update(Connection connection, MealEntry e) throws SQLException {
        String sql = "UPDATE mealentries SET recipe_id=?,recipe_name_snapshot=?,meal_type=?,"
                + "servings=?,calories_kcal=?,protein_g=?,carbs_g=?,fat_g=?,fiber_g=? "
                + "WHERE entry_id=? AND plan_id=?";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setLong(1, e.getRecipeId());
            ps.setString(2, e.getRecipeNameSnapshot());
            ps.setString(3, e.getMealType().name());
            ps.setBigDecimal(4, e.getServings());
            ps.setBigDecimal(5, e.getCaloriesKcal());
            ps.setBigDecimal(6, e.getProteinG());
            ps.setBigDecimal(7, e.getCarbsG());
            ps.setBigDecimal(8, e.getFatG());
            ps.setBigDecimal(9, e.getFiberG());
            ps.setLong(10, e.getEntryId());
            ps.setLong(11, e.getPlanId());
            if (ps.executeUpdate() != 1) throw new SQLException("Meal entry update failed");
        }
    }

    public void delete(Connection connection, long entryId, long planId) throws SQLException {
        try (PreparedStatement ps = connection.prepareStatement(
                "DELETE FROM mealentries WHERE entry_id=? AND plan_id=?")) {
            ps.setLong(1, entryId);
            ps.setLong(2, planId);
            if (ps.executeUpdate() != 1) throw new SQLException("Meal entry delete failed");
        }
    }

    private void bindEntry(PreparedStatement ps, MealEntry e) throws SQLException {
        ps.setLong(1, e.getPlanId());
        ps.setLong(2, e.getRecipeId());
        ps.setString(3, e.getRecipeNameSnapshot());
        ps.setString(4, e.getMealType().name());
        ps.setBigDecimal(5, e.getServings());
        ps.setBigDecimal(6, e.getCaloriesKcal());
        ps.setBigDecimal(7, e.getProteinG());
        ps.setBigDecimal(8, e.getCarbsG());
        ps.setBigDecimal(9, e.getFatG());
        ps.setBigDecimal(10, e.getFiberG());
    }

    private MealEntry mapRow(ResultSet rs) throws SQLException {
        return new MealEntry(rs.getLong("entry_id"), rs.getLong("plan_id"),
                rs.getLong("recipe_id"), rs.getString("recipe_name_snapshot"),
                MealEntry.MealType.valueOf(rs.getString("meal_type")),
                rs.getBigDecimal("servings"), rs.getBigDecimal("calories_kcal"),
                rs.getBigDecimal("protein_g"), rs.getBigDecimal("carbs_g"),
                rs.getBigDecimal("fat_g"), rs.getBigDecimal("fiber_g"),
                rs.getTimestamp("recorded_at").toLocalDateTime());
    }
}
