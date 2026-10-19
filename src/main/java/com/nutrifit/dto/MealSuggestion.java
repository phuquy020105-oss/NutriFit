package com.nutrifit.dto;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

/** Server-owned preview. It is never a persisted meal plan until explicitly saved. */
public record MealSuggestion(long userId, LocalDate date, BigDecimal targetKcal,
                             boolean personalized, List<SuggestedMeal> meals) {
    public MealSuggestion { meals = List.copyOf(meals); }
    public NutritionFacts total() {
        NutritionFacts sum = NutritionFacts.ZERO;
        for (SuggestedMeal meal : meals) sum = sum.add(meal.nutrition());
        return sum.rounded();
    }
    public BigDecimal differenceKcal() { return total().caloriesKcal().subtract(targetKcal); }
}
