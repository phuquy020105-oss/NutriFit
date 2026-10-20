package com.nutrifit.service;

import com.nutrifit.dao.UserProfileDAO;
import com.nutrifit.dto.*;
import com.nutrifit.model.*;
import java.math.*;
import java.nio.file.*;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Offline cohort A. Uses real onboarding calculations with a capture-only DAO, never JDBC. */
class FoodQualityCohortBenchmarkTest {
    record Adult(String id, String sex, int age, int height, int weight) {}
    static final List<Adult> ADULTS = List.of(
        new Adult("F22", "female", 22, 155, 50), new Adult("F45", "female", 45, 165, 75),
        new Adult("F68", "female", 68, 158, 60), new Adult("M20", "male", 20, 178, 75),
        new Adult("M42", "male", 42, 170, 92), new Adult("M70", "male", 70, 168, 68));
    static final class CapturingProfileDAO extends UserProfileDAO {
        BigDecimal target;
        int calls;
        @Override public void save(long user, String gender, int age, BigDecimal height,
                BigDecimal weight, String activity, String goal, BigDecimal bmr,
                BigDecimal tdee, BigDecimal target, int water) {
            assertTrue(bmr.signum() > 0 && tdee.signum() > 0);
            assertTrue(target.compareTo(new BigDecimal("1200")) >= 0);
            this.target = target; calls++;
        }
    }
    static BigDecimal target(Adult adult, String activity, String goal) throws Exception {
        var service = new OnboardingService();
        var capture = new CapturingProfileDAO();
        // Test-only seam: production OnboardingService and its formula remain byte-for-byte unchanged.
        var dao = OnboardingService.class.getDeclaredField("dao");
        dao.setAccessible(true); dao.set(service, capture);
        service.save(MealRecommendationServiceTest.USER, adult.sex(), Integer.toString(adult.age()),
                Integer.toString(adult.height()), Integer.toString(adult.weight()), activity, goal);
        assertEquals(1, capture.calls);
        assertNotNull(capture.target);
        return capture.target;
    }
    static double minRelativeError(List<RecipeCandidate> eligible,
            MealRecommendationServiceTest.Fixture fixture) {
        var breakfast = eligible.stream().filter(r -> r.mealType() == MealEntry.MealType.BREAKFAST).toList();
        var lunch = eligible.stream().filter(r -> r.mealType() == MealEntry.MealType.LUNCH).toList();
        var dinner = eligible.stream().filter(r -> r.mealType() == MealEntry.MealType.DINNER).toList();
        double best = Double.POSITIVE_INFINITY;
        for (var b : breakfast) for (var l : lunch) for (var d : dinner) {
            double error = RealCatalogBenchmarkTest.projected(List.of(b,l,d), fixture).caloriesKcal()
                    .subtract(fixture.target).abs().doubleValue() / fixture.target.doubleValue();
            best = Math.min(best, error);
        }
        return best;
    }
    static String cell(Object value) { return value.toString().replace(',', '/'); }
    static String line(Object... values) {
        return String.join(",", Arrays.stream(values).map(FoodQualityCohortBenchmarkTest::cell).toList()) + "\n";
    }

    @Test void currentCatalogAcrossAdultProfilesUsesExistingTargetsAndStoredSnapshots() throws Exception {
        benchmark("CURRENT_60_DOCUMENTED_REFERENCES", RealCatalog.load(), "cohort-current");
    }

