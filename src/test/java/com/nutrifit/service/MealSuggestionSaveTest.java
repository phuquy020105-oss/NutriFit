package com.nutrifit.service;

import com.nutrifit.dao.*;
import com.nutrifit.dto.*;
import com.nutrifit.model.*;
import java.lang.reflect.Proxy;
import java.math.BigDecimal;
import java.sql.*;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class MealSuggestionSaveTest {
    @Test void freeSavesThreeMealsInOneTransactionAndRecalculatesUntrustedFacts() throws Exception {
        Fixture f = new Fixture();
        MealSuggestion original=f.catalog.service.recommendDay(42);
        MealSuggestion forged=new MealSuggestion(42,original.date(),BigDecimal.ONE,false,
                original.meals().stream().map(m->new SuggestedMeal(m.recipeId(),"Untrusted name",m.mealType(),
                        BigDecimal.ONE,NutritionFacts.ZERO)).toList());
        MealSuggestion saved=f.service.saveSuggestion(42,forged,MealRecommendationServiceTest.amounts("1.23"));
        assertEquals(List.of("begin","commit","close"),f.events);
        assertEquals(3,f.committed.size());
        assertEquals(new BigDecimal("2400"),saved.targetKcal());
        for (SuggestedMeal m:saved.meals()) {
            MealEntry stored=f.committed.get(key(m.mealType(),m.recipeId()));
            assertEquals(m.nutrition(),MealPlannerService.snapshot(stored));
            assertNotEquals("Untrusted name",stored.getRecipeNameSnapshot());
            assertEquals(new BigDecimal("1.23"),stored.getServings());
        }
    }
    @Test void anySecondOrThirdWriteFailureRollsBackEntirePlanAndPreservesManualMeals() throws Exception {
        for(int failure:new int[]{2,3}) {
            Fixture f=new Fixture(); f.manual(); f.failAt=failure;
            MealSuggestion day=f.catalog.service.recommendDay(42);
            assertThrows(SQLException.class,()->f.service.saveSuggestion(42,day,MealRecommendationServiceTest.amounts("1")));
            assertEquals(List.of("begin","rollback","close"),f.events);
            assertEquals(1,f.committed.size());
            assertEquals("Manual meal",f.committed.get("manual").getRecipeNameSnapshot());
            assertFalse(f.planCommitted);
        }
    }
    @Test void duplicateRecipeMergesOriginalSnapshotAndLeavesOtherManualEntriesUntouched() throws Exception {
        Fixture f=new Fixture(); f.manual();
        MealSuggestion day=f.catalog.service.recommendDay(42);
        SuggestedMeal m=day.meals().getFirst();
        MealEntry old=new MealEntry(10L,m.recipeId(),"Historical snapshot",m.mealType(),
                new BigDecimal("1.00"),new BigDecimal("100.000"),new BigDecimal("10.000"),
                new BigDecimal("20.000"),new BigDecimal("5.000"),new BigDecimal("2.000"));
        old.setEntryId(50L);
        f.committed.put(key(m.mealType(),m.recipeId()),old);
        f.service.saveSuggestion(42,day,MealRecommendationServiceTest.amounts("1"));
        MealEntry merged=f.committed.get(key(m.mealType(),m.recipeId()));
        assertEquals("Historical snapshot",merged.getRecipeNameSnapshot());
        assertEquals(new BigDecimal("2.00"),merged.getServings());
        assertEquals(new BigDecimal("200.000"),merged.getCaloriesKcal());
        assertEquals(4,f.committed.size());
        assertEquals("Manual meal",f.committed.get("manual").getRecipeNameSnapshot());
    }
    @Test void ownerWrongDateAndInvalidPortionsCannotWrite() throws Exception {
        for(int mode=0;mode<4;mode++) {
            Fixture f=new Fixture();MealSuggestion day=f.catalog.service.recommendDay(42);
            MealSuggestion draft=mode==1||mode==2?new MealSuggestion(42,day.date().plusDays(mode==1?-1:1),
                    day.targetKcal(),false,day.meals()):day;
            long user=mode==0?43:42;
            Map<MealEntry.MealType,BigDecimal> amounts=MealRecommendationServiceTest.amounts(mode==3?"0":"1");
            assertThrows(RuntimeException.class,()->f.service.saveSuggestion(user,draft,amounts));
            assertTrue(f.committed.isEmpty());
            assertEquals(List.of("begin","rollback","close"),f.events);
        }
    }
    @Test void preferencesAreRecheckedInSameSaveTransaction() throws Exception {
        Fixture f=new Fixture();MealSuggestion day=f.catalog.service.recommendDay(42);
        f.catalog.premium=true;
        long ingredient=f.catalog.inputs.get(day.meals().getFirst().recipeId()).ingredients().getFirst().foodId();
        f.catalog.saved.add(new FoodPreference(42L,ingredient,FoodPreference.PreferenceType.DISLIKE));
        assertThrows(RecommendationUnavailableException.class,()->f.service.saveSuggestion(42,day,
                MealRecommendationServiceTest.amounts("1")));
        assertTrue(f.committed.isEmpty());
        assertEquals(0,f.writes);
    }
    private static String key(MealEntry.MealType type,long recipe){return type+":"+recipe;}
    private static MealEntry copy(MealEntry e){
        MealEntry result=new MealEntry(e.getPlanId(),e.getRecipeId(),e.getRecipeNameSnapshot(),e.getMealType(),
                e.getServings(),e.getCaloriesKcal(),e.getProteinG(),e.getCarbsG(),e.getFatG(),e.getFiberG());
        result.setEntryId(e.getEntryId());return result;
    }
    private static class Fixture {
        final MealRecommendationServiceTest.Fixture catalog=new MealRecommendationServiceTest.Fixture();
        final List<String> events=new ArrayList<>();
        Map<String,MealEntry> committed=new LinkedHashMap<>(),pending;
        boolean planCommitted;int writes,failAt;
        final Connection c=(Connection)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{Connection.class},
                (p,m,a)->{
                    switch(m.getName()){
                        case "setAutoCommit" -> {
                            assertEquals(false,a[0]);events.add("begin");pending=new LinkedHashMap<>();
                            committed.forEach((k,v)->pending.put(k,copy(v)));
                        }
                        case "commit" -> {events.add("commit");committed=pending;planCommitted=true;}
                        case "rollback" -> {events.add("rollback");pending=null;}
                        case "close" -> events.add("close");
                        default -> throw new AssertionError("Unexpected JDBC "+m.getName());
                    }return null;
                });
        final MealPlanDAO plans=new MealPlanDAO(){
            @Override public long findOrCreateForUpdate(Connection connection,long user,java.time.LocalDate day){
                assertSame(c,connection);assertEquals(42,user);
                assertEquals(java.time.LocalDate.now(MealRecommendationServiceTest.CLOCK),day);return 10;
            }
        };
        final MealEntryDAO entries=new MealEntryDAO(){
            @Override public Optional<MealEntry> findByPlanMealRecipe(Connection connection,long plan,MealEntry.MealType type,long id){
                assertSame(c,connection);return Optional.ofNullable(pending.get(key(type,id)));
            }
            @Override public long insert(Connection connection,MealEntry entry)throws SQLException{
                write();pending.put(key(entry.getMealType(),entry.getRecipeId()),entry);return writes+100;
            }
            @Override public void update(Connection connection,MealEntry entry)throws SQLException{
                write();pending.put(key(entry.getMealType(),entry.getRecipeId()),entry);
            }
            private void write()throws SQLException{if(++writes==failAt)throw new SQLException("injected failure");}
        };
        final MealPlannerService service=new MealPlannerService(plans,entries,catalog.recipes,new NutritionCalculator(),
                MealRecommendationServiceTest.CLOCK,()->c,catalog.users,catalog.preferences);
        void manual(){
            MealEntry e=new MealEntry(10L,999L,"Manual meal",MealEntry.MealType.LUNCH,BigDecimal.ONE,
                    BigDecimal.TEN,BigDecimal.ONE,BigDecimal.ONE,BigDecimal.ONE,BigDecimal.ONE);
            e.setEntryId(99L);committed.put("manual",e);
        }
    }
}
