package com.nutrifit.dto;

import org.junit.jupiter.api.Test;
import java.math.BigDecimal;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class NutritionFactsTest {
    private NutritionFacts all(String value) {
        BigDecimal n = new BigDecimal(value);
        return new NutritionFacts(n, n, n, n, n);
    }

    @Test
    void acceptsMaximumForEveryNutrient() {
        assertEquals(all("999999999.999"), all("999999999.999").toMealEntry(BigDecimal.ONE));
    }

    @Test
    void checksOverflowAfterRoundingForEachNutrient() {
        for (int index = 0; index < 5; index++) {
            BigDecimal[] values = {BigDecimal.ZERO, BigDecimal.ZERO, BigDecimal.ZERO,
                    BigDecimal.ZERO, BigDecimal.ZERO};
            values[index] = new BigDecimal("999999999.9995");
            NutritionFacts facts = new NutritionFacts(values[0], values[1], values[2], values[3], values[4]);
            assertThrows(IllegalArgumentException.class, () -> facts.toMealEntry(BigDecimal.ONE));
        }
        assertEquals(all("999999999.999"), all("999999999.9994").toMealEntry(BigDecimal.ONE));
        assertThrows(IllegalArgumentException.class, () -> all("1000000000").toMealEntry(BigDecimal.ONE));
    }

    @Test
    void roundsHalfUpOnceAndAllowsLargeIntermediateValues() {
        assertEquals(all("0.001"), all("0.0005").toMealEntry(BigDecimal.ONE));
        assertEquals(all("0.000"), all("0.0004").toMealEntry(BigDecimal.ONE));
        assertEquals(all("999999999.999"), all("1999999999.998").toMealEntry(new BigDecimal("2")));
        for (BigDecimal divisor : List.of(BigDecimal.ZERO, new BigDecimal("-1"))) {
            assertThrows(IllegalArgumentException.class, () -> all("1").toMealEntry(divisor));
        }
        assertThrows(IllegalArgumentException.class, () -> all("1").toMealEntry(null));
    }

    @Test
    void dashboardTotalsCanExceedTheLimitForAnIndividualEntry() {
        assertEquals(all("1999999999.998"), all("999999999.999").add(all("999999999.999")).rounded());
    }
}
