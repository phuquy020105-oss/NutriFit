package com.nutrifit.dto;

import com.nutrifit.model.WorkoutPlan;
import com.nutrifit.model.WorkoutPlanDay;
import com.nutrifit.model.WorkoutPlanDetail;

import java.util.ArrayList;
import java.util.List;

/** Dữ liệu lồng nhau để JSP hiển thị: lộ trình -> các ngày -> các bài tập. */
public class WorkoutPlanView {

    private final WorkoutPlan plan;
    private final List<DayView> days = new ArrayList<>();

    public WorkoutPlanView(WorkoutPlan plan) {
        this.plan = plan;
    }

    public WorkoutPlan getPlan() { return plan; }
    public List<DayView> getDays() { return days; }

    public static class DayView {
        private final WorkoutPlanDay day;
        private final List<ItemView> items = new ArrayList<>();
        private double totalCalories;

        public DayView(WorkoutPlanDay day) { this.day = day; }

        public void addItem(ItemView item) {
            items.add(item);
            totalCalories += item.getCalories();
        }

        public WorkoutPlanDay getDay() { return day; }
        public List<ItemView> getItems() { return items; }
        public double getTotalCalories() { return totalCalories; }
    }

    public static class ItemView {
        private final WorkoutPlanDetail detail;
        private final String workoutName;
        private final double calories;

        public ItemView(WorkoutPlanDetail detail, String workoutName, double calories) {
            this.detail = detail;
            this.workoutName = workoutName;
            this.calories = calories;
        }

        public WorkoutPlanDetail getDetail() { return detail; }
        public String getWorkoutName() { return workoutName; }
        public double getCalories() { return calories; }
    }
}
