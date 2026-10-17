package com.nutrifit.model;

import java.time.LocalDate;

/** Bảng: workoutlogs */
public class WorkoutLog {
    private long logId;
    private long userId;
    private long workoutId;
    private Long planDetailId;
    private LocalDate loggedDate;
    private int durationMinutes;
    private double metValue;
    private double estimatedCalories;

    public WorkoutLog() {}

    public long getLogId() { return logId; }
    public void setLogId(long logId) { this.logId = logId; }

    public long getUserId() { return userId; }
    public void setUserId(long userId) { this.userId = userId; }

    public long getWorkoutId() { return workoutId; }
    public void setWorkoutId(long workoutId) { this.workoutId = workoutId; }

    public Long getPlanDetailId() { return planDetailId; }
    public void setPlanDetailId(Long planDetailId) { this.planDetailId = planDetailId; }

    public LocalDate getLoggedDate() { return loggedDate; }
    public void setLoggedDate(LocalDate loggedDate) { this.loggedDate = loggedDate; }

    public int getDurationMinutes() { return durationMinutes; }
    public void setDurationMinutes(int durationMinutes) { this.durationMinutes = durationMinutes; }

    public double getMetValue() { return metValue; }
    public void setMetValue(double metValue) { this.metValue = metValue; }

    public double getEstimatedCalories() { return estimatedCalories; }
    public void setEstimatedCalories(double estimatedCalories) { this.estimatedCalories = estimatedCalories; }
}
