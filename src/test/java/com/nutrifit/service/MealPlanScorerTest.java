package com.nutrifit.service;

import com.nutrifit.dto.*;
import java.math.BigDecimal;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class MealPlanScorerTest {
    final MealPlanScorer scorer=new MealPlanScorer();
    private NutritionFacts facts(String k,String p,String c,String f,String fiber) {
        return new NutritionFacts(new BigDecimal(k),new BigDecimal(p),new BigDecimal(c),new BigDecimal(f),new BigDecimal(fiber));
    }
    private MealPlanScorer.Score score(NutritionFacts f,NutritionGoal goal){
        return scorer.evaluate(f,new BigDecimal("1800"),goal,List.of(f.scale(new BigDecimal(".25")),
                f.scale(new BigDecimal(".40")),f.scale(new BigDecimal(".35"))),0,0,0);
    }
    @Test void twoCaloriesNeverOutweighExcessFatAndMissingFiber() {
        var exact=facts("1800","90","140","100","2");
        var balanced=facts("1802","90","225","60","26");
        assertTrue(score(balanced,NutritionGoal.MAINTAIN).total()<score(exact,NutritionGoal.MAINTAIN).total());
        assertTrue(score(exact,NutritionGoal.MAINTAIN).fat()>0);
        assertTrue(score(exact,NutritionGoal.MAINTAIN).fiber()>score(balanced,NutritionGoal.MAINTAIN).fiber());
    }
    @Test void everyComponentAndWeightedTotalAreBounded() {
        var s=scorer.evaluate(facts("1","1000","2000","3000","0"),new BigDecimal("1800"),NutritionGoal.LOSE,
                List.of(NutritionFacts.ZERO,NutritionFacts.ZERO,NutritionFacts.ZERO),10,10,10);
        for(double n:new double[]{s.energy(),s.protein(),s.carbohydrate(),s.fat(),s.fiber(),s.mealBalance(),s.diversity(),s.repetition(),s.preference(),s.total()})
            assertTrue(n>=0 && n<=1);
    }
    @Test void goalsChangeOnlyEnergyDirectionAndNeverProteinReference() {
        var high=facts("2000","100","250","66.667","28");
        var lose=score(high,NutritionGoal.LOSE);var gain=score(high,NutritionGoal.GAIN);var maintain=score(high,NutritionGoal.MAINTAIN);
        assertTrue(lose.energy()>maintain.energy());assertEquals(gain.energy(),maintain.energy());
        assertEquals(lose.protein(),gain.protein());assertEquals(lose.fat(),gain.fat());
        var low=facts("1600","80","200","53.333","23");
        assertTrue(score(low,NutritionGoal.GAIN).energy()>score(low,NutritionGoal.MAINTAIN).energy());
        assertEquals(NutritionGoal.LOSE,NutritionGoal.fromProfile(" lose "));
        assertEquals(NutritionGoal.MAINTAIN,NutritionGoal.fromProfile(null));
    }
    @Test void warningsArePresentForPoorBestAvailableMenu() {
        var warnings=scorer.warnings(facts("1300","60","100","80","3"),new BigDecimal("2200"));
        assertTrue(warnings.size()>=3);
    }
}
