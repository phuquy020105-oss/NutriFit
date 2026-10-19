package com.nutrifit.dto;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Objects;

/** Server-owned preview, including the journal totals seen before saving. */
public record MealSuggestion(long userId, LocalDate date, BigDecimal targetKcal,
                             boolean personalized, List<SuggestedMeal> meals,
                             NutritionFacts recordedToday, NutritionFacts projectedDay, int recordedMealCount) {
    public MealSuggestion {
        meals = List.copyOf(meals);
        Objects.requireNonNull(recordedToday);
        Objects.requireNonNull(projectedDay);
        if (recordedMealCount < 0) throw new IllegalArgumentException("Invalid journal count");
    }
    /** Retained constructor for callers without a journal snapshot. */
    public MealSuggestion(long userId, LocalDate date, BigDecimal targetKcal,
                          boolean personalized, List<SuggestedMeal> meals) {
        this(userId, date, targetKcal, personalized, meals, NutritionFacts.ZERO.rounded(), sum(meals), 0);
    }
    private static NutritionFacts sum(List<SuggestedMeal> meals) {
        NutritionFacts sum = NutritionFacts.ZERO;
        for (SuggestedMeal meal : meals) sum = sum.add(meal.nutrition());
        return sum.rounded();
    }
    public NutritionFacts total() { return sum(meals); }
    public BigDecimal differenceKcal() { return total().caloriesKcal().subtract(targetKcal); }
    public BigDecimal projectedDifferenceKcal() { return projectedDay.caloriesKcal().subtract(targetKcal); }
    public boolean exceedsTarget() { return projectedDifferenceKcal().signum() > 0; }
}
