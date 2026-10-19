package com.nutrifit.dto;

import com.nutrifit.model.MealEntry;
import java.util.Set;

public record RecipeCandidate(long recipeId, String name, MealEntry.MealType mealType,
                              Set<Long> foodIds, NutritionFacts perServing, String imageUrl) {
    public RecipeCandidate(long recipeId,String name,MealEntry.MealType mealType,Set<Long> foodIds,NutritionFacts perServing) {
        this(recipeId,name,mealType,foodIds,perServing,null);
    }
    public RecipeCandidate {
        foodIds = Set.copyOf(foodIds);
    }
}
