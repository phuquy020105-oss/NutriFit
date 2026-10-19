package com.nutrifit.service;

import com.nutrifit.dao.*;
import com.nutrifit.dto.*;
import com.nutrifit.model.*;
import java.lang.reflect.Proxy;
import java.math.BigDecimal;
import java.sql.*;
import java.time.*;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class MealRecommendationServiceTest {
    static final long USER = 42;
    static final Clock CLOCK = Clock.fixed(Instant.parse("2026-10-19T05:00:00Z"), ZoneId.of("Asia/Bangkok"));

    @Test void freeGetsExactlyThreeCorrectMealsWithoutReadingPreferencesOrWriting() throws Exception {
        Fixture f = new Fixture();
        f.saved.add(new FoodPreference(USER, 110L, FoodPreference.PreferenceType.DISLIKE));
        MealSuggestion day = f.service.recommendDay(USER);
        assertEquals(List.of(MealEntry.MealType.values()), day.meals().stream().map(SuggestedMeal::mealType).toList());
        assertFalse(day.personalized());
        assertEquals(0, f.preferenceReads);
        assertEquals(3, day.meals().size());
        assertTrue(day.meals().stream().allMatch(m -> m.servings().compareTo(BigDecimal.ONE) == 0));
        assertEquals(0, day.total().caloriesKcal().compareTo(new BigDecimal("1500")));
        assertEquals(0, day.differenceKcal().compareTo(new BigDecimal("-900")));
    }
    @Test void clientPortionsAreIgnoredAndAllMacrosUseOneStandardServing() throws Exception {
        Fixture f = new Fixture();
        MealSuggestion day = f.service.recommendDay(USER);
        Map<MealEntry.MealType, BigDecimal> portions = amounts("1.5");
        MealSuggestion edited = f.service.refresh(USER, day, portions);
        NutritionFacts expected = NutritionFacts.ZERO;
        for (SuggestedMeal m : edited.meals()) {
            NutritionFacts facts = new NutritionCalculator().calculate(f.inputs.get(m.recipeId()), new BigDecimal("1.00"));
            assertEquals(facts, m.nutrition());
            expected = expected.add(facts);
        }
        assertEquals(expected.rounded(), edited.total());
    }
    @Test void premiumDislikeExcludesIngredientAndLikeRanksAlternativeFirst() throws Exception {
        Fixture f = new Fixture(); f.premium = true;
        f.saved.add(new FoodPreference(USER, 110L, FoodPreference.PreferenceType.DISLIKE));
        f.saved.add(new FoodPreference(USER, 121L, FoodPreference.PreferenceType.LIKE));
        MealSuggestion day = f.service.recommendDay(USER);
        assertTrue(day.personalized());
        assertEquals(11, day.meals().get(0).recipeId());
        assertEquals(21, day.meals().get(1).recipeId());
        assertTrue(day.meals().stream().noneMatch(m -> f.inputs.get(m.recipeId()).ingredients().stream()
                .anyMatch(i -> i.foodId() == 110)));
        assertEquals(21, f.service.recommend(USER, MealEntry.MealType.LUNCH, 2).getFirst().recipe().recipeId());
    }
    @Test void premiumWithoutPreferencesStillGetsThreeMeals() throws Exception {
        Fixture f = new Fixture(); f.premium = true;
        assertEquals(3, f.service.recommendDay(USER).meals().size());
        assertEquals(1, f.preferenceReads);
    }
    @Test void expiredPremiumUsesFreePathAndIgnoresOldPreferences() throws Exception {
        Fixture f = new Fixture(); f.premium = false;
        for (RecipeNutritionInput r : f.inputs.values()) {
            f.saved.add(new FoodPreference(USER, r.ingredients().getFirst().foodId(), FoodPreference.PreferenceType.DISLIKE));
        }
        assertEquals(3, f.service.recommendDay(USER).meals().size());
        assertEquals(0, f.preferenceReads);
    }
    @Test void insufficientEligibleRecipesFailWithoutRelaxingDislike() {
        Fixture f = new Fixture(); f.premium = true;
        f.saved.add(new FoodPreference(USER, 110L, FoodPreference.PreferenceType.DISLIKE));
        f.saved.add(new FoodPreference(USER, 111L, FoodPreference.PreferenceType.DISLIKE));
        RecommendationUnavailableException e = assertThrows(RecommendationUnavailableException.class,
                () -> f.service.recommendDay(USER));
        assertTrue(e.getMessage().contains("bữa sáng"));
    }
    @Test void missingTargetFailsSafelyInsteadOfInventingBmr() {
        Fixture f = new Fixture(); f.target = null;
        assertThrows(RecommendationUnavailableException.class, () -> f.service.recommendDay(USER));
    }
    @Test void previewCannotCrossAccountOrDayAndCannotForgeMealTypes() throws Exception {
        Fixture f = new Fixture(); MealSuggestion day = f.service.recommendDay(USER);
        assertThrows(SecurityException.class, () -> f.service.refresh(USER + 1, day, amounts("1")));
        for (int offset : new int[]{-1, 1}) {
            MealSuggestion stale = new MealSuggestion(USER, day.date().plusDays(offset), day.targetKcal(), false, day.meals());
            assertThrows(RecommendationUnavailableException.class, () -> f.service.refresh(USER, stale, amounts("1")));
        }
        MealSuggestion duplicate = new MealSuggestion(USER, day.date(), day.targetKcal(), false,
                List.of(day.meals().getFirst(), day.meals().getFirst(), day.meals().getLast()));
        assertThrows(IllegalArgumentException.class, () -> f.service.refresh(USER, duplicate, amounts("1")));
    }
    @Test void serverRechecksNewDislikesAndInactiveOrMismatchedRecipes() throws Exception {
        Fixture f = new Fixture(); MealSuggestion day = f.service.recommendDay(USER);
        long first = day.meals().getFirst().recipeId();
        f.premium = true;
        f.saved.add(new FoodPreference(USER, f.inputs.get(first).ingredients().getFirst().foodId(), FoodPreference.PreferenceType.DISLIKE));
        assertThrows(RecommendationUnavailableException.class, () -> f.service.refresh(USER, day, amounts("1")));
        f.premium = false; f.inputs.remove(first);
        assertThrows(RecommendationUnavailableException.class, () -> f.service.refresh(USER, day, amounts("1")));
    }
    @Test void clientServingsAreIgnoredButNutritionOverflowIsRejected() throws Exception {
        Fixture f = new Fixture(); MealSuggestion day = f.service.recommendDay(USER);
        for (String bad : List.of("0", "-1", "1.001", "1.32", "0.89", "1.53", "1.23", "3", "1000000")) {
            MealSuggestion refreshed=f.service.refresh(USER,day,amounts(bad));
            assertTrue(refreshed.meals().stream().allMatch(m -> m.servings().equals(new BigDecimal("1.00"))));
        }
        long id = day.meals().getFirst().recipeId();
        RecipeNutritionInput old = f.inputs.get(id);
        f.inputs.put(id, new RecipeNutritionInput(id, old.name(), old.mealType(), BigDecimal.ONE,
                List.of(new IngredientNutritionLine(1, new BigDecimal("100"), facts("1000000000")))));
        assertThrows(IllegalArgumentException.class, () -> f.service.refresh(USER, day, amounts("1")));
    }
    @Test void invalidIdentityDoesNotOpenConnection() {
        MealRecommendationService s = new MealRecommendationService(() -> { throw new AssertionError("No JDBC expected"); });
        assertThrows(SecurityException.class, () -> s.recommendDay(0));
        assertThrows(SecurityException.class, () -> s.recommend(0, MealEntry.MealType.LUNCH, 1));
    }
    @Test void searchesCombinationsInsteadOfChoosingEachMealNearOneThird() throws Exception {
        Fixture f = new Fixture(); f.inputs.clear(); f.target = new BigDecimal("2000");
        put(f,10,MealEntry.MealType.BREAKFAST,"400"); put(f,11,MealEntry.MealType.BREAKFAST,"550");
        put(f,20,MealEntry.MealType.LUNCH,"700"); put(f,21,MealEntry.MealType.LUNCH,"1000");
        put(f,30,MealEntry.MealType.DINNER,"600"); put(f,31,MealEntry.MealType.DINNER,"650");
        MealSuggestion day = f.service.recommendDay(USER);
        assertEquals(List.of(10L,21L,30L),day.meals().stream().map(SuggestedMeal::recipeId).toList());
        assertEquals(0,day.total().caloriesKcal().compareTo(f.target));
        assertTrue(day.meals().stream().allMatch(m -> m.servings().compareTo(BigDecimal.ONE) == 0));
    }
    @Test void allThirtyRecipesAreConsideredAndExtremeTargetsNeverScalePortions() throws Exception {
        Fixture f = new Fixture(); f.inputs.clear();
        for (var type : MealEntry.MealType.values()) for (int i=0;i<10;i++) {
            put(f,100L*(type.ordinal()+1)+i,type,Integer.toString(400+i*10));
        }
        for (String target : List.of("100", "10000")) {
            f.target = new BigDecimal(target);
            MealSuggestion day = f.service.recommendDay(USER);
            assertTrue(day.meals().stream().allMatch(m -> m.servings().compareTo(BigDecimal.ONE) == 0));
            assertEquals(0,day.total().caloriesKcal().compareTo(new BigDecimal(target.equals("100")?"1200":"1470")));
            assertNotEquals(0,day.differenceKcal().signum());
        }
    }
    @Test void premiumLikesCanWinWithinCalorieBandButNotOverrideLargeEnergyMismatch() throws Exception {
        Fixture f = new Fixture(); f.inputs.clear(); f.premium=true; f.target=new BigDecimal("2000");
        put(f,10,MealEntry.MealType.BREAKFAST,"400"); put(f,11,MealEntry.MealType.BREAKFAST,"350");
        put(f,20,MealEntry.MealType.LUNCH,"900"); put(f,30,MealEntry.MealType.DINNER,"700");
        f.saved.add(new FoodPreference(USER,111L,FoodPreference.PreferenceType.LIKE));
        assertEquals(11L,f.service.recommendDay(USER).meals().getFirst().recipeId());
        put(f,11,MealEntry.MealType.BREAKFAST,"20");
        assertEquals(10L,f.service.recommendDay(USER).meals().getFirst().recipeId());
    }
    @Test void journalChangesChoiceAndWarnsOnActualProjectedTotalIncludingExistingMeals() throws Exception {
        Fixture f = new Fixture(); f.target=new BigDecimal("1800");
        f.journal.add(entry("500"));
        MealSuggestion day = f.service.recommendDay(USER);
        assertEquals(1,day.recordedMealCount());
        assertEquals(0,day.recordedToday().caloriesKcal().compareTo(new BigDecimal("500")));
        assertEquals(0,day.total().caloriesKcal().compareTo(new BigDecimal("1300")));
        assertEquals(0,day.projectedDifferenceKcal().signum());
        assertFalse(day.exceedsTarget());
        f.journal.clear();f.journal.add(entry("1900"));
        day=f.service.recommendDay(USER);
        assertTrue(day.exceedsTarget());
        assertEquals(0,day.projectedDay().caloriesKcal().compareTo(new BigDecimal("3100")));
        assertEquals(0,day.projectedDifferenceKcal().compareTo(new BigDecimal("1300")));
    }
    @Test void fixedPortionsRecalculateAllFiveFactsAndRefreshJournalWarning() throws Exception {
        Fixture f=new Fixture();f.target=new BigDecimal("1800");
        MealSuggestion day=f.service.recommendDay(USER);
        f.journal.add(entry("600"));
        for (String forged : List.of("0.5","1.32","2","999999")) {
            MealSuggestion changed=f.service.refresh(USER,day,amounts(forged));
            NutritionFacts sum=NutritionFacts.ZERO;
            for (SuggestedMeal meal:changed.meals()) {
                NutritionFacts facts=new NutritionCalculator().calculate(f.inputs.get(meal.recipeId()),BigDecimal.ONE);
                assertEquals(facts,meal.nutrition());sum=sum.add(facts);
                assertEquals(new BigDecimal("1.00"),meal.servings());
            }
            assertEquals(sum.rounded(),changed.total());
            assertEquals(sum.add(MealPlannerService.snapshot(f.journal.getFirst())).rounded(),changed.projectedDay());
            assertEquals(changed.projectedDifferenceKcal().signum()>0,changed.exceedsTarget());
        }
    }
    @Test void explicitRegenerationChoosesDifferentEligibleRecipesAndFallsBackIfOnlyOneCombination() throws Exception {
        Fixture f=new Fixture(); MealSuggestion first=f.service.recommendDay(USER);
        MealSuggestion next=f.service.recommendDay(USER,first);
        assertNotEquals(first.meals().stream().map(SuggestedMeal::recipeId).toList(),next.meals().stream().map(SuggestedMeal::recipeId).toList());
        assertTrue(next.meals().stream().allMatch(m -> m.servings().equals(new BigDecimal("1.00"))));
        Set<Long> only=first.meals().stream().map(SuggestedMeal::recipeId).collect(java.util.stream.Collectors.toSet());
        f.inputs.keySet().removeIf(id -> !only.contains(id));
        MealSuggestion unchanged=f.service.recommendDay(USER,first);
        assertEquals(first.meals(),unchanged.meals());
        assertThrows(SecurityException.class,()->f.service.recommendDay(USER+1,first));
    }
    private static MealEntry entry(String kcal) {
        return new MealEntry(10L,999L,"Recorded meal",MealEntry.MealType.LUNCH,BigDecimal.ONE,
                new BigDecimal(kcal),BigDecimal.ONE,BigDecimal.TEN,BigDecimal.ONE,BigDecimal.ONE);
    }
    private static void put(Fixture f,long id,MealEntry.MealType type,String kcal) {
        f.inputs.put(id,new RecipeNutritionInput(id,"Recipe "+id,type,BigDecimal.ONE,
                List.of(new IngredientNutritionLine(id+100,new BigDecimal("100"),facts(kcal)))));
    }
    static Map<MealEntry.MealType, BigDecimal> amounts(String amount) {
        Map<MealEntry.MealType, BigDecimal> result = new EnumMap<>(MealEntry.MealType.class);
        for (var type : MealEntry.MealType.values()) result.put(type, new BigDecimal(amount));
        return result;
    }
    static NutritionFacts facts(String kcal) {
        return new NutritionFacts(new BigDecimal(kcal), new BigDecimal("11.111"),
                new BigDecimal("23.456"), new BigDecimal("7.123"), new BigDecimal("2.345"));
    }
    static class Fixture {
        boolean premium;
        int preferenceReads;
        BigDecimal target = new BigDecimal("2400");
        final Map<Long, RecipeNutritionInput> inputs = new LinkedHashMap<>();
        final List<FoodPreference> saved = new ArrayList<>();
        final Connection connection = (Connection) Proxy.newProxyInstance(getClass().getClassLoader(),
                new Class<?>[]{Connection.class}, (p,m,a) -> {
                    if (m.getName().equals("close")) return null;
                    if (m.getName().equals("getAutoCommit")) return true;
                    throw new AssertionError("Preview attempted JDBC mutation: " + m.getName());
                });
        final NutritionUserReadDAO users = new NutritionUserReadDAO() {
            @Override public boolean hasPremiumAccess(Connection c,long user,LocalDateTime now) {
                assertEquals(USER,user); return premium;
            }
            @Override public Optional<BigDecimal> findTargetKcal(Connection c,long user) {
                assertEquals(USER,user); return Optional.ofNullable(target);
            }
        };
        final FoodPreferenceDAO preferences = new FoodPreferenceDAO() {
            @Override public List<FoodPreference> findByUser(Connection c,long user) {
                assertEquals(USER,user); preferenceReads++; return saved;
            }
        };
        final RecipeReadPort recipes = new RecipeReadPort() {
            @Override public Optional<RecipeNutritionInput> findNutritionInput(Connection c,long id) {
                return Optional.ofNullable(inputs.get(id));
            }
            @Override public List<RecipeCandidate> listCandidates(Connection c) {
                return inputs.values().stream().map(r -> new RecipeCandidate(r.recipeId(), r.name(),
                        r.mealType(), Set.of(r.ingredients().getFirst().foodId()),
                        new NutritionCalculator().calculate(r,BigDecimal.ONE))).toList();
            }
        };
        final List<MealEntry> journal = new ArrayList<>();
        final MealPlanDAO plans = new MealPlanDAO() {
            @Override public Optional<MealPlan> findByUserAndDate(Connection c,long user,LocalDate day) {
                assertEquals(USER,user); assertEquals(LocalDate.now(CLOCK),day);
                return journal.isEmpty() ? Optional.empty() : Optional.of(new MealPlan(10L,user,day,null));
            }
        };
        final MealEntryDAO entries = new MealEntryDAO() {
            @Override public List<MealEntry> findByPlan(Connection c,long plan) {
                assertEquals(10L,plan); return List.copyOf(journal);
            }
        };
        final MealRecommendationService service = new MealRecommendationService(() -> connection, preferences,
                recipes, users, new NutritionCalculator(), CLOCK, plans, entries);
        Fixture() {
            for (var type : MealEntry.MealType.values()) for (int i=0;i<2;i++) {
                long id=(type.ordinal()+1)*10L+i;
                inputs.put(id,new RecipeNutritionInput(id,"Recipe "+id,type,new BigDecimal("1.5"),
                        List.of(new IngredientNutritionLine(id+100,new BigDecimal("100"),facts(i==0?"600":"750")))));
            }
        }
    }
}
