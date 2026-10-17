package com.nutrifit.model;

/** Bảng: workoutcategories */
public class WorkoutCategory {
    private long categoryId;
    private String categoryName;
    private String iconName;

    public WorkoutCategory() {}

    public long getCategoryId() { return categoryId; }
    public void setCategoryId(long categoryId) { this.categoryId = categoryId; }

    public String getCategoryName() { return categoryName; }
    public void setCategoryName(String categoryName) { this.categoryName = categoryName; }

    public String getIconName() { return iconName; }
    public void setIconName(String iconName) { this.iconName = iconName; }
}
