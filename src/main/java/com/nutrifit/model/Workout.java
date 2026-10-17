package com.nutrifit.model;

/** Bảng: workouts */
public class Workout {
    private long workoutId;
    private long categoryId;
    private Long createdBy;
    private String workoutName;
    private boolean custom;
    private String accessLevel;
    private String description;
    private String instructions;
    private String muscleGroup;
    private String difficultyLevel;
    private String equipment;
    private String targetGoal;
    private String videoUrl;
    private double metValue;
    private int defaultDurationMinutes;

    public Workout() {}

    public long getWorkoutId() { return workoutId; }
    public void setWorkoutId(long workoutId) { this.workoutId = workoutId; }

    public long getCategoryId() { return categoryId; }
    public void setCategoryId(long categoryId) { this.categoryId = categoryId; }

    public Long getCreatedBy() { return createdBy; }
    public void setCreatedBy(Long createdBy) { this.createdBy = createdBy; }

    public String getWorkoutName() { return workoutName; }
    public void setWorkoutName(String workoutName) { this.workoutName = workoutName; }

    public boolean isCustom() { return custom; }
    public void setCustom(boolean custom) { this.custom = custom; }

    public String getAccessLevel() { return accessLevel; }
    public void setAccessLevel(String accessLevel) { this.accessLevel = accessLevel; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public String getInstructions() { return instructions; }
    public void setInstructions(String instructions) { this.instructions = instructions; }

    public String getMuscleGroup() { return muscleGroup; }
    public void setMuscleGroup(String muscleGroup) { this.muscleGroup = muscleGroup; }

    public String getDifficultyLevel() { return difficultyLevel; }
    public void setDifficultyLevel(String difficultyLevel) { this.difficultyLevel = difficultyLevel; }

    public String getEquipment() { return equipment; }
    public void setEquipment(String equipment) { this.equipment = equipment; }

    public String getTargetGoal() { return targetGoal; }
    public void setTargetGoal(String targetGoal) { this.targetGoal = targetGoal; }

    public String getVideoUrl() { return videoUrl; }
    public void setVideoUrl(String videoUrl) { this.videoUrl = videoUrl; }

    public double getMetValue() { return metValue; }
    public void setMetValue(double metValue) { this.metValue = metValue; }

    public int getDefaultDurationMinutes() { return defaultDurationMinutes; }
    public void setDefaultDurationMinutes(int defaultDurationMinutes) { this.defaultDurationMinutes = defaultDurationMinutes; }
}
