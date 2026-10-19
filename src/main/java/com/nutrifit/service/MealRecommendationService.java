package com.nutrifit.service;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.FoodPreferenceDAO;
import com.nutrifit.dao.JdbcRecipeReadAdapter;
import com.nutrifit.dao.NutritionUserReadDAO;
import com.nutrifit.dao.MealPlanDAO;
import com.nutrifit.dao.MealEntryDAO;
import com.nutrifit.model.MealEntry;
import com.nutrifit.dto.*;
import com.nutrifit.model.FoodPreference;
import com.nutrifit.model.MealEntry.MealType;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.sql.Connection;
import java.sql.SQLException;
import java.time.Clock;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;

/** Database recipes and the existing Profile target; no external recipe generator. */
public class MealRecommendationService {
    private static final BigDecimal STANDARD_SERVINGS = new BigDecimal("1.00");
    private final FoodPreferenceDAO preferences;
    private final RecipeReadPort recipes;
    private final NutritionUserReadDAO users;
    private final NutritionCalculator calculator;
    private final ConnectionProvider connections;
    private final Clock clock;
    private final MealPlanDAO plans;
    private final MealEntryDAO entries;

    public MealRecommendationService() { this(DatabaseConfig::getConnection); }
    MealRecommendationService(ConnectionProvider connections) {
        this(connections, new FoodPreferenceDAO(), new JdbcRecipeReadAdapter(),
                new NutritionUserReadDAO(), new NutritionCalculator(), Clock.systemDefaultZone());
    }
    MealRecommendationService(ConnectionProvider connections, FoodPreferenceDAO preferences,
            RecipeReadPort recipes, NutritionUserReadDAO users, NutritionCalculator calculator, Clock clock) {
        this(connections, preferences, recipes, users, calculator, clock, new MealPlanDAO(), new MealEntryDAO());
    }
    MealRecommendationService(ConnectionProvider connections, FoodPreferenceDAO preferences,
            RecipeReadPort recipes, NutritionUserReadDAO users, NutritionCalculator calculator, Clock clock,
            MealPlanDAO plans, MealEntryDAO entries) {
        this.plans = plans; this.entries = entries;
        this.connections = connections; this.preferences = preferences; this.recipes = recipes;
        this.users = users; this.calculator = calculator; this.clock = clock;
    }

    public boolean hasPremiumAccess(long userId) throws SQLException {
        if (userId <= 0) return false;
        try (Connection c = connections.open()) {
            return users.hasPremiumAccess(c, userId, LocalDateTime.now(clock));
        }
    }

    /** Retained integration API: basic recommendations are available to every authenticated user. */
    public List<RecommendedRecipe> recommend(long userId, MealType type, int limit) throws SQLException {
        requireUser(userId);
        if (type == null || limit < 1 || limit > 30) throw new IllegalArgumentException("Invalid filters");
        try (Connection c = connections.open()) {
            Eligibility eligibility = eligibility(c, userId);
            BigDecimal target = users.findTargetKcal(c, userId).orElse(BigDecimal.ZERO)
                    .multiply(mealShare(type));
            return rank(recipes.listCandidates(c), type, target, eligibility).stream().limit(limit).toList();
        }
    }

    public MealSuggestion recommendDay(long userId) throws SQLException {
        return recommendDay(userId, null);
    }

