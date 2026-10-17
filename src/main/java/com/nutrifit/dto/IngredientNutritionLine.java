package com.nutrifit.dto;

import java.math.BigDecimal;
import java.util.Objects;

public record IngredientNutritionLine(long foodId, BigDecimal quantityGrams,
                                      NutritionFacts nutrientsPer100g) {
    public IngredientNutritionLine {
        if (foodId <= 0) throw new IllegalArgumentException("foodId must be positive");
        Objects.requireNonNull(quantityGrams);
        Objects.requireNonNull(nutrientsPer100g);
        if (quantityGrams.signum() <= 0) throw new IllegalArgumentException("Ingredient grams must be positive");
    }
}
