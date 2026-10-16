package com.nutrifit.service;

import com.nutrifit.dto.IngredientNutritionLine;
import com.nutrifit.dto.NutritionFacts;
import com.nutrifit.dto.RecipeNutritionInput;
import java.math.BigDecimal;
import java.math.MathContext;

/** Grams -> nutrients using food values per 100g, normalized to recipe.base_servings. */
public class NutritionCalculator {
    private static final BigDecimal HUNDRED = new BigDecimal("100");

    public NutritionFacts calculate(RecipeNutritionInput recipe, BigDecimal servings) {
        if (servings == null || servings.signum() <= 0) {
            throw new IllegalArgumentException("Servings must be > 0");
        }
        NutritionFacts entireRecipe = NutritionFacts.ZERO;
        for (IngredientNutritionLine line : recipe.ingredients()) {
            BigDecimal gramsPer100 = line.quantityGrams().divide(HUNDRED, MathContext.DECIMAL128);
            entireRecipe = entireRecipe.add(line.nutrientsPer100g().scale(gramsPer100));
        }
        BigDecimal scale = servings.divide(recipe.baseServings(), MathContext.DECIMAL128);
        return entireRecipe.scale(scale).rounded();
    }

    /** Re-scale a *stored* snapshot, rather than silently reading an edited recipe again. */
    public NutritionFacts rescaleStored(NutritionFacts previous, BigDecimal oldServings,
                                        BigDecimal newServings) {
        if (oldServings == null || oldServings.signum() <= 0 ||
                newServings == null || newServings.signum() <= 0) {
            throw new IllegalArgumentException("Servings must be > 0");
        }
        return previous.scale(newServings.divide(oldServings, MathContext.DECIMAL128)).rounded();
    }
}