    /** Explicit regeneration prefers a different eligible combination, when one exists. */
    public MealSuggestion recommendDay(long userId, MealSuggestion previous) throws SQLException {
        requireUser(userId);
        if (previous != null && previous.userId() != userId) throw new SecurityException("Preview owner mismatch");
        try (Connection c = connections.open()) {
            BigDecimal target = target(c, userId);
            Eligibility eligibility = eligibility(c, userId);
            List<RecipeCandidate> catalog = recipes.listCandidates(c);
            LocalDate day = LocalDate.now(clock);
            List<MealEntry> journal = journal(c, userId, day);
            NutritionFacts recorded = recorded(journal);
            Map<MealType, List<Option>> options = new EnumMap<>(MealType.class);
            for (MealType type : MealType.values()) {
                List<Option> choices = rank(catalog, type, target.multiply(mealShare(type)), eligibility).stream()
                        .map(r -> new Option(r.recipe(), r.recipe().foodIds().stream().filter(eligibility.likes()::contains).count(), addedKcal(r.recipe(), journal))).toList();
                if (choices.isEmpty()) throw unavailable(type);
                options.put(type, choices);
            }
            Combination best = null, alternative = null;
            for (Option breakfast : options.get(MealType.BREAKFAST))
                for (Option lunch : options.get(MealType.LUNCH))
                    for (Option dinner : options.get(MealType.DINNER)) {
                        Combination choice = new Combination(breakfast, lunch, dinner, recorded.caloriesKcal(), target);
                        if (best == null || choice.compareTo(best) < 0) best = choice;
                        if (previous != null && !choice.sameRecipes(previous)
                                && (alternative == null || choice.compareTo(alternative) < 0)) alternative = choice;
                    }
            if (alternative != null) best = alternative;
            List<SuggestedMeal> meals = new ArrayList<>();
            for (Option option : List.of(best.breakfast(), best.lunch(), best.dinner())) {
                RecipeNutritionInput input = requireRecipe(c, option.recipe().recipeId(), option.recipe().mealType(), eligibility);
                meals.add(new SuggestedMeal(input.recipeId(), input.name(), input.mealType(), STANDARD_SERVINGS,
                        calculator.calculate(input, STANDARD_SERVINGS)));
            }
            return preview(userId, day, target, eligibility.premium(), meals, journal);
        }
    }

    public MealSuggestion refresh(long userId, MealSuggestion draft, Map<MealType, BigDecimal> amounts)
            throws SQLException {
        requireUser(userId);
        validateDraft(userId, draft, amounts);
        try (Connection c = connections.open()) { return refresh(c, userId, draft, amounts); }
    }

    /** Called inside the save transaction, rechecking expiry, preferences, recipes and portions. */
    MealSuggestion refresh(Connection c, long userId, MealSuggestion draft, Map<MealType, BigDecimal> amounts)
            throws SQLException {
        requireUser(userId);
        validateDraft(userId, draft, amounts);
        Eligibility eligibility = eligibility(c, userId);
        List<SuggestedMeal> meals = new ArrayList<>();
        for (SuggestedMeal meal : draft.meals()) {
            BigDecimal servings = STANDARD_SERVINGS;
            RecipeNutritionInput input = requireRecipe(c, meal.recipeId(), meal.mealType(), eligibility);
            meals.add(new SuggestedMeal(input.recipeId(), input.name(), input.mealType(), servings,
                    calculator.calculate(input, servings)));
        }
        return preview(userId, draft.date(), target(c, userId), eligibility.premium(), meals,
                journal(c, userId, draft.date()));
    }

    void validateDraft(long userId, MealSuggestion draft, Map<MealType, BigDecimal> amounts) {
        if (draft == null || draft.userId() != userId) throw new SecurityException("Preview owner mismatch");
        if (!LocalDate.now(clock).equals(draft.date())) {
            throw new RecommendationUnavailableException("Gợi ý đã sang ngày khác. Hãy tạo gợi ý mới cho hôm nay.");
        }
        if (draft.meals().size() != 3) {
            throw new IllegalArgumentException("Exactly three meals required");
        }
        Set<MealType> types = EnumSet.noneOf(MealType.class);
        for (SuggestedMeal meal : draft.meals()) {
            if (meal.mealType() == null || !types.add(meal.mealType())) {
                throw new IllegalArgumentException("Duplicate meal type");
            }
        }
    }

