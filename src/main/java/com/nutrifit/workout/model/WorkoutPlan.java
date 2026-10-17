package com.nutrifit.model;

import java.time.LocalDate;

/** Bảng: workoutplans */
public class WorkoutPlan {
    private long planId;
    private long userId;
    private String planName;
    private LocalDate startDate;
    private LocalDate endDate;
    private boolean active;

    public WorkoutPlan() {}

    public long getPlanId() { return planId; }
    public void setPlanId(long planId) { this.planId = planId; }

    public long getUserId() { return userId; }
    public void setUserId(long userId) { this.userId = userId; }

    public String getPlanName() { return planName; }
    public void setPlanName(String planName) { this.planName = planName; }

    public LocalDate getStartDate() { return startDate; }
    public void setStartDate(LocalDate startDate) { this.startDate = startDate; }

    public LocalDate getEndDate() { return endDate; }
    public void setEndDate(LocalDate endDate) { this.endDate = endDate; }

    public boolean isActive() { return active; }
    public void setActive(boolean active) { this.active = active; }
}
