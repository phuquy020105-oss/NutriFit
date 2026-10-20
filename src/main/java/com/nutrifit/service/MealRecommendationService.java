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
    private final MealPlanScorer scorer = new MealPlanScorer();

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
        return recommendDay(userId, previous, previous==null?List.of():List.of(recipeIds(previous)));
    }

    public MealSuggestion recommendDay(long userId, MealSuggestion previous, List<List<Long>> recent) throws SQLException {
        requireUser(userId);
        if (recent==null || recent.size()>5) throw new IllegalArgumentException("At most five recent combinations required");
        if (previous != null && previous.userId() != userId) throw new SecurityException("Preview owner mismatch");
        try (var timing = com.nutrifit.observability.Performance.scope("recommend");
             Connection c = connections.open()) {
            BigDecimal target = target(c, userId);
            Eligibility eligibility = eligibility(c, userId);
            List<RecipeCandidate> catalog = recipes.listCandidates(c);
            LocalDate day = LocalDate.now(clock);
            List<MealEntry> journal = journal(c, userId, day);
            NutritionFacts recorded = recorded(journal);
            NutritionGoal goal = users.findGoal(c, userId);
            Map<Long,Integer> frequency = new HashMap<>();
            for (RecipeCandidate recipe:catalog) for(long id:recipe.foodIds()) frequency.merge(id,1,Integer::sum);
            Map<MealType, List<Option>> options = new EnumMap<>(MealType.class);
            for (MealType type : MealType.values()) {
                List<Option> choices = eligible(catalog, type, eligibility).stream()
                        .map(r -> new Option(r, addedFacts(r, journal))).toList();
                if (choices.isEmpty()) throw unavailable(type);
                options.put(type, choices);
            }
            Combination best = null, alternative = null, novel = null;
            Combination bestInRange = null, alternativeInRange = null, novelInRange = null;
            boolean energyFeasible = false;
            BigDecimal feasibilityDistance = target.multiply(new BigDecimal("0.10"));
            BigDecimal rankingDistance = target.multiply(new BigDecimal("0.15"));
            for (Option breakfast : options.get(MealType.BREAKFAST))
                for (Option lunch : options.get(MealType.LUNCH))
                    for (Option dinner : options.get(MealType.DINNER)) {
                        Combination choice = combination(breakfast,lunch,dinner,recorded,target,goal,eligibility,
                                frequency,journal,recent);
                        // A practical energy option must not lose to a large deficit for a small soft-score gain.
                        if (choice.energyDistance().compareTo(feasibilityDistance) <= 0) energyFeasible = true;
                        if (choice.energyDistance().compareTo(rankingDistance) <= 0) {
                            if (bestInRange == null || choice.compareTo(bestInRange) < 0) bestInRange = choice;
                            if (previous != null && !choice.sameRecipes(previous)
                                    && (alternativeInRange == null || choice.compareTo(alternativeInRange) < 0)) alternativeInRange = choice;
                            if (!recent.contains(choice.ids()) && (novelInRange == null || choice.compareTo(novelInRange) < 0)) novelInRange = choice;
                        }
                        if (best == null || choice.compareTo(best) < 0) best = choice;
                        if (previous != null && !choice.sameRecipes(previous)
                                && (alternative == null || choice.compareTo(alternative) < 0)) alternative = choice;
                        if (!recent.contains(choice.ids()) && (novel==null || choice.compareTo(novel)<0)) novel=choice;
                    }
            // Same eligibility, dislikes, servings and score weights. If a <=10% option exists,
            // rank and regenerate within15%; otherwise retain the honest catalog-limited fallback.
            if (energyFeasible) {
                best = bestInRange; alternative = alternativeInRange; novel = novelInRange;
            }
            // Prefer novelty only within a small quality margin; never force a much worse menu.
            if (previous!=null && novel!=null && novel.score()<=best.score()+.03) best=novel;
            else if (alternative!=null && alternative.score()<=best.score()+.03) best=alternative;
            List<SuggestedMeal> meals = new ArrayList<>();
            Map<Long,RecipeNutritionInput> selectedInputs = recipes.findNutritionInputs(c, best.ids());
            for (Option option : List.of(best.breakfast(), best.lunch(), best.dinner())) {
                RecipeNutritionInput input = requireRecipe(selectedInputs, option.recipe().recipeId(), option.recipe().mealType(), eligibility);
                meals.add(new SuggestedMeal(input.recipeId(), input.name(), input.mealType(), STANDARD_SERVINGS,
                        calculator.calculate(input, STANDARD_SERVINGS),input.imageUrl()));
            }
            return preview(userId, day, target, eligibility.premium(), meals, journal);
        }
    }

    /** Read-only replacement of one server-owned preview slot; never persists an entry.
     * Recent IDs belong to this draft and slot. Exhaustion retains the existing menu.
     */
    public MealSuggestion swap(long userId, MealSuggestion draft, MealType type, List<Long> recent)
            throws SQLException {
        requireUser(userId);
        validateDraft(userId, draft, Map.of());
        if (type == null || recent == null || recent.size() > 30)
            throw new IllegalArgumentException("Invalid swap filters");
        try (var timing = com.nutrifit.observability.Performance.scope("swap");
             Connection c = connections.open()) {
            MealSuggestion current = refresh(c, userId, draft, Map.of());
            Eligibility access = eligibility(c, userId);
            List<RecipeCandidate> catalog = recipes.listCandidates(c);
            NutritionGoal goal = users.findGoal(c, userId);
            List<MealEntry> journal = journal(c, userId, current.date());
            SuggestedMeal old = current.meals().stream().filter(m -> m.mealType() == type).findFirst().orElseThrow();
            Set<Long> occupied = new HashSet<>(recipeIds(current));
            Map<Long,Integer> frequency = new HashMap<>();
            for (var r : catalog) for (long id : r.foodIds()) frequency.merge(id, 1, Integer::sum);
            double beforeQuality = menuQuality(current, catalog, access, goal, frequency);
            double beforeGap = current.projectedDifferenceKcal().abs().doubleValue();
            double target = current.targetKcal().doubleValue();
            List<SwapChoice> choices = new ArrayList<>();
            for (var candidate : eligible(catalog, type, access)) {
                if (occupied.contains(candidate.recipeId())) continue;
                double energy = relative(candidate.perServing().caloriesKcal(), old.nutrition().caloriesKcal(), 1);
                if (energy > .35 + 1e-12) continue; // Larger differences are not called equivalent.
                double oldFat = old.nutrition().fatG().doubleValue();
                if (candidate.perServing().fatG().doubleValue() > oldFat + Math.max(10, .50*oldFat)) continue;
                // listCandidates already calculates every public recipe with NutritionCalculator in one query.
                // Score alternatives from that same snapshot, then revalidate only the chosen replacement.
                SuggestedMeal replacement = new SuggestedMeal(candidate.recipeId(), candidate.name(), type, STANDARD_SERVINGS,
                        candidate.perServing().rounded(), candidate.imageUrl());
                List<SuggestedMeal> meals = current.meals().stream().map(m -> m.mealType() == type ? replacement : m).toList();
                MealSuggestion next = preview(userId, current.date(), current.targetKcal(), access.premium(), meals, journal);
                double nextGap = next.projectedDifferenceKcal().abs().doubleValue();
                // Assess the actual projected journal, including old snapshots when the same dish merges.
                if (nextGap > Math.max(beforeGap, .15*target) + .03*target) continue;
                double quality = menuQuality(next, catalog, access, goal, frequency);
                if (quality > beforeQuality + .06) continue;
                double similarity = .35*energy
                        + .20*relative(replacement.nutrition().proteinG(), old.nutrition().proteinG(), 10)
                        + .20*relative(replacement.nutrition().carbsG(), old.nutrition().carbsG(), 15)
                        + .15*relative(replacement.nutrition().fatG(), old.nutrition().fatG(), 5)
                        + .10*relative(replacement.nutrition().fiberG(), old.nutrition().fiberG(), 3);
                double missedLikes = access.likes().isEmpty() ? 0 : 1 - (double)candidate.foodIds().stream()
                        .filter(access.likes()::contains).count()/access.likes().size();
                int tier = energy <= .15 + 1e-12 ? 0 : energy <= .25 + 1e-12 ? 1 : 2;
                choices.add(new SwapChoice(next, candidate.recipeId(), tier,
                        .60*similarity + .37*quality + .03*missedLikes));
            }
            if (choices.isEmpty()) return current;
            choices.sort(Comparator.comparingInt(SwapChoice::tier).thenComparingDouble(SwapChoice::score)
                    .thenComparingLong(SwapChoice::id));
            SwapChoice best = choices.getFirst();
            // Novelty cannot expand the energy tier or hide a material quality loss.
            MealSuggestion selected = choices.stream().filter(v -> v.tier() == best.tier() && v.score() <= best.score() + .08
                    && !recent.contains(v.id())).findFirst().map(SwapChoice::suggestion).orElse(current);
            if (selected == current) return current;
            SuggestedMeal replacement = selected.meals().stream().filter(m -> m.mealType() == type).findFirst().orElseThrow();
            RecipeNutritionInput checked = requireRecipe(c, replacement.recipeId(), type, access);
            NutritionFacts checkedFacts = calculator.calculate(checked, STANDARD_SERVINGS);
            if (!checkedFacts.equals(replacement.nutrition().rounded())) {
                throw unavailable(type); // Catalog changed while scoring; never silently use stale nutrition.
            }
            SuggestedMeal finalMeal = new SuggestedMeal(checked.recipeId(), checked.name(), type, STANDARD_SERVINGS,
                    checkedFacts, checked.imageUrl());
            return preview(userId, selected.date(), selected.targetKcal(), access.premium(),
                    selected.meals().stream().map(m -> m.mealType() == type ? finalMeal : m).toList(), journal);
        }
    }

    /** Floors prevent a zero/near-zero nutrient from producing NaN or an infinite similarity penalty. */
    static double relative(BigDecimal candidate, BigDecimal original, double floor) {
        return candidate.subtract(original).abs().doubleValue()/Math.max(floor, original.doubleValue());
    }
    private record SwapChoice(MealSuggestion suggestion, long id, int tier, double score) { }
    private double menuQuality(MealSuggestion menu, List<RecipeCandidate> catalog, Eligibility access,
            NutritionGoal goal, Map<Long,Integer> frequency) {
        Set<Long> ids = new HashSet<>(recipeIds(menu));
        List<RecipeCandidate> selected = catalog.stream().filter(r -> ids.contains(r.recipeId()))
                .sorted(Comparator.comparing(RecipeCandidate::mealType)).toList();
        Set<Long> foods = new HashSet<>(); for (var r : selected) foods.addAll(r.foodIds());
        double missed = access.likes().isEmpty() ? 0 : 1 - (double)foods.stream()
                .filter(access.likes()::contains).count()/access.likes().size();
        return scorer.evaluate(menu.projectedDay(), menu.targetKcal(), goal,
                menu.meals().stream().map(SuggestedMeal::nutrition).toList(),
                MealPlanScorer.ingredientOverlap(selected, frequency), 0, missed).total();
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
        Map<Long,RecipeNutritionInput> selectedInputs = recipes.findNutritionInputs(c, recipeIds(draft));
        for (SuggestedMeal meal : draft.meals()) {
            BigDecimal servings = STANDARD_SERVINGS;
            RecipeNutritionInput input = requireRecipe(selectedInputs, meal.recipeId(), meal.mealType(), eligibility);
            meals.add(new SuggestedMeal(input.recipeId(), input.name(), input.mealType(), servings,
                    calculator.calculate(input, servings),input.imageUrl()));
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
        List<RecipeCandidate> valid = eligible(catalog,type,eligibility);
        return valid.stream().map(r -> {
            double missed=eligibility.likes().isEmpty()?0:1-(double)r.foodIds().stream()
                    .filter(eligibility.likes()::contains).count()/eligibility.likes().size();
            double score=scorer.evaluate(r.perServing(),mealTarget.max(BigDecimal.ONE),NutritionGoal.MAINTAIN,
                    List.of(r.perServing()),0,0,missed).total();
            return new RecommendedRecipe(r,1-score,"Cân bằng dinh dưỡng từ catalog và sở thích hiện hành");
        }).sorted(Comparator.comparingDouble(RecommendedRecipe::score).reversed()
                .thenComparingLong(r->r.recipe().recipeId())).toList();
    }

    private static List<RecipeCandidate> eligible(List<RecipeCandidate> catalog,MealType type,Eligibility eligibility) {
        return catalog.stream().filter(r->r.mealType()==type && r.perServing().caloriesKcal().signum()>0
                && Collections.disjoint(r.foodIds(),eligibility.dislikes())).sorted(Comparator.comparingLong(RecipeCandidate::recipeId)).toList();
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

    private NutritionFacts addedFacts(RecipeCandidate recipe, List<MealEntry> journal) {
        for (MealEntry old:journal) if(old.getRecipeId()==recipe.recipeId() && old.getMealType()==recipe.mealType()) {
            NutritionFacts merged=calculator.rescaleStored(MealPlannerService.snapshot(old),old.getServings(),
                    old.getServings().add(BigDecimal.ONE));
            return new NutritionFacts(merged.caloriesKcal().subtract(old.getCaloriesKcal()),
                    merged.proteinG().subtract(old.getProteinG()),merged.carbsG().subtract(old.getCarbsG()),
                    merged.fatG().subtract(old.getFatG()),merged.fiberG().subtract(old.getFiberG()));
        }
        return recipe.perServing();
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
        return new MealSuggestion(userId, day, target, premium, meals, recorded(journal), projected.rounded(), journal.size(),
                scorer.warnings(projected,target));
    }

    public static List<Long> recipeIds(MealSuggestion suggestion) {
        return suggestion.meals().stream().sorted(Comparator.comparing(SuggestedMeal::mealType)).map(SuggestedMeal::recipeId).toList();
    }
    private record Option(RecipeCandidate recipe, NutritionFacts added) { }
    private record Combination(Option breakfast,Option lunch,Option dinner,double score,BigDecimal energyDistance)
            implements Comparable<Combination> {
        List<Long> ids(){return List.of(breakfast.recipe().recipeId(),lunch.recipe().recipeId(),dinner.recipe().recipeId());}
        boolean sameRecipes(MealSuggestion previous){return ids().equals(recipeIds(previous));}
        @Override public int compareTo(Combination other) {
            int result=Double.compare(score,other.score);
            if(result==0) result=energyDistance.compareTo(other.energyDistance);
            for(int i=0;result==0 && i<3;i++) result=Long.compare(ids().get(i),other.ids().get(i));
            return result;
        }
    }
    private Combination combination(Option breakfast,Option lunch,Option dinner,NutritionFacts recorded,
            BigDecimal target,NutritionGoal goal,Eligibility eligibility,Map<Long,Integer> frequency,
            List<MealEntry> journal,List<List<Long>> recent) {
        List<RecipeCandidate> selected=List.of(breakfast.recipe(),lunch.recipe(),dinner.recipe());
        NutritionFacts projected=recorded.add(breakfast.added()).add(lunch.added()).add(dinner.added());
        Set<Long> foods=new HashSet<>();for(var r:selected)foods.addAll(r.foodIds());
        double missed=eligibility.likes().isEmpty()?0:1-(double)foods.stream().filter(eligibility.likes()::contains).count()/eligibility.likes().size();
        int repeats=0;
        for(var r:selected) {
            if(journal.stream().anyMatch(e->e.getRecipeId()==r.recipeId()))repeats++;
            for(var old:recent)if(old.contains(r.recipeId()))repeats++;
        }
        double repeated=(double)repeats/(3*(recent.size()+1));
        var score=scorer.evaluate(projected,target,goal,selected.stream().map(RecipeCandidate::perServing).toList(),
                MealPlanScorer.ingredientOverlap(selected,frequency),repeated,missed);
        return new Combination(breakfast,lunch,dinner,score.total(),projected.caloriesKcal().subtract(target).abs());
    }

    private RecipeNutritionInput requireRecipe(Connection c, long id, MealType type, Eligibility eligibility)
            throws SQLException {
        RecipeNutritionInput input = recipes.findNutritionInput(c, id).orElseThrow(() -> unavailable(type));
        if (input.mealType() != type || input.ingredients().stream()
                .anyMatch(line -> eligibility.dislikes().contains(line.foodId()))) throw unavailable(type);
        return input;
    }

    private RecipeNutritionInput requireRecipe(Map<Long,RecipeNutritionInput> inputs, long id, MealType type, Eligibility eligibility) {
        RecipeNutritionInput input = inputs.get(id);
        if (input == null || input.mealType() != type || input.ingredients().stream()
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