    private BigDecimal target(Connection c, long userId) throws SQLException {
        return users.findTargetKcal(c, userId).orElseThrow(() ->
                new RecommendationUnavailableException("Hãy hoàn tất mục tiêu dinh dưỡng trong hồ sơ trước khi tạo thực đơn."));
    }

    private Eligibility eligibility(Connection c, long userId) throws SQLException {
        boolean premium = users.hasPremiumAccess(c, userId, LocalDateTime.now(clock));
        Set<Long> likes = new HashSet<>(), dislikes = new HashSet<>();
        // Expired/Free users never read or apply stored Premium preferences.
        if (premium) for (FoodPreference p : preferences.findByUser(c, userId)) {
            (p.getType() == FoodPreference.PreferenceType.LIKE ? likes : dislikes).add(p.getFoodId());
        }
        return new Eligibility(premium, likes, dislikes);
    }

    private List<RecommendedRecipe> rank(List<RecipeCandidate> catalog, MealType type,
                                        BigDecimal mealTarget, Eligibility eligibility) {
        List<RecipeCandidate> valid = catalog.stream().filter(r -> r.mealType() == type
                && r.perServing().caloriesKcal().signum() > 0
                && Collections.disjoint(r.foodIds(), eligibility.dislikes())).toList();
        Comparator<RecipeCandidate> ordering = Comparator
                .comparingLong((RecipeCandidate r) -> r.foodIds().stream().filter(eligibility.likes()::contains).count())
                .reversed()
                .thenComparing(r -> r.perServing().caloriesKcal().subtract(mealTarget).abs())
                .thenComparingLong(RecipeCandidate::recipeId);
        return valid.stream().sorted(ordering).map(r -> {
            long matches = r.foodIds().stream().filter(eligibility.likes()::contains).count();
            return new RecommendedRecipe(r, matches,
                    eligibility.premium() ? "Ưu tiên nguyên liệu thích; loại nguyên liệu không thích"
                            : "Theo mục tiêu calories trong hồ sơ");
        }).toList();
    }

    private static BigDecimal mealShare(MealType type) {
        return switch (type) {
            case BREAKFAST -> new BigDecimal("0.25");
            case LUNCH -> new BigDecimal("0.40");
            case DINNER -> new BigDecimal("0.35");
        };
    }

    private List<MealEntry> journal(Connection c, long userId, LocalDate day) throws SQLException {
        var plan = plans.findByUserAndDate(c, userId, day);
        if (plan.isEmpty()) return List.of();
        return c.getAutoCommit() ? entries.findByPlan(c, plan.get().getPlanId())
                : entries.findByPlanForUpdate(c, plan.get().getPlanId());
    }

    private static NutritionFacts recorded(List<MealEntry> journal) {
        NutritionFacts total = NutritionFacts.ZERO;
        for (MealEntry entry : journal) total = total.add(MealPlannerService.snapshot(entry));
        return total.rounded();
    }

    private BigDecimal addedKcal(RecipeCandidate recipe, List<MealEntry> journal) {
        for (MealEntry old : journal) {
            if (old.getRecipeId() == recipe.recipeId() && old.getMealType() == recipe.mealType()) {
                NutritionFacts merged = calculator.rescaleStored(MealPlannerService.snapshot(old), old.getServings(),
                        old.getServings().add(BigDecimal.ONE));
                return merged.caloriesKcal().subtract(old.getCaloriesKcal());
            }
        }
        return recipe.perServing().caloriesKcal();
    }

    private MealSuggestion preview(long userId, LocalDate day, BigDecimal target, boolean premium,
                                    List<SuggestedMeal> meals, List<MealEntry> journal) {
        NutritionFacts projected = NutritionFacts.ZERO;
        Set<String> merged = new HashSet<>();
        for (MealEntry old : journal) {
            SuggestedMeal match = meals.stream().filter(m -> m.recipeId() == old.getRecipeId()
                    && m.mealType() == old.getMealType()).findFirst().orElse(null);
            if (match == null) projected = projected.add(MealPlannerService.snapshot(old));
            else {
                projected = projected.add(calculator.rescaleStored(MealPlannerService.snapshot(old), old.getServings(),
                        old.getServings().add(match.servings())));
                merged.add(match.mealType() + ":" + match.recipeId());
            }
        }
        for (SuggestedMeal meal : meals) if (!merged.contains(meal.mealType() + ":" + meal.recipeId())) {
            projected = projected.add(meal.nutrition());
        }
        return new MealSuggestion(userId, day, target, premium, meals, recorded(journal), projected.rounded(), journal.size());
    }

