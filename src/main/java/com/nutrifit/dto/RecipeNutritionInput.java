package com.nutrifit.dto;

import com.nutrifit.model.MealEntry;
import java.math.BigDecimal;
import java.util.List;
import java.util.Objects;

public record RecipeNutritionInput(long recipeId, String name, MealEntry.MealType mealType,
                                   BigDecimal baseServings, List<IngredientNutritionLine> ingredients) {
    public RecipeNutritionInput {
        if (recipeId <= 0) throw new IllegalArgumentException("Invalid recipeId");
        Objects.requireNonNull(name);
        Objects.requireNonNull(mealType);
        Objects.requireNonNull(baseServings);
        Objects.requireNonNull(ingredients);
        if (baseServings.signum() <= 0 || ingredients.isEmpty()) {
            throw new IllegalArgumentException("Recipe needs base servings and ingredients");
        }
        ingredients = List.copyOf(ingredients);
    }
}
