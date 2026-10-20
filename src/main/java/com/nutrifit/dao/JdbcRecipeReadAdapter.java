package com.nutrifit.dao;

import com.nutrifit.dto.IngredientNutritionLine;
import com.nutrifit.dto.NutritionFacts;
import com.nutrifit.dto.RecipeCandidate;
import com.nutrifit.dto.RecipeNutritionInput;
import com.nutrifit.model.MealEntry;
import com.nutrifit.service.NutritionCalculator;
import com.nutrifit.service.RecipeReadPort;
import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

/** Temporary read-only adapter to shared recipes/recipeingredients/foods tables. */
public class JdbcRecipeReadAdapter implements RecipeReadPort {
    private static final String SELECT = "SELECT r.recipe_id,r.name,r.meal_type,r.base_servings,r.image_url,"
            + "i.food_id,i.quantity_grams,f.active AS food_active,"
            + "f.calories_per_100g,f.protein_per_100g,f.carbs_per_100g,"
            + "f.fat_per_100g,f.fiber_per_100g "
            + "FROM recipes r LEFT JOIN recipeingredients i ON i.recipe_id=r.recipe_id "
            + "LEFT JOIN foods f ON f.food_id=i.food_id ";

    @Override
    public Optional<RecipeNutritionInput> findNutritionInput(Connection connection, long recipeId)
            throws SQLException {
        String sql = SELECT + "WHERE r.recipe_id=? AND r.active=TRUE ORDER BY i.ingredient_id";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setLong(1, recipeId);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) return Optional.empty();
                RecipeRows recipe = new RecipeRows(rs);
                do {
                    recipe.append(rs);
                } while (rs.next());
                return recipe.input();
            }
        }
    }

    @Override
    public Map<Long, RecipeNutritionInput> findNutritionInputs(Connection connection, java.util.Collection<Long> recipeIds)
            throws SQLException {
        List<Long> ids = recipeIds.stream().distinct().toList();
        if (ids.isEmpty()) return Map.of();
        if (ids.size() > 60 || ids.stream().anyMatch(id -> id == null || id <= 0))
            throw new IllegalArgumentException("Invalid recipe batch");
        Map<Long, RecipeRows> grouped = new LinkedHashMap<>();
        String marks = String.join(",", java.util.Collections.nCopies(ids.size(), "?"));
        try (PreparedStatement ps = connection.prepareStatement(SELECT + "WHERE r.active=TRUE AND r.recipe_id IN ("
                + marks + ") ORDER BY r.recipe_id,i.ingredient_id")) {
            for (int i=0; i<ids.size(); i++) ps.setLong(i+1, ids.get(i));
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    long id = rs.getLong("recipe_id");
                    RecipeRows row = grouped.get(id);
                    if (row == null) { row = new RecipeRows(rs); grouped.put(id,row); }
                    row.append(rs);
                }
            }
        }
        Map<Long,RecipeNutritionInput> result = new LinkedHashMap<>();
        for (var entry : grouped.entrySet()) entry.getValue().input().ifPresent(input -> result.put(entry.getKey(),input));
        return result;
    }

    @Override
    public List<RecipeCandidate> listCandidates(Connection connection) throws SQLException {
        List<RecipeCandidate> result = new ArrayList<>();
        Map<Long, RecipeRows> grouped = new LinkedHashMap<>();
        // Read every active candidate and its ingredients in one query; no silent catalog cutoff.
        try (PreparedStatement ps = connection.prepareStatement(
                SELECT + "WHERE r.active=TRUE ORDER BY r.recipe_id,i.ingredient_id")) {
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    long id = rs.getLong("recipe_id");
                    RecipeRows recipe = grouped.get(id);
                    if (recipe == null) {
                        recipe = new RecipeRows(rs);
                        grouped.put(id, recipe);
                    }
                    recipe.append(rs);
                }
            }
        }
        NutritionCalculator calculator = new NutritionCalculator();
        for (RecipeRows rows : grouped.values()) {
            Optional<RecipeNutritionInput> input = rows.input();
            if (input.isEmpty()) continue;
            RecipeNutritionInput recipe = input.get();
            Set<Long> foodIds = new HashSet<>();
            for (IngredientNutritionLine line : recipe.ingredients()) foodIds.add(line.foodId());
            try {
                result.add(new RecipeCandidate(recipe.recipeId(), recipe.name(), recipe.mealType(), foodIds,
                        calculator.calculate(recipe, BigDecimal.ONE),recipe.imageUrl()));
            } catch (IllegalArgumentException e) {
                // A non-storable per-serving value must not make all other recipes unavailable.
            }
        }
        return result;
    }

    private static final class RecipeRows {
        private final long id;
        private final String name;
        private final String imageUrl;
        private final BigDecimal base;
        private final List<IngredientNutritionLine> ingredients = new ArrayList<>();
        private MealEntry.MealType type;
        private boolean valid;

        private RecipeRows(ResultSet rs) throws SQLException {
            id = rs.getLong("recipe_id");
            name = rs.getString("name");
            imageUrl = rs.getString("image_url");
            base = rs.getBigDecimal("base_servings");
            String mealType = rs.getString("meal_type");
            valid = id > 0 && name != null && !name.isBlank() && base != null && base.signum() > 0;
            if (mealType == null) valid = false;
            else {
                try {
                    type = MealEntry.MealType.valueOf(mealType);
                } catch (IllegalArgumentException e) {
                    valid = false;
                }
            }
        }

        private void append(ResultSet rs) throws SQLException {
            if (!valid) return;
            long foodId = rs.getLong("food_id");
            if (rs.wasNull() || foodId <= 0 || !rs.getBoolean("food_active")) {
                valid = false;
                return;
            }
            BigDecimal grams = rs.getBigDecimal("quantity_grams");
            BigDecimal kcal = rs.getBigDecimal("calories_per_100g");
            BigDecimal protein = rs.getBigDecimal("protein_per_100g");
            BigDecimal carbs = rs.getBigDecimal("carbs_per_100g");
            BigDecimal fat = rs.getBigDecimal("fat_per_100g");
            BigDecimal fiber = rs.getBigDecimal("fiber_per_100g");
            if (grams == null || kcal == null || protein == null || carbs == null || fat == null || fiber == null) {
                valid = false;
                return;
            }
            try {
                ingredients.add(new IngredientNutritionLine(foodId, grams,
                        new NutritionFacts(kcal, protein, carbs, fat, fiber)));
            } catch (IllegalArgumentException e) {
                valid = false;
            }
        }

        private Optional<RecipeNutritionInput> input() {
            return valid && !ingredients.isEmpty()
                    ? Optional.of(new RecipeNutritionInput(id, name, type, base, ingredients,imageUrl)) : Optional.empty();
        }
    }
}
