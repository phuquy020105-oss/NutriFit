package com.nutrifit.service;

import com.nutrifit.dto.IngredientNutritionLine;
import com.nutrifit.dto.NutritionFacts;
import com.nutrifit.dto.RecipeNutritionInput;
import com.nutrifit.model.MealEntry;
import org.junit.jupiter.api.Test;
import java.math.BigDecimal;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class NutritionCalculatorTest {
    private final NutritionCalculator calculator = new NutritionCalculator();

    @Test
    void calculatesNutrientsAcrossBaseServings() {
        RecipeNutritionInput recipe = new RecipeNutritionInput(1L, "Sample", MealEntry.MealType.LUNCH,
                new BigDecimal("2.00"), List.of(
                new IngredientNutritionLine(11L, new BigDecimal("200.00"),
                        new NutritionFacts(new BigDecimal("100"),new BigDecimal("10"),
                                new BigDecimal("20"),new BigDecimal("5"),new BigDecimal("2")))));
        NutritionFacts result = calculator.calculate(recipe, new BigDecimal("1.50"));
        assertEquals(new BigDecimal("150.000"), result.caloriesKcal());
        assertEquals(new BigDecimal("15.000"), result.proteinG());
        assertEquals(new BigDecimal("30.000"), result.carbsG());
        assertEquals(new BigDecimal("7.500"), result.fatG());
        assertEquals(new BigDecimal("3.000"), result.fiberG());
    }

    @Test
    void rejectsInvalidServings() {
        assertThrows(IllegalArgumentException.class,
                () -> MealPlannerService.validServings(new BigDecimal("0.001")));
        assertThrows(IllegalArgumentException.class,
                () -> MealPlannerService.validServings(BigDecimal.ZERO));
        assertEquals(new BigDecimal("1.50"),
                MealPlannerService.validServings(new BigDecimal("1.5")));
    }

    @Test
    void rescalesOldSnapshotRatherThanRereadingRecipe() {
        NutritionFacts stored = new NutritionFacts(new BigDecimal("100.000"),
                new BigDecimal("10.000"),new BigDecimal("0.000"),
                new BigDecimal("2.500"),new BigDecimal("1.000"));
        assertEquals(new BigDecimal("200.000"), calculator.rescaleStored(stored,
                new BigDecimal("1.00"), new BigDecimal("2.00")).caloriesKcal());
    }
}
