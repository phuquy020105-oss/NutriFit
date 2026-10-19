package com.nutrifit.service;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.FoodPreferenceDAO;
import com.nutrifit.dao.JdbcRecipeReadAdapter;
import com.nutrifit.dao.NutritionUserReadDAO;
import com.nutrifit.dto.*;
import com.nutrifit.model.FoodPreference;
import com.nutrifit.model.MealEntry.MealType;
import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.sql.Connection;
import java.sql.SQLException;
import java.time.Clock;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;

/** Database recipes and the existing Profile target; no external recipe generator. */
public class MealRecommendationService {
    private final FoodPreferenceDAO preferences;
    private final RecipeReadPort recipes;
    private final NutritionUserReadDAO users;
    private final NutritionCalculator calculator;
    private final ConnectionProvider connections;
    private final Clock clock;

    public MealRecommendationService() { this(DatabaseConfig::getConnection); }
    MealRecommendationService(ConnectionProvider connections) {
        this(connections, new FoodPreferenceDAO(), new JdbcRecipeReadAdapter(),
                new NutritionUserReadDAO(), new NutritionCalculator(), Clock.systemDefaultZone());
    }
    MealRecommendationService(ConnectionProvider connections, FoodPreferenceDAO preferences,
            RecipeReadPort recipes, NutritionUserReadDAO users, NutritionCalculator calculator, Clock clock) {
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
                    .divide(new BigDecimal("3"), MathContext.DECIMAL128);
            return rank(recipes.listCandidates(c), type, target, eligibility).stream().limit(limit).toList();
        }
    }

    public MealSuggestion recommendDay(long userId) throws SQLException {
        requireUser(userId);
        try (Connection c = connections.open()) {
            BigDecimal target = target(c, userId);
            Eligibility eligibility = eligibility(c, userId);
            List<RecipeCandidate> catalog = recipes.listCandidates(c);
            List<SuggestedMeal> meals = new ArrayList<>();
            BigDecimal mealTarget = target.divide(new BigDecimal("3"), MathContext.DECIMAL128);
            for (MealType type : MealType.values()) {
                List<RecommendedRecipe> ranked = rank(catalog, type, mealTarget, eligibility);
                if (ranked.isEmpty()) throw unavailable(type);
                RecipeCandidate candidate = ranked.getFirst().recipe();
                BigDecimal servings = portion(candidate, mealTarget);
                RecipeNutritionInput input = requireRecipe(c, candidate.recipeId(), type, eligibility);
                meals.add(new SuggestedMeal(input.recipeId(), input.name(), type, servings,
                        calculator.calculate(input, servings)));
            }
            return new MealSuggestion(userId, LocalDate.now(clock), target, eligibility.premium(), meals);
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
            BigDecimal servings = MealPlannerService.validServings(amounts.get(meal.mealType()));
            RecipeNutritionInput input = requireRecipe(c, meal.recipeId(), meal.mealType(), eligibility);
            meals.add(new SuggestedMeal(input.recipeId(), input.name(), input.mealType(), servings,
                    calculator.calculate(input, servings)));
        }
        return new MealSuggestion(userId, draft.date(), target(c, userId), eligibility.premium(), meals);
    }

    private void validateDraft(long userId, MealSuggestion draft, Map<MealType, BigDecimal> amounts) {
        if (draft == null || draft.userId() != userId) throw new SecurityException("Preview owner mismatch");
        if (!LocalDate.now(clock).equals(draft.date())) {
            throw new RecommendationUnavailableException("Gợi ý đã sang ngày khác. Hãy tạo gợi ý mới cho hôm nay.");
        }
        if (draft.meals().size() != 3 || amounts == null || amounts.size() != 3) {
            throw new IllegalArgumentException("Exactly three meals required");
        }
        Set<MealType> types = EnumSet.noneOf(MealType.class);
        for (SuggestedMeal meal : draft.meals()) {
            if (meal.mealType() == null || !types.add(meal.mealType())) {
                throw new IllegalArgumentException("Duplicate meal type");
            }
            MealPlannerService.validServings(amounts.get(meal.mealType()));
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
                .thenComparing(r -> r.perServing().scale(portion(r, mealTarget)).caloriesKcal().subtract(mealTarget).abs())
                .thenComparing(r -> r.perServing().caloriesKcal().subtract(mealTarget).abs())
                .thenComparingLong(RecipeCandidate::recipeId);
        return valid.stream().sorted(ordering).map(r -> {
            long matches = r.foodIds().stream().filter(eligibility.likes()::contains).count();
            return new RecommendedRecipe(r, matches,
                    eligibility.premium() ? "Ưu tiên nguyên liệu thích; loại nguyên liệu không thích"
                            : "Theo mục tiêu calories trong hồ sơ");
        }).toList();
    }

    private static BigDecimal portion(RecipeCandidate recipe, BigDecimal target) {
        // Reasonable initial portion range; the user may subsequently edit within storage limits.
        return target.signum() <= 0 ? new BigDecimal("1.00")
                : target.divide(recipe.perServing().caloriesKcal(), 2, RoundingMode.HALF_UP)
                        .max(new BigDecimal("0.25")).min(new BigDecimal("4.00"));
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
