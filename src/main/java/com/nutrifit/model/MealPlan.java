package com.nutrifit.model;

import java.time.LocalDate;
import java.time.LocalDateTime;

public class MealPlan {

    // 1. Attributes
    private Long planId;
    private Long userId;
    private LocalDate planDate;
    private LocalDateTime createdAt;

    // 2. No-argument constructor
    public MealPlan() {
    }

    // 3. Constructor for creating a new meal plan
    public MealPlan(Long userId, LocalDate planDate) {
        this.userId = userId;
        this.planDate = planDate;
    }

    // 4. Constructor for a complete meal plan
    public MealPlan(Long planId, Long userId,
                    LocalDate planDate, LocalDateTime createdAt) {
        this.planId = planId;
        this.userId = userId;
        this.planDate = planDate;
        this.createdAt = createdAt;
    }

    // 5. Getters and Setters
    public Long getPlanId() {
        return planId;
    }

    public void setPlanId(Long planId) {
        this.planId = planId;
    }

    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public LocalDate getPlanDate() {
        return planDate;
    }

    public void setPlanDate(LocalDate planDate) {
        this.planDate = planDate;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
