package com.nutrifit.service;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.JdbcRecipeReadAdapter;
import com.nutrifit.dao.MealEntryDAO;
import com.nutrifit.dao.MealPlanDAO;
import com.nutrifit.dto.DaySummary;
import com.nutrifit.dto.NutritionFacts;
import com.nutrifit.dto.RecipeCandidate;
import com.nutrifit.dto.RecipeNutritionInput;
import com.nutrifit.model.MealEntry;
import com.nutrifit.model.MealPlan;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.sql.Connection;
import java.sql.SQLException;
import java.time.Clock;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

/** Entry point for meal mutations; enforces current day and ownership. */
public class MealPlannerService {
    private final MealPlanDAO plans;
    private final MealEntryDAO entries;
    private final RecipeReadPort recipes;
    private final NutritionCalculator calculator;
    private final Clock clock;

    public MealPlannerService() {
        this(new MealPlanDAO(), new MealEntryDAO(), new JdbcRecipeReadAdapter(),
                new NutritionCalculator(), Clock.systemDefaultZone());
    }

    public MealPlannerService(MealPlanDAO plans, MealEntryDAO entries, RecipeReadPort recipes,
                              NutritionCalculator calculator, Clock clock) {
        this.plans = plans;
        this.entries = entries;
        this.recipes = recipes;
        this.calculator = calculator;
        this.clock = clock;
    }

    public LocalDate today() { return LocalDate.now(clock); }

    public DaySummary getToday(long userId) throws SQLException {
        return getDay(userId, today());
    }

    public DaySummary getPastDay(long userId, LocalDate day) throws SQLException {
        if (day == null || !day.isBefore(today())) {
            throw new IllegalArgumentException("History must be before today");
        }
        return getDay(userId, day);
    }

    private DaySummary getDay(long userId, LocalDate day) throws SQLException {
        checkUser(userId);
        try (Connection c = DatabaseConfig.getConnection()) {
            Optional<MealPlan> plan = plans.findByUserAndDate(c, userId, day);
            List<MealEntry> list = plan.isPresent() ? entries.findByPlan(c, plan.get().getPlanId()) : List.of();
            NutritionFacts sum = NutritionFacts.ZERO;
            for (MealEntry e : list) sum = sum.add(snapshot(e));
            return new DaySummary(day, plan.orElse(null), list, sum.rounded());
        }
    }

    public List<RecipeCandidate> listAvailableRecipes() throws SQLException {
        try (Connection c = DatabaseConfig.getConnection()) {
            return recipes.listCandidates(c);
        }
    }

    public MealEntry addMeal(long userId, long recipeId, MealEntry.MealType type, BigDecimal servings)
            throws SQLException {
        checkUser(userId);
        checkId(recipeId);
        BigDecimal amount = validServings(servings);
        if (type == null) throw new IllegalArgumentException("Select a meal type");
        try (Connection c = DatabaseConfig.getConnection()) {
            c.setAutoCommit(false);
            try {
                RecipeNutritionInput recipe = requireRecipe(c, recipeId, type);
                long planId = plans.findOrCreateForUpdate(c, userId, today());
                Optional<MealEntry> existing = entries.findByPlanMealRecipe(c, planId, type, recipeId);
                MealEntry e;
                if (existing.isPresent()) {
                    e = existing.get();
                    BigDecimal newServings = validServings(e.getServings().add(amount));
                    putFacts(e, calculator.rescaleStored(snapshot(e), e.getServings(), newServings));
                    e.setServings(newServings);
                    entries.update(c, e);
                } else {
                    NutritionFacts facts = calculator.calculate(recipe, amount);
                    e = new MealEntry(planId, recipeId, recipe.name(), type, amount,
                            facts.caloriesKcal(), facts.proteinG(), facts.carbsG(),
                            facts.fatG(), facts.fiberG());
                    e.setEntryId(entries.insert(c, e));
                }
                c.commit();
                return e;
            } catch (SQLException | RuntimeException e) {
                c.rollback();
                throw e;
            }
        }
    }

