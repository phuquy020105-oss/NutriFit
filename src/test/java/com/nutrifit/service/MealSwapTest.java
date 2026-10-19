package com.nutrifit.service;

import com.nutrifit.dto.*;
import com.nutrifit.model.*;
import com.nutrifit.model.MealEntry.MealType;
import java.math.BigDecimal;
import java.nio.file.*;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static com.nutrifit.service.MealRecommendationServiceTest.*;

class MealSwapTest {
    static MealSuggestion menu(Fixture f) throws Exception { return f.service.recommendDay(USER); }
    static SuggestedMeal meal(MealSuggestion s,MealType t){return s.meals().stream().filter(m->m.mealType()==t).findFirst().orElseThrow();}
    static void put(Fixture f,long id,MealType type,NutritionFacts n,long food){
        f.inputs.put(id,new RecipeNutritionInput(id,"Recipe "+id,type,BigDecimal.ONE,
                List.of(new IngredientNutritionLine(food,new BigDecimal("100"),n)),"/assets/images/recipes/recipe-"+id+".webp"));
    }
    static Fixture uniform(){
        Fixture f=new Fixture();f.inputs.clear();f.target=new BigDecimal("1800");
        for(var type:MealType.values())for(int n=0;n<4;n++)put(f,10L+type.ordinal()*10+n,type,facts("600"),100L+type.ordinal()*10+n);
        return f;
    }
    @Test void eachSlotChangesOnlyItselfAndNeverPersistsOrTrustsClientFacts()throws Exception{
        for(var type:MealType.values()){
            var f=uniform();var before=menu(f);var old=meal(before,type);
            var next=f.service.swap(USER,before,type,List.of(old.recipeId()));
            assertNotEquals(old.recipeId(),meal(next,type).recipeId());
            for(var other:MealType.values())if(other!=type)assertEquals(meal(before,other),meal(next,other));
            assertEquals(type,f.inputs.get(meal(next,type).recipeId()).mealType());
            assertTrue(f.journal.isEmpty());assertEquals(0,f.preferenceReads);
            assertEquals(new BigDecimal("1.00"),meal(next,type).servings());
            assertEquals(new NutritionCalculator().calculate(f.inputs.get(meal(next,type).recipeId()),BigDecimal.ONE),meal(next,type).nutrition());
            assertEquals(f.inputs.get(meal(next,type).recipeId()).imageUrl(),meal(next,type).imageUrl());
        }
    }
    @Test void preferencesArePremiumOnlyAndDislikesAreNeverRelaxed()throws Exception{
        for(boolean premium:List.of(false,true)){
            var f=uniform();var original=menu(f);long current=meal(original,MealType.LUNCH).recipeId();
            long disliked=21, liked=22;
            f.saved.add(new FoodPreference(USER,111L,FoodPreference.PreferenceType.DISLIKE));
            f.saved.add(new FoodPreference(USER,112L,FoodPreference.PreferenceType.LIKE));f.premium=premium;
            var next=f.service.swap(USER,original,MealType.LUNCH,List.of(current));
            assertEquals(premium?liked:disliked,meal(next,MealType.LUNCH).recipeId());
            if(!premium)assertEquals(0,f.preferenceReads);
        }
    }
    @Test void recentChoicesExhaustWithoutImmediateCyclingOrUnsafeFallback()throws Exception{
        var f=uniform();var s=menu(f);var history=new ArrayList<Long>();history.add(meal(s,MealType.DINNER).recipeId());
        for(int i=0;i<3;i++){
            var next=f.service.swap(USER,s,MealType.DINNER,history);
            long id=meal(next,MealType.DINNER).recipeId();assertFalse(history.contains(id));history.add(id);s=next;
        }
        assertEquals(s.meals(),f.service.swap(USER,s,MealType.DINNER,history).meals());
        f.inputs.keySet().removeIf(id->id>=30 && id!=history.getLast());
        assertEquals(s.meals(),f.service.swap(USER,s,MealType.DINNER,history).meals());
    }
    @Test void similarityUsesAllNutrientsAndRejectsLargeFatIncreaseOrEnergyChange()throws Exception{
        var f=uniform();var original=menu(f);
        put(f,21,MealType.LUNCH,new NutritionFacts(new BigDecimal("600"),new BigDecimal("20"),new BigDecimal("30"),new BigDecimal("50"),BigDecimal.ZERO),111);
        put(f,22,MealType.LUNCH,facts("610"),112);
        put(f,23,MealType.LUNCH,facts("1100"),113);
        var next=f.service.swap(USER,original,MealType.LUNCH,List.of(20L));
        assertEquals(22,meal(next,MealType.LUNCH).recipeId());
        assertEquals(1,MealRecommendationService.relative(BigDecimal.valueOf(3),BigDecimal.ZERO,3));
        assertEquals(.5,MealRecommendationService.relative(BigDecimal.valueOf(5),BigDecimal.ZERO,10));
        var low=uniform();low.inputs.keySet().removeIf(id->!Set.of(10L,20L,30L).contains(id));
        put(low,20,MealType.LUNCH,facts("80"),120);low.target=new BigDecimal("1280");
        var tiny=menu(low);put(low,21,MealType.LUNCH,facts("120"),121);
        assertEquals(20,meal(low.service.swap(USER,tiny,MealType.LUNCH,List.of(20L)),MealType.LUNCH).recipeId(),
            "A100kcal denominator floor must not disguise a50percent energy increase in a low-energy meal");
    }
    @Test void projectedJournalQualityCanExcludeAnOtherwiseSimilarReplacement()throws Exception{
        var f=uniform();var first=menu(f);
        // The old snapshot is much more energy-dense than the live reference. A merge of21
        // would add900kcal despite a600kcal menu card. The journal-aware guard must reject it.
        var old=new MealEntry(10L,21L,"Old snapshot",MealType.LUNCH,BigDecimal.ONE,
                new BigDecimal("900"),BigDecimal.TEN,BigDecimal.TEN,BigDecimal.TEN,BigDecimal.ONE);
        f.journal.add(old);f.target=new BigDecimal("2700");
        var current=f.service.refresh(USER,first,amounts("1"));
        var next=f.service.swap(USER,current,MealType.LUNCH,List.of(20L));
        assertNotEquals(21,meal(next,MealType.LUNCH).recipeId());assertEquals(22,meal(next,MealType.LUNCH).recipeId());
        assertEquals(new BigDecimal("900"),old.getCaloriesKcal());
        assertEquals(new BigDecimal("2700.000"),next.projectedDay().caloriesKcal());
    }
    @Test void ownerDateAndNullMealAreRejectedBeforeSwap()throws Exception{
        var f=uniform();var s=menu(f);
        assertThrows(SecurityException.class,()->f.service.swap(USER+1,s,MealType.LUNCH,List.of()));
        assertThrows(IllegalArgumentException.class,()->f.service.swap(USER,s,null,List.of()));
        var stale=new MealSuggestion(USER,s.date().minusDays(1),s.targetKcal(),false,s.meals());
        assertThrows(RecommendationUnavailableException.class,()->f.service.swap(USER,stale,MealType.LUNCH,List.of()));
    }
    @Test void actual30And60RecipeCatalogsBenchmarkSlotEquivalenceAndNovelty()throws Exception{
        var csv=new StringBuilder("catalog,target,premium,meal,attempts,changes,max_relative_calorie_change,unique_recipes\n");
        int totalChanges=0;
        for(String file:List.of("database/staging/food-quality-v1/release/catalog-A-baseline.json","database/staging/food-quality-v1/release/catalog-C-qualified.json")){
            var inputs=RealCatalog.load(Path.of(file));
            for(String kcal:List.of("1600","2000","2400"))for(boolean premium:List.of(false,true))for(var type:MealType.values()){
                var f=RealCatalogBenchmarkTest.fixture(inputs);f.target=new BigDecimal(kcal);f.premium=premium;
                if(premium){f.saved.add(new FoodPreference(USER,18L,FoodPreference.PreferenceType.DISLIKE));f.saved.add(new FoodPreference(USER,12L,FoodPreference.PreferenceType.LIKE));}
                var s=menu(f);var history=new ArrayList<Long>();history.add(meal(s,type).recipeId());int changes=0;double max=0;
                for(int i=0;i<6;i++){
                    var next=f.service.swap(USER,s,type,history);var before=meal(s,type);var after=meal(next,type);
                    for(var other:MealType.values())if(other!=type)assertEquals(meal(s,other),meal(next,other));
                    if(before.recipeId()==after.recipeId())break;
                    assertFalse(history.contains(after.recipeId()));history.add(after.recipeId());changes++;
                    double relative=MealRecommendationService.relative(after.nutrition().caloriesKcal(),before.nutrition().caloriesKcal(),100);
                    assertTrue(relative<=.35+1e-12);max=Math.max(max,relative);
                    assertEquals(type,f.inputs.get(after.recipeId()).mealType());
                    if(premium)assertTrue(f.inputs.get(after.recipeId()).ingredients().stream().noneMatch(l->l.foodId()==18));
                    assertTrue(f.journal.isEmpty());s=next;
                }
                totalChanges+=changes;
                csv.append(inputs.size()).append(',').append(kcal).append(',').append(premium).append(',').append(type).append(",6,").append(changes).append(',').append(max).append(',').append(history.size()).append('\n');
            }
        }
        assertTrue(totalChanges>30,"Actual catalogs must offer usable, diverse slot replacements");
        Files.createDirectories(Path.of("target/food-quality"));Files.writeString(Path.of("target/food-quality/swap-benchmark.csv"),csv);
    }
}
