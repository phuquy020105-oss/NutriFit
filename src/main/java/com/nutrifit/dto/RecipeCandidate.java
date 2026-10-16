package com.nutrifit.dto;

import com.nutrifit.model.MealEntry;
import java.util.Set;

public record RecipeCandidate(long recipeId, String name, MealEntry.MealType mealType,
                              Set<Long> foodIds, NutritionFacts perServing) {
    public RecipeCandidate {
        foodIds = Set.copyOf(foodIds);
    }
}
