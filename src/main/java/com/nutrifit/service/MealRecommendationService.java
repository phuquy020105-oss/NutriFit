package com.nutrifit.service;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.FoodPreferenceDAO;
import com.nutrifit.dao.JdbcRecipeReadAdapter;
import com.nutrifit.dto.RecipeCandidate;
import com.nutrifit.dto.RecommendedRecipe;
import com.nutrifit.model.FoodPreference;
import com.nutrifit.model.MealEntry;
import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
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

    /** Preliminary premium check: must be replaced/approved by Payment owner at integration. */
    public boolean hasPremiumAccess(long userId) throws SQLException {
        if (userId <= 0) return false;
        try (Connection c = DatabaseConfig.getConnection()) {
            return premiumInConnection(c, userId);
        }
    }

    public List<RecommendedRecipe> recommend(long userId, MealEntry.MealType type, int limit)
            throws SQLException {
        if (userId <= 0) throw new SecurityException("Login required");
        if (type == null || limit < 1 || limit > 30) {
            throw new IllegalArgumentException("Invalid recommendation filters");
        }
        try (Connection c = DatabaseConfig.getConnection()) {
            if (!premiumInConnection(c, userId)) {
                throw new SecurityException("Premium subscription required");
            }
            BigDecimal dailyTarget = dailyTarget(c, userId);
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
                String reason = matches > 0 ? "Matches " + matches + " liked ingredient(s)" : "No disliked ingredients";
                if (mealTarget != null && mealTarget.signum() > 0) {
                    double deviation = recipe.perServing().caloriesKcal().subtract(mealTarget).abs()
                            .divide(mealTarget, java.math.MathContext.DECIMAL64).doubleValue();
                    score += Math.max(0, 5.0 - deviation * 5.0);
                    reason += "; compared with a 1/3 daily calorie target";
                }
                scored.add(new RecommendedRecipe(recipe, score, reason));
            }
            scored.sort(Comparator.comparingDouble(RecommendedRecipe::score).reversed()
                    .thenComparing(x -> x.recipe().name()));
            return List.copyOf(scored.subList(0, Math.min(limit, scored.size())));
        }
    }

    private boolean premiumInConnection(Connection c, long userId) throws SQLException {
        String sql = "SELECT subscription_status,premium_expires_at FROM users WHERE user_id=?";
        try (PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setLong(1, userId);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next() || !"PREMIUM".equals(rs.getString("subscription_status"))) return false;
                Timestamp expiry = rs.getTimestamp("premium_expires_at");
                return expiry == null || expiry.toLocalDateTime().isAfter(LocalDateTime.now());
            }
        }
    }

    private BigDecimal dailyTarget(Connection c, long userId) throws SQLException {
        try (PreparedStatement ps = c.prepareStatement(
                "SELECT target_kcal FROM userprofiles WHERE user_id=?")) {
            ps.setLong(1, userId);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? rs.getBigDecimal(1) : null;
            }
        }
    }
}
