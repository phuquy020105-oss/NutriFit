package com.nutrifit.dto;

import com.nutrifit.model.MealEntry;
import com.nutrifit.model.MealPlan;
import java.time.LocalDate;
import java.util.List;

public record DaySummary(LocalDate date, MealPlan plan, List<MealEntry> entries, NutritionFacts total) {
    public DaySummary { entries = List.copyOf(entries); }
}