    private record Option(RecipeCandidate recipe, long likes, BigDecimal addedKcal) { }

    private record Combination(Option breakfast, Option lunch, Option dinner, BigDecimal recorded, BigDecimal target)
            implements Comparable<Combination> {
        private boolean sameRecipes(MealSuggestion previous) {
            return previous.meals().size() == 3 && List.of(breakfast, lunch, dinner).stream().allMatch(option ->
                    previous.meals().stream().anyMatch(m -> m.mealType() == option.recipe().mealType()
                            && m.recipeId() == option.recipe().recipeId()));
        }
        private BigDecimal distance() {
            return recorded.add(breakfast.addedKcal()).add(lunch.addedKcal()).add(dinner.addedKcal()).subtract(target).abs();
        }
        private BigDecimal band() {
            // Within the same 10% target band, preferences can win without forcing portions.
            return distance().divide(target.max(BigDecimal.ONE).multiply(new BigDecimal("0.10")), 0, RoundingMode.DOWN);
        }
        private long likes() { return breakfast.likes() + lunch.likes() + dinner.likes(); }
        private BigDecimal balance() {
            BigDecimal total = breakfast.recipe().perServing().caloriesKcal()
                    .add(lunch.recipe().perServing().caloriesKcal()).add(dinner.recipe().perServing().caloriesKcal());
            return breakfast.recipe().perServing().caloriesKcal().subtract(total.multiply(mealShare(MealType.BREAKFAST))).abs()
                    .add(lunch.recipe().perServing().caloriesKcal().subtract(total.multiply(mealShare(MealType.LUNCH))).abs());
        }
        @Override public int compareTo(Combination other) {
            int result = band().compareTo(other.band());
            if (result == 0) result = Long.compare(other.likes(), likes());
            if (result == 0) result = distance().compareTo(other.distance());
            if (result == 0) result = balance().compareTo(other.balance());
            if (result == 0) result = Long.compare(breakfast.recipe().recipeId(), other.breakfast.recipe().recipeId());
            if (result == 0) result = Long.compare(lunch.recipe().recipeId(), other.lunch.recipe().recipeId());
            if (result == 0) result = Long.compare(dinner.recipe().recipeId(), other.dinner.recipe().recipeId());
            return result;
        }
    }

    private RecipeNutritionInput requireRecipe(Connection c, long id, MealType type, Eligibility eligibility)
            throws SQLException {
        RecipeNutritionInput input = recipes.findNutritionInput(c, id).orElseThrow(() -> unavailable(type));
        if (input.mealType() != type || input.ingredients().stream()
                .anyMatch(line -> eligibility.dislikes().contains(line.foodId()))) throw unavailable(type);
        return input;
    }

    private static RecommendationUnavailableException unavailable(MealType type) {
        String label = switch (type) { case BREAKFAST -> "bữa sáng"; case LUNCH -> "bữa trưa"; case DINNER -> "bữa tối"; };
        return new RecommendationUnavailableException("Không đủ công thức phù hợp cho " + label
                + ". Hãy kiểm tra sở thích hoặc dữ liệu món ăn. Nguyên liệu DISLIKE không được tự động bỏ qua.");
    }
    private static void requireUser(long userId) { if (userId <= 0) throw new SecurityException("Login required"); }
    private record Eligibility(boolean premium, Set<Long> likes, Set<Long> dislikes) { }
}
