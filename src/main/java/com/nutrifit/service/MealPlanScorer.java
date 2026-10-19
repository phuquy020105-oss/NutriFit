package com.nutrifit.service;

import com.nutrifit.dto.*;
import java.math.BigDecimal;
import java.util.*;

/** Soft adult reference ranges, not clinical constraints. Scores never become stored nutrition.
 * AMDR and fibre reference: Health Canada, reference-values-macronutrients.html.
 */
public final class MealPlanScorer {
    public record Score(double energy, double protein, double carbohydrate, double fat, double fiber,
                        double mealBalance, double diversity, double repetition, double preference) {
        public double total() {
            return .30*energy + .08*protein + .10*carbohydrate + .15*fat + .17*fiber
                    + .05*mealBalance + .06*diversity + .06*repetition + .03*preference;
        }
    }

    public Score evaluate(NutritionFacts projected, BigDecimal target, NutritionGoal goal,
            List<NutritionFacts> meals, double overlap, double repeated, double missedLikes) {
        double kcal = projected.caloriesKcal().doubleValue();
        double targetKcal = target.doubleValue();
        if (targetKcal <= 0) throw new IllegalArgumentException("Positive target required");
        double delta = (kcal-targetKcal)/targetKcal;
        // Goal affects only the direction of energy mismatch; all goals share the same AMDR.
        double directional = ((goal==NutritionGoal.LOSE && delta>0) || (goal==NutritionGoal.GAIN && delta<0)) ? 1.15 : 1;
        double error = Math.abs(delta)*directional;
        double energy = error/(.20+error);
        double denominator = Math.max(kcal, 1);
        double protein = outside(4*projected.proteinG().doubleValue()/denominator,.10,.35);
        double carbs = outside(4*projected.carbsG().doubleValue()/denominator,.45,.65);
        double fat = outside(9*projected.fatG().doubleValue()/denominator,.20,.35);
        double fiber = clamp(1-projected.fiberG().doubleValue()/(.014*targetKcal));
        double mealKcal = meals.stream().mapToDouble(f->f.caloriesKcal().doubleValue()).sum();
        double balance = 0;
        double[] shares = {.25,.40,.35};
        for(int i=0;meals.size()==3 && i<meals.size();i++) balance += Math.abs(meals.get(i).caloriesKcal().doubleValue()/Math.max(mealKcal,1)-shares[i]);
        return new Score(clamp(energy),protein,carbs,fat,fiber,clamp(balance/1.5),
                clamp(overlap),clamp(repeated),clamp(missedLikes));
    }
    private static double outside(double value,double min,double max) {
        return clamp(Math.max(min-value,Math.max(0,value-max))/(max-min));
    }
    private static double clamp(double value) { return Math.max(0,Math.min(1,value)); }

    /** Fixed, safe explanations only; algorithm scores are not shown to the user. */
    public List<String> warnings(NutritionFacts day, BigDecimal target) {
        List<String> messages = new ArrayList<>();
        double kcal=day.caloriesKcal().doubleValue(), denominator=Math.max(kcal,1);
        if (Math.abs(kcal-target.doubleValue())/target.doubleValue()>.15)
            messages.add("Tổng dự kiến còn lệch mục tiêu năng lượng; đây là lựa chọn từ những món hiện có.");
        if (9*day.fatG().doubleValue()/denominator>.35)
            messages.add("Lượng chất béo còn cao so với khoảng tham khảo.");
        if (day.fiberG().doubleValue()<.014*target.doubleValue())
            messages.add("Lượng chất xơ còn thấp so với tham khảo cho cả ngày; cân nhắc thêm rau, đậu hoặc trái cây phù hợp.");
        double protein=4*day.proteinG().doubleValue()/denominator, carbs=4*day.carbsG().doubleValue()/denominator;
        if (protein<.10 || protein>.35 || carbs<.45 || carbs>.65)
            messages.add("Tỷ lệ các nhóm dinh dưỡng còn lệch khoảng tham khảo. Đây là gợi ý từ những món hiện có.");
        return List.copyOf(messages);
    }

    /** Common ingredients contribute less than distinctive ingredients to overlap. */
    public static double ingredientOverlap(List<RecipeCandidate> meals, Map<Long,Integer> frequency) {
        double total=0;int pairs=0;
        for(int i=0;i<meals.size();i++) for(int j=i+1;j<meals.size();j++) {
            Set<Long> union=new HashSet<>(meals.get(i).foodIds());union.addAll(meals.get(j).foodIds());
            double same=0,all=0;
            for(long id:union) {
                double weight=1.0/Math.max(1,frequency.getOrDefault(id,1));all+=weight;
                if(meals.get(i).foodIds().contains(id) && meals.get(j).foodIds().contains(id)) same+=weight;
            }
            total+=all==0?0:same/all;pairs++;
        }
        return pairs==0?0:total/pairs;
    }
}
