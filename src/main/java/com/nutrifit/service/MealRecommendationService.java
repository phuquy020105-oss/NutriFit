package com.nutrifit.service;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.FoodPreferenceDAO;
import com.nutrifit.dao.JdbcRecipeReadAdapter;
import com.nutrifit.dao.NutritionUserReadDAO;
import com.nutrifit.dto.RecipeCandidate;
import com.nutrifit.dto.RecommendedRecipe;
import com.nutrifit.model.FoodPreference;
import com.nutrifit.model.MealEntry;
import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Simple deterministic recommendation ranking; not a medical nutrition prescription. */
public class MealRecommendationService {
    private final FoodPreferenceDAO preferences = new FoodPreferenceDAO();
    private final RecipeReadPort recipes = new JdbcRecipeReadAdapter();
    private final NutritionUserReadDAO users = new NutritionUserReadDAO();
    private final ConnectionProvider connections;

    public MealRecommendationService() {
        this(DatabaseConfig::getConnection);
    }

    MealRecommendationService(ConnectionProvider connections) {
        this.connections = connections;
    }

    /** Preliminary premium check: must be replaced/approved by Payment owner at integration. */
    public boolean hasPremiumAccess(long userId) throws SQLException {
        if (userId <= 0) return false;
        try (Connection c = connections.open()) {
            return users.hasPremiumAccess(c, userId, LocalDateTime.now());
        }
    }

    public List<RecommendedRecipe> recommend(long userId, MealEntry.MealType type, int limit)
            throws SQLException {
        if (userId <= 0) throw new SecurityException("Login required");
        if (type == null || limit < 1 || limit > 30) {
            throw new IllegalArgumentException("Invalid recommendation filters");
        }
        try (Connection c = connections.open()) {
            if (!users.hasPremiumAccess(c, userId, LocalDateTime.now())) {
                throw new SecurityException("Premium subscription required");
            }
            BigDecimal dailyTarget = users.findTargetKcal(c, userId).orElse(null);
            BigDecimal mealTarget = dailyTarget == null ? null : dailyTarget.divide(new BigDecimal("3"), java.math.MathContext.DECIMAL128);
            Set<Long> liked = new HashSet<>();
            Set<Long> disliked = new HashSet<>();
            for (FoodPreference p : preferences.findByUser(c, userId)) {
                (p.getType() == FoodPreference.PreferenceType.LIKE ? liked : disliked).add(p.getFoodId());
            }
            List<RecommendedRecipe> scored = new ArrayList<>();
            for (RecipeCandidate recipe : recipes.listCandidates(c)) {
                if (recipe.mealType() != type || !java.util.Collections.disjoint(recipe.foodIds(), disliked)) continue;
                long matches = recipe.foodIds().stream().filter(liked::contains).count();
                double score = matches * 10.0;
                String reason = matches > 0 ? "Có " + matches + " nguyên liệu bạn thích"
                        : "Không chứa nguyên liệu bạn không thích";
                if (mealTarget != null && mealTarget.signum() > 0) {
                    double deviation = recipe.perServing().caloriesKcal().subtract(mealTarget).abs()
                            .divide(mealTarget, java.math.MathContext.DECIMAL64).doubleValue();
                    score += Math.max(0, 5.0 - deviation * 5.0);
                    reason += "; so sánh năng lượng mỗi khẩu phần với 1/3 mục tiêu ngày";
                }
                scored.add(new RecommendedRecipe(recipe, score, reason));
            }
            scored.sort(Comparator.comparingDouble(RecommendedRecipe::score).reversed()
                    .thenComparing(x -> x.recipe().name())
                    .thenComparingLong(x -> x.recipe().recipeId()));
            return List.copyOf(scored.subList(0, Math.min(limit, scored.size())));
        }
    }

}
