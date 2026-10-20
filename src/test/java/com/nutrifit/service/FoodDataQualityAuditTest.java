package com.nutrifit.service;

import com.nutrifit.dto.*;
import com.nutrifit.model.MealEntry;
import com.nutrifit.util.JsonLite;
import java.math.*;
import java.nio.file.*;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Current catalog and provenance checks; retired research snapshots are not runtime fixtures. */
class FoodDataQualityAuditTest {
    static final List<String> KEYS=List.of("calories_per_100g","protein_per_100g","carbs_per_100g","fat_per_100g","fiber_per_100g");
    @SuppressWarnings("unchecked") static Map<String,Object> object(Object o){return (Map<String,Object>)o;}
    @SuppressWarnings("unchecked") static List<Map<String,Object>> rows(Object o){return (List<Map<String,Object>>)o;}
    static Map<String,Object> read(String path)throws Exception{return object(JsonLite.parse(Files.readString(Path.of(path))));}
    static Map<String,Map<String,Object>> evidence()throws Exception{
        var out=new HashMap<String,Map<String,Object>>();for(var f:rows(read("database/seed/provenance.json").get("foods")))assertNull(out.put(f.get("food_ref").toString(),f));return out;
    }
    static NutritionFacts sourceFacts(Map<String,Object> f){
        var n=object(f.get("nutrients"));var v=KEYS.stream().map(k->new BigDecimal(object(n.get(k)).get("value").toString())).toList();return new NutritionFacts(v.get(0),v.get(1),v.get(2),v.get(3),v.get(4));
    }
    @Test void everyNutrientKeepsItsSourceMethodConfidenceAndExplicitEstimate()throws Exception{
        var catalog=read("database/seed/catalog.json");var evidence=evidence();assertEquals(100,evidence.size());int estimates=0;
        for(var f:rows(catalog.get("foods"))){
            var e=evidence.get(f.get("ref"));assertNotNull(e);assertEquals(f.get("state"),e.get("state"));assertFalse(object(e.get("source")).isEmpty());
            for(String k:KEYS){var fact=object(object(e.get("nutrients")).get(k));assertNotNull(fact.get("value"));
                assertEquals(0,new BigDecimal(object(f.get("nutrients")).get(k).toString()).compareTo(new BigDecimal(fact.get("value").toString())));
                assertTrue(Set.of("MATCHED","CALCULATED","ESTIMATED").contains(fact.get("status")));assertFalse(fact.get("method").toString().isBlank());assertNotNull(fact.get("confidence"));
                if("ESTIMATED".equals(fact.get("status")))estimates++;
            }
        }assertEquals(103,estimates);
    }
    @Test void allSixtyRecipesUseValidUnitsAndCalculatorMatchesIndependentDecimalSum()throws Exception{
        var catalog=RealCatalog.load();assertEquals(60,catalog.size());assertEquals(607,catalog.stream().mapToInt(r->r.ingredients().size()).sum());
        var calc=new NutritionCalculator();for(var type:MealEntry.MealType.values())assertEquals(20,catalog.stream().filter(r->r.mealType()==type).count());
        for(var r:catalog){assertEquals(0,BigDecimal.ONE.compareTo(r.baseServings()));var sums=new BigDecimal[]{BigDecimal.ZERO,BigDecimal.ZERO,BigDecimal.ZERO,BigDecimal.ZERO,BigDecimal.ZERO};
            assertFalse(r.ingredients().isEmpty());var ids=new HashSet<Long>();
            for(var i:r.ingredients()){assertTrue(ids.add(i.foodId()));assertTrue(i.quantityGrams().signum()>0);var n=i.nutrientsPer100g();var values=List.of(n.caloriesKcal(),n.proteinG(),n.carbsG(),n.fatG(),n.fiberG());
                for(int j=0;j<5;j++)sums[j]=sums[j].add(values.get(j).multiply(i.quantityGrams()).divide(new BigDecimal("100")));
            }
            var n=calc.calculate(r,BigDecimal.ONE);var values=List.of(n.caloriesKcal(),n.proteinG(),n.carbsG(),n.fatG(),n.fiberG());for(int j=0;j<5;j++)assertEquals(0,sums[j].setScale(3,RoundingMode.HALF_UP).compareTo(values.get(j)),r.name());
        }
    }
    @Test void sourceBasedRiceAndDriedFungusRegressionKeepsEdibleStateAndFiber()throws Exception{
        var foods=evidence();var recipe=new RecipeNutritionInput(1L,"Offline source calculation",MealEntry.MealType.LUNCH,BigDecimal.ONE,
            List.of(new IngredientNutritionLine(1L,new BigDecimal("100"),sourceFacts(foods.get("F001"))),new IngredientNutritionLine(59L,new BigDecimal("2"),sourceFacts(foods.get("F059")))));
        var result=new NutritionCalculator().calculate(recipe,BigDecimal.ONE);
        assertEquals(new BigDecimal("135.680"),result.caloriesKcal());assertEquals(new BigDecimal("2.875"),result.proteinG());assertEquals(new BigDecimal("27.828"),result.carbsG());assertEquals(new BigDecimal("0.295"),result.fatG());assertEquals(new BigDecimal("1.802"),result.fiberG());
    }
    @Test void cookedBellyKeepsItsOfficialSourceIdentityAndValues()throws Exception{
        var belly=evidence().get("F018");assertEquals("974",object(belly.get("source")).get("record_id"));assertEquals("Pork, belly, boiled",object(belly.get("source")).get("description"));
        assertEquals(new BigDecimal("428"),sourceFacts(belly).caloriesKcal());assertEquals(new BigDecimal("38.20"),sourceFacts(belly).fatG());
    }
    @Test void unresolvedOfficialMatchesAreExplicitEstimatesNotInventedMeasurements()throws Exception{
        var foods=evidence();for(String ref:List.of("F011","F025","F058")){
            var food=foods.get(ref);assertEquals("OWNER_ACCEPTED_EDUCATIONAL_FORMULATION_OR_ANALOG",object(food.get("source")).get("type"));
            for(String key:KEYS){var fact=object(object(food.get("nutrients")).get(key));assertEquals("ESTIMATED",fact.get("status"));assertEquals("LOW",fact.get("confidence"));assertFalse(fact.get("method").toString().isBlank());}
        }
    }
}
