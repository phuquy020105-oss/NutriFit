package com.nutrifit.dao;

import com.nutrifit.dto.IngredientNutritionLine;
import com.nutrifit.dto.NutritionFacts;
import com.nutrifit.dto.RecipeCandidate;
import com.nutrifit.dto.RecipeNutritionInput;
import com.nutrifit.model.MealEntry;
import com.nutrifit.service.NutritionCalculator;
import com.nutrifit.service.RecipeReadPort;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;

/** Temporary read-only adapter to shared recipes/recipeingredients/foods tables. */
public class JdbcRecipeReadAdapter implements RecipeReadPort {
    @Override
    public Optional<RecipeNutritionInput> findNutritionInput(Connection connection, long recipeId)
            throws SQLException {
        String sql = "SELECT r.recipe_id,r.name,r.meal_type,r.base_servings,"
                + "i.food_id,i.quantity_grams,f.active AS food_active,"
                + "f.calories_per_100g,f.protein_per_100g,f.carbs_per_100g,"
                + "f.fat_per_100g,f.fiber_per_100g "
                + "FROM recipes r LEFT JOIN recipeingredients i ON i.recipe_id=r.recipe_id "
                + "LEFT JOIN foods f ON f.food_id=i.food_id "
                + "WHERE r.recipe_id=? AND r.active=TRUE ORDER BY i.ingredient_id";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setLong(1, recipeId);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) return Optional.empty();
                String name = rs.getString("name");
                MealEntry.MealType mealType = MealEntry.MealType.valueOf(rs.getString("meal_type"));
                java.math.BigDecimal base = rs.getBigDecimal("base_servings");
                List<IngredientNutritionLine> ingredients = new ArrayList<>();
                do {
                    long foodId = rs.getLong("food_id");
                    if (rs.wasNull() || !rs.getBoolean("food_active")) {
                        // A recipe without complete active ingredient data is not selectable.
                        return Optional.empty();
                    }
                    ingredients.add(new IngredientNutritionLine(foodId, rs.getBigDecimal("quantity_grams"),
                            new NutritionFacts(rs.getBigDecimal("calories_per_100g"),
                                    rs.getBigDecimal("protein_per_100g"), rs.getBigDecimal("carbs_per_100g"),
                                    rs.getBigDecimal("fat_per_100g"), rs.getBigDecimal("fiber_per_100g"))));
                } while (rs.next());
                return Optional.of(new RecipeNutritionInput(recipeId, name, mealType, base, ingredients));
            }
        }
    }

    @Override
    public List<RecipeCandidate> listCandidates(Connection connection) throws SQLException {
        List<RecipeCandidate> result = new ArrayList<>();
        // Small project catalog; production optimization can batch ingredient reads.
        try (PreparedStatement ps = connection.prepareStatement(
                "SELECT recipe_id FROM recipes WHERE active=TRUE ORDER BY recipe_id LIMIT 200")) {
            try (ResultSet rs = ps.executeQuery()) {
                List<Long> ids = new ArrayList<>();
                while (rs.next()) ids.add(rs.getLong(1));
                NutritionCalculator calc = new NutritionCalculator();
                for (Long id : ids) {
                    Optional<RecipeNutritionInput> maybe = findNutritionInput(connection, id);
                    if (maybe.isEmpty()) continue;
                    RecipeNutritionInput recipe = maybe.get();
                    Set<Long> foodIds = new HashSet<>();
                    for (IngredientNutritionLine ingredient : recipe.ingredients()) foodIds.add(ingredient.foodId());
                    result.add(new RecipeCandidate(id, recipe.name(), recipe.mealType(), foodIds,
                            calc.calculate(recipe, java.math.BigDecimal.ONE)));
                }
            }
        }
        return result;
    }
}
