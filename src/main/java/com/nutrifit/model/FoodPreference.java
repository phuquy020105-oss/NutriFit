
package com.nutrifit.model;

import java.time.LocalDateTime;

public class FoodPreference {

    // 1. Preference types supported by MySQL
    public enum PreferenceType {
        LIKE,
        DISLIKE
    }

    // 2. Attributes
    private Long preferenceId;
    private Long userId;
    private Long foodId;
    private PreferenceType type;
    private LocalDateTime updatedAt;

    // 3. No-argument constructor
    public FoodPreference() {
    }

    // 4. Constructor for creating a new preference
    public FoodPreference(
            Long userId,
            Long foodId,
            PreferenceType type
    ) {
        this.userId = userId;
        this.foodId = foodId;
        this.type = type;
    }

    // 5. Constructor for an existing database record
    public FoodPreference(
            Long preferenceId,
            Long userId,
            Long foodId,
            PreferenceType type,
            LocalDateTime updatedAt
    ) {
        this.preferenceId = preferenceId;
        this.userId = userId;
        this.foodId = foodId;
        this.type = type;
        this.updatedAt = updatedAt;
    }

    // 6. Getters and Setters
    public Long getPreferenceId() {
        return preferenceId;
    }

    public void setPreferenceId(Long preferenceId) {
        this.preferenceId = preferenceId;
    }

    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public Long getFoodId() {
        return foodId;
    }

    public void setFoodId(Long foodId) {
        this.foodId = foodId;
    }

    public PreferenceType getType() {
        return type;
    }

    public void setType(PreferenceType type) {
        this.type = type;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
}
