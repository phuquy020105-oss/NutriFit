package com.nutrifit.service;

import com.nutrifit.dto.IngredientNutritionLine;
import com.nutrifit.dto.NutritionFacts;
import com.nutrifit.dto.RecipeNutritionInput;
import java.math.BigDecimal;

/** Grams -> nutrients using food values per 100g, normalized to recipe.base_servings. */
public class NutritionCalculator {
    private static final BigDecimal HUNDRED = new BigDecimal("100");

    public NutritionFacts calculate(RecipeNutritionInput recipe, BigDecimal servings) {
        if (recipe == null) throw new IllegalArgumentException("Recipe is required");
        BigDecimal amount = MealPlannerService.validServings(servings);
        NutritionFacts entireRecipe = NutritionFacts.ZERO;
        for (IngredientNutritionLine line : recipe.ingredients()) {
            BigDecimal gramsPer100 = line.quantityGrams().divide(HUNDRED);
            entireRecipe = entireRecipe.add(line.nutrientsPer100g().scale(gramsPer100));
        }
        return entireRecipe.scale(amount).toMealEntry(recipe.baseServings());
    }

    /** Re-scale a *stored* snapshot, rather than silently reading an edited recipe again. */
    public NutritionFacts rescaleStored(NutritionFacts previous, BigDecimal oldServings,
                                        BigDecimal newServings) {
        if (previous == null) throw new IllegalArgumentException("Snapshot is required");
        BigDecimal oldAmount = MealPlannerService.validServings(oldServings);
        BigDecimal newAmount = MealPlannerService.validServings(newServings);
        return previous.scale(newAmount).toMealEntry(oldAmount);
    }
}