    public MealEntry updateMeal(long userId, long entryId, long recipeId,
            MealEntry.MealType type, BigDecimal servings) throws SQLException {
        checkUser(userId);
        checkId(entryId);
        checkId(recipeId);
        BigDecimal amount = validServings(servings);
        if (type == null) throw new IllegalArgumentException("Select a meal type");
        try (Connection c = DatabaseConfig.getConnection()) {
            c.setAutoCommit(false);
            try {
                MealEntry e = entries.findByIdAndUser(c, entryId, userId)
                        .orElseThrow(() -> new IllegalArgumentException("Meal entry not found"));
                verifyCurrentPlan(c, userId, e.getPlanId());
                if (e.getRecipeId().equals(recipeId) && e.getMealType() == type) {
                    putFacts(e, calculator.rescaleStored(snapshot(e), e.getServings(), amount));
                } else {
                    RecipeNutritionInput recipe = requireRecipe(c, recipeId, type);
                    Optional<MealEntry> duplicate = entries.findByPlanMealRecipe(
                            c, e.getPlanId(), type, recipeId);
                    if (duplicate.isPresent() && !duplicate.get().getEntryId().equals(entryId)) {
                        throw new IllegalArgumentException("Recipe already exists in this meal");
                    }
                    e.setRecipeId(recipeId);
                    e.setRecipeNameSnapshot(recipe.name());
                    e.setMealType(type);
                    putFacts(e, calculator.calculate(recipe, amount));
                }
                e.setServings(amount);
                entries.update(c, e);
                c.commit();
                return e;
            } catch (SQLException | RuntimeException e) {
                c.rollback();
                throw e;
            }
        }
    }

    public void removeMeal(long userId, long entryId) throws SQLException {
        checkUser(userId);
        checkId(entryId);
        try (Connection c = DatabaseConfig.getConnection()) {
            c.setAutoCommit(false);
            try {
                MealEntry e = entries.findByIdAndUser(c, entryId, userId)
                        .orElseThrow(() -> new IllegalArgumentException("Meal entry not found"));
                verifyCurrentPlan(c, userId, e.getPlanId());
                entries.delete(c, entryId, e.getPlanId());
                c.commit();
            } catch (SQLException | RuntimeException e) {
                c.rollback();
                throw e;
            }
        }
    }

    private void verifyCurrentPlan(Connection c, long userId, long planId) throws SQLException {
        MealPlan todayPlan = plans.findByUserAndDate(c, userId, today())
                .orElseThrow(() -> new IllegalArgumentException("Only today's entries can be edited"));
        if (!todayPlan.getPlanId().equals(planId)) {
            throw new IllegalArgumentException("Only today's entries can be edited");
        }
    }

    private RecipeNutritionInput requireRecipe(Connection c, long recipeId, MealEntry.MealType type)
            throws SQLException {
        RecipeNutritionInput r = recipes.findNutritionInput(c, recipeId)
                .orElseThrow(() -> new IllegalArgumentException("Recipe missing or inactive"));
        if (r.mealType() != type) {
            throw new IllegalArgumentException("Recipe does not belong to the selected meal type");
        }
        return r;
    }

    public static NutritionFacts snapshot(MealEntry e) {
        return new NutritionFacts(e.getCaloriesKcal(), e.getProteinG(), e.getCarbsG(),
                e.getFatG(), e.getFiberG());
    }

    private static void putFacts(MealEntry e, NutritionFacts f) {
        e.setCaloriesKcal(f.caloriesKcal());
        e.setProteinG(f.proteinG());
        e.setCarbsG(f.carbsG());
        e.setFatG(f.fatG());
        e.setFiberG(f.fiberG());
    }

    public static BigDecimal validServings(BigDecimal servings) {
        if (servings == null || servings.signum() <= 0 ||
                servings.compareTo(new BigDecimal("999999.99")) > 0) {
            throw new IllegalArgumentException("Servings must be between 0.01 and 999999.99");
        }
        try {
            BigDecimal valid = servings.setScale(2, RoundingMode.UNNECESSARY);
            if (valid.signum() <= 0) throw new IllegalArgumentException("Servings must be positive");
            return valid;
        } catch (ArithmeticException e) {
            throw new IllegalArgumentException("Servings support up to two decimal places");
        }
    }

    private static void checkUser(long userId) {
        if (userId <= 0) throw new SecurityException("Login required");
    }
    private static void checkId(long id) {
        if (id <= 0) throw new IllegalArgumentException("Invalid ID");
    }
}