    private void benchmark(String dataset, List<RecipeNutritionInput> data, String output) throws Exception {
        assertEquals(60, data.size());
        var historicalRecipe = RealCatalog.load().get(22);
        var lines = new ArrayList<String>();
        lines.add("dataset,adult,gender,age,height_cm,weight_kg,activity,goal,subscription_case,journal,target_kcal,success,recipe_ids,projected_kcal,protein_g,available_carbs_g,fat_g,fiber_g,absolute_error_kcal,relative_error,protein_energy_ratio,carb_energy_ratio,fat_energy_ratio,nin_fiber_reference_g,fiber_gap_g,energy_feasible_10pct,best_relative_error,large_error_despite_feasible,unique_food_count,runtime_ms\n");
        int cases=0, success=0, feasible=0, avoidable=0;
        for (var adult : ADULTS) for (String activity : List.of("sedentary", "moderate", "very_high"))
            for (String goal : List.of("lose", "maintain", "gain")) {
                BigDecimal target = target(adult,activity,goal);
                for (int subscription=0; subscription<4; subscription++) for (int journal=0; journal<2; journal++) {
                    cases++;
                    var f = RealCatalogBenchmarkTest.fixture(data);
                    f.target=target; f.goal=NutritionGoal.valueOf(goal.toUpperCase(Locale.ROOT));
                    f.premium=subscription==1 || subscription==2;
                    String scenario = switch(subscription) { case 1 -> "PREMIUM_LIKE"; case 2 -> "PREMIUM_DISLIKE";
                        case 3 -> "EXPIRED_WITH_STORED_DISLIKES"; default -> "FREE_WITH_STORED_DISLIKES"; };
                    if (subscription==1) f.saved.add(new FoodPreference(MealRecommendationServiceTest.USER,12L,FoodPreference.PreferenceType.LIKE));
                    else if (subscription==2) f.saved.add(new FoodPreference(MealRecommendationServiceTest.USER,18L,FoodPreference.PreferenceType.DISLIKE));
                    else for (long id=1; id<=82; id++) f.saved.add(new FoodPreference(MealRecommendationServiceTest.USER,id,FoodPreference.PreferenceType.DISLIKE));
                    if (journal==1) {
                        var old=historicalRecipe; var n=new NutritionCalculator().calculate(old,new BigDecimal(".50"));
                        f.journal.add(new MealEntry(10L,old.recipeId(),old.name(),old.mealType(),new BigDecimal(".50"),
                                n.caloriesKcal(),n.proteinG(),n.carbsG(),n.fatG(),n.fiberG()));
                    }
                    var historical = f.journal.stream().map(MealPlannerService::snapshot).toList();
                    var all=RealCatalogBenchmarkTest.candidates(f);
                    var eligible=all.stream().filter(r -> subscriptionAllowed(r,f)).toList();
                    double best=minRelativeError(eligible,f);
                    boolean possible=best<=.10+1e-12;
                    if (possible) feasible++;
                    long begin=System.nanoTime();
                    var suggestion=f.service.recommendDay(MealRecommendationServiceTest.USER);
                    double millis=(System.nanoTime()-begin)/1_000_000.0;
                    assertEquals(3,suggestion.meals().size());
                    assertEquals(List.of(MealEntry.MealType.values()), suggestion.meals().stream().map(SuggestedMeal::mealType).toList());
                    assertTrue(suggestion.meals().stream().allMatch(m->m.servings().equals(new BigDecimal("1.00"))));
                    assertEquals(historical,f.journal.stream().map(MealPlannerService::snapshot).toList());
                    if (!f.premium) assertEquals(0,f.preferenceReads);
                    Set<Long> foodIds=new HashSet<>();
                    for (var meal:suggestion.meals()) {
                        var input=f.inputs.get(meal.recipeId());
                        assertEquals(new NutritionCalculator().calculate(input,BigDecimal.ONE),meal.nutrition());
                        input.ingredients().forEach(i->foodIds.add(i.foodId()));
                    }
                    if (subscription==2) assertFalse(foodIds.contains(18L));
                    success++;
                    var n=suggestion.projectedDay();
                    double kcal=n.caloriesKcal().doubleValue(), error=Math.abs(kcal-target.doubleValue());
                    double relative=error/target.doubleValue();
                    if (possible) assertTrue(relative<=.15+1e-12,"Feasible cohorts must remain within15% even with LIKE/history");
                    boolean poor=possible && relative>.20;
                    if (poor) avoidable++;
                    double fiberReference=adult.sex().equals("male") ? (adult.age()<50?21:20) : (adult.age()<50?18:17);
                    lines.add(line(dataset,adult.id(),adult.sex(),adult.age(),adult.height(),adult.weight(),activity,goal,scenario,journal,
                            target,true,MealRecommendationService.recipeIds(suggestion),n.caloriesKcal(),n.proteinG(),n.carbsG(),n.fatG(),n.fiberG(),
                            error,relative,4*n.proteinG().doubleValue()/kcal,4*n.carbsG().doubleValue()/kcal,9*n.fatG().doubleValue()/kcal,
                            fiberReference,Math.max(0,fiberReference-n.fiberG().doubleValue()),possible,best,poor,foodIds.size(),millis));
                }
            }
        assertEquals(432,cases); assertEquals(cases,success);
        assertEquals(0,avoidable,"A feasible menu must not lose to a >20% energy gap");
        Path out=Path.of("target/food-quality"); Files.createDirectories(out);
        Files.writeString(out.resolve(output+".csv"),String.join("",lines));
        Files.writeString(out.resolve(output+"-summary.txt"),"dataset="+dataset+"\ncases="+cases+"\nsuccess="+success+
            "\nenergy_feasible_10pct="+feasible+"\nselected_error_over20pct_when_feasible="+avoidable+
            "\nquality="+(avoidable==0?"NO_AVOIDABLE_ENERGY_GAP_OBSERVED":"FAIL_AVOIDABLE_ENERGY_GAP")+
            "\nsource_quality=DOCUMENTED_REFERENCES_INCLUDING_ESTIMATES\n");
    }
    static boolean subscriptionAllowed(RecipeCandidate recipe,MealRecommendationServiceTest.Fixture fixture) {
        return !fixture.premium || fixture.saved.stream().filter(p->p.getType()==FoodPreference.PreferenceType.DISLIKE)
                .noneMatch(p->recipe.foodIds().contains(p.getFoodId()));
    }

    @Test void energyRangeAlsoAppliesToRegenerationAndRecentMenuPreference() throws Exception {
        var f=RealCatalogBenchmarkTest.fixture(RealCatalog.load());
        f.target=target(ADULTS.getFirst(),"very_high","lose");
        f.premium=true;
        f.saved.add(new FoodPreference(MealRecommendationServiceTest.USER,12L,FoodPreference.PreferenceType.LIKE));
        List<List<Long>> recent=new ArrayList<>();
        MealSuggestion previous=null;
        for (int i=0;i<6;i++) {
            var now=f.service.recommendDay(MealRecommendationServiceTest.USER,previous,recent);
            assertTrue(now.projectedDay().caloriesKcal().subtract(f.target).abs()
                    .compareTo(f.target.multiply(new BigDecimal(".15")))<=0,
                    "Novelty must not escape the practical energy pool");
            recent.add(MealRecommendationService.recipeIds(now));
            if (recent.size()>5) recent.removeFirst();
            previous=now;
        }
    }

    @Test void targetsComeFromCurrentOnboardingNotADuplicateFormula() throws Exception {
        var adult=new Adult("existing-reference","male",30,175,70);
        assertEquals(new BigDecimal("1678.50"),target(adult,"sedentary","lose"));
        assertEquals(new BigDecimal("3432.63"),target(adult,"very_high","gain"));
    }
}
