package com.nutrifit.dto;

import com.nutrifit.model.MealEntry;
import java.math.BigDecimal;

public record SuggestedMeal(long recipeId, String name, MealEntry.MealType mealType,
                            BigDecimal servings, NutritionFacts nutrition, String imageUrl) {
    public SuggestedMeal(long recipeId,String name,MealEntry.MealType mealType,BigDecimal servings,NutritionFacts nutrition) {
        this(recipeId,name,mealType,servings,nutrition,null);
    }
}
