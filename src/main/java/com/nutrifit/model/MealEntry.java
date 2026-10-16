
package com.nutrifit.model;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public class MealEntry {

    // 1. Meal types supported by the database
    public enum MealType {
        BREAKFAST,
        LUNCH,
        DINNER
    }

    // 2. Attributes
    private Long entryId;
    private Long planId;
    private Long recipeId;
    private String recipeNameSnapshot;
    private MealType mealType;
    private BigDecimal servings;

    // Nutritional snapshots
    private BigDecimal caloriesKcal;
    private BigDecimal proteinG;
    private BigDecimal carbsG;
    private BigDecimal fatG;
    private BigDecimal fiberG;

    private LocalDateTime recordedAt;

    // 3. No-argument constructor
    public MealEntry() {
    }

    // 4. Constructor for creating a new meal entry
    public MealEntry(
            Long planId,
            Long recipeId,
            String recipeNameSnapshot,
            MealType mealType,
            BigDecimal servings,
            BigDecimal caloriesKcal,
            BigDecimal proteinG,
            BigDecimal carbsG,
            BigDecimal fatG,
            BigDecimal fiberG
    ) {
        this.planId = planId;
        this.recipeId = recipeId;
        this.recipeNameSnapshot = recipeNameSnapshot;
        this.mealType = mealType;
        this.servings = servings;
        this.caloriesKcal = caloriesKcal;
        this.proteinG = proteinG;
        this.carbsG = carbsG;
        this.fatG = fatG;
        this.fiberG = fiberG;
    }

    // 5. Constructor for an existing database record
    public MealEntry(
            Long entryId,
            Long planId,
            Long recipeId,
            String recipeNameSnapshot,
            MealType mealType,
            BigDecimal servings,
            BigDecimal caloriesKcal,
            BigDecimal proteinG,
            BigDecimal carbsG,
            BigDecimal fatG,
            BigDecimal fiberG,
            LocalDateTime recordedAt
    ) {
        this(
            planId,
            recipeId,
            recipeNameSnapshot,
            mealType,
            servings,
            caloriesKcal,
            proteinG,
            carbsG,
            fatG,
            fiberG
        );

        this.entryId = entryId;
        this.recordedAt = recordedAt;
    }

    // 6. Getters and Setters
    public Long getEntryId() {
        return entryId;
    }

    public void setEntryId(Long entryId) {
        this.entryId = entryId;
    }

    public Long getPlanId() {
        return planId;
    }

    public void setPlanId(Long planId) {
        this.planId = planId;
    }

    public Long getRecipeId() {
        return recipeId;
    }

    public void setRecipeId(Long recipeId) {
        this.recipeId = recipeId;
    }

    public String getRecipeNameSnapshot() {
        return recipeNameSnapshot;
    }

    public void setRecipeNameSnapshot(String recipeNameSnapshot) {
        this.recipeNameSnapshot = recipeNameSnapshot;
    }

    public MealType getMealType() {
        return mealType;
    }

    public void setMealType(MealType mealType) {
        this.mealType = mealType;
    }

    public BigDecimal getServings() {
        return servings;
    }

    public void setServings(BigDecimal servings) {
        this.servings = servings;
    }

    public BigDecimal getCaloriesKcal() {
        return caloriesKcal;
    }

    public void setCaloriesKcal(BigDecimal caloriesKcal) {
        this.caloriesKcal = caloriesKcal;
    }

    public BigDecimal getProteinG() {
        return proteinG;
    }

    public void setProteinG(BigDecimal proteinG) {
        this.proteinG = proteinG;
    }

    public BigDecimal getCarbsG() {
        return carbsG;
    }

    public void setCarbsG(BigDecimal carbsG) {
        this.carbsG = carbsG;
    }

    public BigDecimal getFatG() {
        return fatG;
    }

    public void setFatG(BigDecimal fatG) {
        this.fatG = fatG;
    }

    public BigDecimal getFiberG() {
        return fiberG;
    }

    public void setFiberG(BigDecimal fiberG) {
        this.fiberG = fiberG;
    }

    public LocalDateTime getRecordedAt() {
        return recordedAt;
    }

    public void setRecordedAt(LocalDateTime recordedAt) {
        this.recordedAt = recordedAt;
    }
}
