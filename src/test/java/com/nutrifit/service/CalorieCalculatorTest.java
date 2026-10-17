package com.nutrifit.service;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class CalorieCalculatorTest {

    @Test
    void calculatesCaloriesAndRoundsToThreeDecimalPlaces() {
        assertEquals(210.0, CalorieCalculator.calculate(7.0, 60.0, 30));
        assertEquals(3.333, CalorieCalculator.calculate(1.0, 10.0, 20));
    }

    @Test
    void rejectsNonPositiveMetWeightOrDuration() {
        assertThrows(IllegalArgumentException.class, () -> CalorieCalculator.calculate(0, 60, 30));
        assertThrows(IllegalArgumentException.class, () -> CalorieCalculator.calculate(5, 0, 30));
        assertThrows(IllegalArgumentException.class, () -> CalorieCalculator.calculate(5, 60, 0));
    }
}
