package com.nutrifit.dto;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Objects;

public record NutritionFacts(BigDecimal caloriesKcal, BigDecimal proteinG,
                             BigDecimal carbsG, BigDecimal fatG, BigDecimal fiberG) {
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

    private static BigDecimal r3(BigDecimal value) {
        return value.setScale(3, RoundingMode.HALF_UP);
    }
}
