package com.nutrifit.service;

import com.nutrifit.dto.*;
import com.nutrifit.model.*;
import java.math.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class RealCatalogBenchmarkTest {
    static final BigDecimal ONE=new BigDecimal("1.00");
    static final MealPlanScorer SCORER=new MealPlanScorer();
    static MealRecommendationServiceTest.Fixture fixture(List<RecipeNutritionInput> data) {
        var f=new MealRecommendationServiceTest.Fixture();f.inputs.clear();data.forEach(r->f.inputs.put(r.recipeId(),r));return f;
    }
    static List<RecipeCandidate> candidates(MealRecommendationServiceTest.Fixture f)throws Exception{return f.recipes.listCandidates(f.connection);}
    static Set<Long> likes(MealRecommendationServiceTest.Fixture f){
        Set<Long> result=new HashSet<>();if(f.premium)f.saved.stream().filter(p->p.getType()==FoodPreference.PreferenceType.LIKE).forEach(p->result.add(p.getFoodId()));return result;
    }
    static NutritionFacts added(RecipeCandidate r,MealRecommendationServiceTest.Fixture f){
        for(var old:f.journal)if(old.getRecipeId()==r.recipeId()&&old.getMealType()==r.mealType()){
            var a=new NutritionCalculator().rescaleStored(MealPlannerService.snapshot(old),old.getServings(),old.getServings().add(ONE));
            return new NutritionFacts(a.caloriesKcal().subtract(old.getCaloriesKcal()),a.proteinG().subtract(old.getProteinG()),a.carbsG().subtract(old.getCarbsG()),a.fatG().subtract(old.getFatG()),a.fiberG().subtract(old.getFiberG()));
        }return r.perServing();
    }
    static NutritionFacts projected(List<RecipeCandidate> rows,MealRecommendationServiceTest.Fixture f){
        var sum=NutritionFacts.ZERO;for(var e:f.journal)sum=sum.add(MealPlannerService.snapshot(e));for(var r:rows)sum=sum.add(added(r,f));return sum;
    }
    record OldChoice(List<RecipeCandidate> rows,int band,long likes,BigDecimal distance,BigDecimal balance) implements Comparable<OldChoice>{
        public int compareTo(OldChoice o){int n=Integer.compare(band,o.band);if(n==0)n=Long.compare(o.likes,likes);if(n==0)n=distance.compareTo(o.distance);if(n==0)n=balance.compareTo(o.balance);for(int i=0;n==0&&i<3;i++)n=Long.compare(rows.get(i).recipeId(),o.rows.get(i).recipeId());return n;}
    }
    // Exact ranking policy at a3ab60b: 10% energy band, LIKE count, distance, meal balance, IDs.
    static MealSuggestion legacy(MealRecommendationServiceTest.Fixture f)throws Exception{
        var all=candidates(f);Set<Long> no=new HashSet<>();if(f.premium)f.saved.stream().filter(p->p.getType()==FoodPreference.PreferenceType.DISLIKE).forEach(p->no.add(p.getFoodId()));
        var b=all.stream().filter(r->r.mealType()==MealEntry.MealType.BREAKFAST&&Collections.disjoint(r.foodIds(),no)).toList();
        var l=all.stream().filter(r->r.mealType()==MealEntry.MealType.LUNCH&&Collections.disjoint(r.foodIds(),no)).toList();
        var d=all.stream().filter(r->r.mealType()==MealEntry.MealType.DINNER&&Collections.disjoint(r.foodIds(),no)).toList();
        OldChoice best=null;var liked=likes(f);
        for(var breakfast:b)for(var lunch:l)for(var dinner:d){
            var rows=List.of(breakfast,lunch,dinner);var distance=projected(rows,f).caloriesKcal().subtract(f.target).abs();
            int band=distance.divide(f.target.max(BigDecimal.ONE).multiply(new BigDecimal(".1")),0,RoundingMode.DOWN).intValueExact();
            long count=rows.stream().mapToLong(r->r.foodIds().stream().filter(liked::contains).count()).sum();
            var total=rows.stream().map(r->r.perServing().caloriesKcal()).reduce(BigDecimal.ZERO,BigDecimal::add);
            var balance=breakfast.perServing().caloriesKcal().subtract(total.multiply(new BigDecimal(".25"))).abs().add(lunch.perServing().caloriesKcal().subtract(total.multiply(new BigDecimal(".40"))).abs());
            var choice=new OldChoice(rows,band,count,distance,balance);if(best==null||choice.compareTo(best)<0)best=choice;
        }
        var meals=best.rows.stream().map(r->new SuggestedMeal(r.recipeId(),r.name(),r.mealType(),ONE,r.perServing())).toList();
        return f.service.refresh(MealRecommendationServiceTest.USER,new MealSuggestion(MealRecommendationServiceTest.USER,java.time.LocalDate.now(MealRecommendationServiceTest.CLOCK),f.target,f.premium,meals),MealRecommendationServiceTest.amounts("1"));
    }
    static double cost(MealSuggestion s,MealRecommendationServiceTest.Fixture f)throws Exception{
        var all=candidates(f);Map<Long,Integer> frequency=new HashMap<>();for(var r:all)for(long id:r.foodIds())frequency.merge(id,1,Integer::sum);
        var rows=all.stream().filter(r->MealRecommendationService.recipeIds(s).contains(r.recipeId())).sorted(Comparator.comparing(RecipeCandidate::mealType)).toList();
        var union=new HashSet<Long>();rows.forEach(r->union.addAll(r.foodIds()));var liked=likes(f);
        double missed=liked.isEmpty()?0:1-(double)union.stream().filter(liked::contains).count()/liked.size();
        double repeated=rows.stream().filter(r->f.journal.stream().anyMatch(e->e.getRecipeId()==r.recipeId())).count()/3.0;
        return SCORER.evaluate(s.projectedDay(),f.target,f.goal,rows.stream().map(RecipeCandidate::perServing).toList(),MealPlanScorer.ingredientOverlap(rows,frequency),repeated,missed).total();
    }
    static String csv(String label,String algorithm,MealSuggestion s,double score){
        var n=s.projectedDay();double k=n.caloriesKcal().doubleValue();
        return String.format(Locale.ROOT,"%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%.6f,%.6f,%.6f%n",label,algorithm,s.targetKcal(),MealRecommendationService.recipeIds(s).toString().replace(",","/").replace(" ",""),n.caloriesKcal(),n.proteinG(),n.carbsG(),n.fatG(),n.fiberG(),s.projectedDifferenceKcal(),9*n.fatG().doubleValue()/k,1000*n.fiberG().doubleValue()/k,score);
    }
    @Test void benchmarkCommittedDataAcrossExistingProfileTargetsAndPreferences()throws Exception{
        var data=RealCatalog.load();assertEquals(60,data.size());assertEquals(607,data.stream().mapToInt(r->r.ingredients().size()).sum());
        List<String> lines=new ArrayList<>();lines.add("case,algorithm,target,recipe_ids,kcal,protein_g,carbs_g,fat_g,fiber_g,difference_kcal,fat_energy_ratio,fiber_g_per_1000kcal,score\n");
        // Existing OnboardingService outputs for male 30y/70kg/175cm; all five activity levels and goals.
        String[][] targets={{"1678.50","1978.50","2278.50"},{"1967.03","2267.03","2567.03"},{"2255.56","2555.56","2855.56"},{"2544.09","2844.09","3144.09"},{"2832.63","3132.63","3432.63"}};
        int improved=0,changed=0,cases=0;double before=0,after=0;
        for(int a=0;a<targets.length;a++)for(var goal:NutritionGoal.values())for(int pref=0;pref<4;pref++)for(int journal=0;journal<2;journal++){
            var f=fixture(data);f.target=new BigDecimal(targets[a][goal.ordinal()]);f.goal=goal;f.premium=pref>0;
            if(pref==2)f.saved.add(new FoodPreference(MealRecommendationServiceTest.USER,12L,FoodPreference.PreferenceType.LIKE));
            if(pref==3)f.saved.add(new FoodPreference(MealRecommendationServiceTest.USER,18L,FoodPreference.PreferenceType.DISLIKE));
            if(journal==1){var r=data.get(22);var n=new NutritionCalculator().calculate(r,new BigDecimal(".50"));f.journal.add(new MealEntry(10L,r.recipeId(),r.name(),r.mealType(),new BigDecimal(".50"),n.caloriesKcal(),n.proteinG(),n.carbsG(),n.fatG(),n.fiberG()));}
            var old=legacy(f);var now=f.service.recommendDay(MealRecommendationServiceTest.USER);double oldCost=cost(old,f),newCost=cost(now,f);
            assertTrue(newCost<=oldCost+1e-9,"New ranking must minimize the documented objective");
            assertEquals(3,now.meals().size());assertTrue(now.meals().stream().allMatch(m->m.servings().equals(ONE)));
            if(pref==3)assertTrue(now.meals().stream().noneMatch(m->f.inputs.get(m.recipeId()).ingredients().stream().anyMatch(i->i.foodId()==18L)));
            if(!MealRecommendationService.recipeIds(old).equals(MealRecommendationService.recipeIds(now)))changed++;
            if(newCost<oldCost-1e-9)improved++;before+=oldCost;after+=newCost;cases++;
            String label="activity"+a+"_"+goal+"_pref"+pref+"_journal"+journal;
            lines.add(csv(label,"old",old,oldCost));lines.add(csv(label,"new",now,newCost));
        }
        Path out=Path.of("target/nutrition-audit");Files.createDirectories(out);Files.writeString(out.resolve("benchmark.csv"),String.join("",lines));
        String hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(Path.of("database/seed/catalog.json"))));
        Files.writeString(out.resolve("benchmark-summary.txt"),"catalog_sha256="+hash+"\ncases="+cases+"\nchanged="+changed+"\nimproved_score="+improved+"\nold_mean_score="+before/cases+"\nnew_mean_score="+after/cases+"\n");
        assertTrue(improved>0);
    }
    @Test void regenerationAvoidsRecentMenusWithinQualityMarginAndScalesToSixty()throws Exception{
        var data=RealCatalog.load();var f=fixture(data);f.target=new BigDecimal("1600");
        var first=f.service.recommendDay(MealRecommendationServiceTest.USER);List<List<Long>> recent=new ArrayList<>();recent.add(MealRecommendationService.recipeIds(first));
        var second=f.service.recommendDay(MealRecommendationServiceTest.USER,first,recent);
        assertNotEquals(MealRecommendationService.recipeIds(first),MealRecommendationService.recipeIds(second));
        recent.add(MealRecommendationService.recipeIds(second));
        var third=f.service.recommendDay(MealRecommendationServiceTest.USER,second,recent);
        assertFalse(recent.contains(MealRecommendationService.recipeIds(third)));
        // Capacity fixture only: clones are never written to JSON, SQL or a database.
        for(var r:data)f.inputs.put(r.recipeId()+1000,new RecipeNutritionInput(r.recipeId()+1000,r.name(),r.mealType(),r.baseServings(),r.ingredients()));
        assertTimeout(Duration.ofSeconds(10),()->assertEquals(3,f.service.recommendDay(MealRecommendationServiceTest.USER).meals().size()));
    }
}
