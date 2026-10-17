package com.nutrifit.model;

/** Bảng: workoutplandays */
public class WorkoutPlanDay {
    private long planDayId;
    private long planId;
    private int dayIndex;
    private String dayName;
    private String focusArea;
    private boolean restDay;

    public WorkoutPlanDay() {}

    public long getPlanDayId() { return planDayId; }
    public void setPlanDayId(long planDayId) { this.planDayId = planDayId; }

    public long getPlanId() { return planId; }
    public void setPlanId(long planId) { this.planId = planId; }

    public int getDayIndex() { return dayIndex; }
    public void setDayIndex(int dayIndex) { this.dayIndex = dayIndex; }

    public String getDayName() { return dayName; }
    public void setDayName(String dayName) { this.dayName = dayName; }

    public String getFocusArea() { return focusArea; }
    public void setFocusArea(String focusArea) { this.focusArea = focusArea; }

    public boolean isRestDay() { return restDay; }
    public void setRestDay(boolean restDay) { this.restDay = restDay; }
}
