package com.nutrifit.dto;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Objects;

public record NutritionFacts(BigDecimal caloriesKcal, BigDecimal proteinG,
                             BigDecimal carbsG, BigDecimal fatG, BigDecimal fiberG) {
    private static final BigDecimal MEAL_ENTRY_MAX = new BigDecimal("999999999.999");
    public static final NutritionFacts ZERO = new NutritionFacts(
            BigDecimal.ZERO, BigDecimal.ZERO, BigDecimal.ZERO, BigDecimal.ZERO, BigDecimal.ZERO);

    public NutritionFacts {
        Objects.requireNonNull(caloriesKcal);
        Objects.requireNonNull(proteinG);
        Objects.requireNonNull(carbsG);
        Objects.requireNonNull(fatG);
        Objects.requireNonNull(fiberG);
        if (caloriesKcal.signum() < 0 || proteinG.signum() < 0 || carbsG.signum() < 0
                || fatG.signum() < 0 || fiberG.signum() < 0) {
            throw new IllegalArgumentException("Nutrient values must be non-negative");
        }
    }

    public NutritionFacts add(NutritionFacts other) {
        return new NutritionFacts(caloriesKcal.add(other.caloriesKcal), proteinG.add(other.proteinG),
                carbsG.add(other.carbsG), fatG.add(other.fatG), fiberG.add(other.fiberG));
    }

    public NutritionFacts scale(BigDecimal multiplier) {
        if (multiplier == null || multiplier.signum() < 0) {
            throw new IllegalArgumentException("Multiplier must be non-negative");
        }
        return new NutritionFacts(caloriesKcal.multiply(multiplier), proteinG.multiply(multiplier),
                carbsG.multiply(multiplier), fatG.multiply(multiplier), fiberG.multiply(multiplier));
    }

    public NutritionFacts rounded() {
        return new NutritionFacts(r3(caloriesKcal), r3(proteinG), r3(carbsG), r3(fatG), r3(fiberG));
    }

    /** Round once after division, then validate the stored DECIMAL(12,3) snapshot.
     * Daily totals and intermediate recipe values are deliberately not capped.
     */
    public NutritionFacts toMealEntry(BigDecimal divisor) {
        if (divisor == null || divisor.signum() <= 0) {
            throw new IllegalArgumentException("Divisor must be positive");
        }
        return new NutritionFacts(stored(caloriesKcal, divisor), stored(proteinG, divisor),
                stored(carbsG, divisor), stored(fatG, divisor), stored(fiberG, divisor));
    }

    private static BigDecimal stored(BigDecimal value, BigDecimal divisor) {
        BigDecimal result = value.divide(divisor, 3, RoundingMode.HALF_UP);
        if (result.compareTo(MEAL_ENTRY_MAX) > 0) {
            throw new IllegalArgumentException("Nutrition exceeds the meal entry storage limit");
        }
        return result;
    }

    private static BigDecimal r3(BigDecimal value) {
        return value.setScale(3, RoundingMode.HALF_UP);
    }
}
