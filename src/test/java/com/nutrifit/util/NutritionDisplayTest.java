package com.nutrifit.util;

import com.nutrifit.dto.*;
import java.math.BigDecimal;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class NutritionDisplayTest {
    @Test void vietnameseHalfUpIncludesNegativeDifferencesAndNull() {
        String[][] pairs={{"1693.655","1.694"},{"71.470","71"},{"158.923","159"},{"82.861","83"},{"4.991","5"},{"-.500","-1"},{".499","0"},{".500","1"}};
        for(var p:pairs)assertEquals(p[1],NutritionDisplay.integer(new BigDecimal(p[0])));
        assertEquals("—",NutritionDisplay.integer(null));
    }
    @Test void totalsRoundFromRawDataWithoutChangingThreeDecimalSnapshots() {
        var f=new NutritionFacts(new BigDecimal("100.490"),new BigDecimal("1.001"),new BigDecimal("2.002"),new BigDecimal("3.003"),new BigDecimal("4.004"));
        var total=f.add(f).add(f);
        assertEquals("301",NutritionDisplay.integer(total.caloriesKcal())); // not 100+100+100
        assertEquals("100",NutritionDisplay.integer(f.caloriesKcal()));
        assertEquals(new BigDecimal("100.490"),f.toMealEntry(BigDecimal.ONE).caloriesKcal());
        assertEquals(3,f.toMealEntry(BigDecimal.ONE).fiberG().scale());
    }
    @Test void imageUrlsAcceptOnlyPackagedLocalAssets() {
        assertEquals("/nutrifit/assets/images/recipes/pho-bo.webp",RecipeImage.url("/nutrifit","/assets/images/recipes/pho-bo.webp"));
        for(String bad:new String[]{null,"","javascript:alert(1)","https://evil.test/x.jpg","/assets/images/recipes/../x.png","/assets/images/recipes/a.webp?x=1","/assets/images/recipes/a\".jpg"})
            assertEquals("/nutrifit"+RecipeImage.FALLBACK,RecipeImage.url("/nutrifit",bad));
        assertEquals(RecipeImage.FALLBACK,RecipeImage.url("",null));
    }
}
