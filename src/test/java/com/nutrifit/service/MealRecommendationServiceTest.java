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
        assertTrue(day.differenceKcal().abs().compareTo(new BigDecimal("10")) < 0);
    }
    @Test void freeCanChangePortionsAndBackendRecomputesAllMacros() throws Exception {
        Fixture f = new Fixture();
        MealSuggestion day = f.service.recommendDay(USER);
        Map<MealEntry.MealType, BigDecimal> portions = amounts("1.23");
        MealSuggestion edited = f.service.refresh(USER, day, portions);
        NutritionFacts expected = NutritionFacts.ZERO;
        for (SuggestedMeal m : edited.meals()) {
            NutritionFacts facts = new NutritionCalculator().calculate(f.inputs.get(m.recipeId()), new BigDecimal("1.23"));
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
    @Test void invalidServingsAndOverflowAreRejected() throws Exception {
        Fixture f = new Fixture(); MealSuggestion day = f.service.recommendDay(USER);
        for (String bad : List.of("0", "-1", "1.001", "1000000")) {
            assertThrows(IllegalArgumentException.class, () -> f.service.refresh(USER, day, amounts(bad)));
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
        final MealRecommendationService service = new MealRecommendationService(() -> connection, preferences,
                recipes, users, new NutritionCalculator(), CLOCK);
        Fixture() {
            for (var type : MealEntry.MealType.values()) for (int i=0;i<2;i++) {
                long id=(type.ordinal()+1)*10L+i;
                inputs.put(id,new RecipeNutritionInput(id,"Recipe "+id,type,new BigDecimal("1.5"),
                        List.of(new IngredientNutritionLine(id+100,new BigDecimal("100"),facts(i==0?"600":"750")))));
            }
        }
    }
}
