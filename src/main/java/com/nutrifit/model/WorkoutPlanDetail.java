package com.nutrifit.model;

/** Bảng: workoutplandetails */
public class WorkoutPlanDetail {
    private long detailId;
    private long planDayId;
    private long workoutId;
    private int durationMinutes;
    private int orderIndex;

    public WorkoutPlanDetail() {}

    public long getDetailId() { return detailId; }
    public void setDetailId(long detailId) { this.detailId = detailId; }

    public long getPlanDayId() { return planDayId; }
    public void setPlanDayId(long planDayId) { this.planDayId = planDayId; }

    public long getWorkoutId() { return workoutId; }
    public void setWorkoutId(long workoutId) { this.workoutId = workoutId; }

    public int getDurationMinutes() { return durationMinutes; }
    public void setDurationMinutes(int durationMinutes) { this.durationMinutes = durationMinutes; }

    public int getOrderIndex() { return orderIndex; }
    public void setOrderIndex(int orderIndex) { this.orderIndex = orderIndex; }
}
