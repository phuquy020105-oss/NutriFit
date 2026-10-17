package com.nutrifit.model;

/** Bảng: workoutgoals */
public class WorkoutGoal {
    private long goalId;
    private long userId;
    private int weeklySessionsTarget;
    private int weeklyDurationTarget;

    public WorkoutGoal() {}

    public long getGoalId() { return goalId; }
    public void setGoalId(long goalId) { this.goalId = goalId; }

    public long getUserId() { return userId; }
    public void setUserId(long userId) { this.userId = userId; }

    public int getWeeklySessionsTarget() { return weeklySessionsTarget; }
    public void setWeeklySessionsTarget(int weeklySessionsTarget) { this.weeklySessionsTarget = weeklySessionsTarget; }

    public int getWeeklyDurationTarget() { return weeklyDurationTarget; }
    public void setWeeklyDurationTarget(int weeklyDurationTarget) { this.weeklyDurationTarget = weeklyDurationTarget; }
}
