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

    @Test
    void rejectsInvalidDecimalServingsAtTheCalculatorBoundary() {
        RecipeNutritionInput recipe = recipe("100", "1");
        for (BigDecimal servings : new BigDecimal[]{null, BigDecimal.ZERO, new BigDecimal("-1"),
                new BigDecimal("0.001"), new BigDecimal("1.001"), new BigDecimal("1000000")}) {
            assertThrows(IllegalArgumentException.class, () -> calculator.calculate(recipe, servings));
            assertThrows(IllegalArgumentException.class,
                    () -> calculator.rescaleStored(NutritionFacts.ZERO, BigDecimal.ONE, servings));
            assertThrows(IllegalArgumentException.class,
                    () -> calculator.rescaleStored(NutritionFacts.ZERO, servings, BigDecimal.ONE));
        }
        assertThrows(IllegalArgumentException.class, () -> calculator.calculate(null, BigDecimal.ONE));
        assertThrows(IllegalArgumentException.class,
                () -> calculator.rescaleStored(null, BigDecimal.ONE, BigDecimal.ONE));
        assertEquals(new BigDecimal("0.01"), MealPlannerService.validServings(new BigDecimal("0.0100")));
        assertEquals(new BigDecimal("999999.99"),
                MealPlannerService.validServings(new BigDecimal("999999.99")));
    }

    @Test
    void rejectsOverflowForBothNewAndRescaledSnapshots() {
        assertThrows(IllegalArgumentException.class,
                () -> calculator.calculate(recipe("2000", "1"), new BigDecimal("999999.99")));
        NutritionFacts maximum = new NutritionFacts(new BigDecimal("999999999.999"),
                BigDecimal.ZERO, BigDecimal.ZERO, BigDecimal.ZERO, BigDecimal.ZERO);
        assertEquals(maximum.rounded(), calculator.rescaleStored(maximum, BigDecimal.ONE, BigDecimal.ONE));
        assertThrows(IllegalArgumentException.class,
                () -> calculator.rescaleStored(maximum, BigDecimal.ONE, new BigDecimal("2")));
    }

    @Test
    void dividesBaseServingsWithoutRoundingTheIntermediateRatio() {
        assertEquals(new BigDecimal("0.167"),
                calculator.calculate(recipe("1", "6"), BigDecimal.ONE).caloriesKcal());
        assertEquals(new BigDecimal("999999999.999"),
                calculator.calculate(recipe("1999999999.998", "2"), BigDecimal.ONE).caloriesKcal());
    }

    private RecipeNutritionInput recipe(String kcal, String baseServings) {
        return new RecipeNutritionInput(1L, "Sample", MealEntry.MealType.LUNCH,
                new BigDecimal(baseServings), List.of(new IngredientNutritionLine(11L,
                new BigDecimal("100"), new NutritionFacts(new BigDecimal(kcal),
                BigDecimal.ZERO, BigDecimal.ZERO, BigDecimal.ZERO, BigDecimal.ZERO))));
    }
}
