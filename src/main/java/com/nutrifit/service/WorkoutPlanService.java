package com.nutrifit.service;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.WorkoutDAO;
import com.nutrifit.dao.WorkoutGoalDAO;
import com.nutrifit.dao.WorkoutPlanDAO;
import com.nutrifit.dao.WorkoutPlanDayDAO;
import com.nutrifit.dao.WorkoutPlanDetailDAO;
import com.nutrifit.dto.WorkoutPlanView;
import com.nutrifit.model.Workout;
import com.nutrifit.model.WorkoutGoal;
import com.nutrifit.model.WorkoutPlan;
import com.nutrifit.model.WorkoutPlanDay;
import com.nutrifit.model.WorkoutPlanDetail;

import java.sql.Connection;
import java.sql.SQLException;
import java.time.LocalDate;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class WorkoutPlanService {

    private static final int DEFAULT_SESSIONS_PER_WEEK = 3;

    private final WorkoutGoalDAO goalDAO = new WorkoutGoalDAO();
    private final WorkoutPlanDAO planDAO = new WorkoutPlanDAO();
    private final WorkoutPlanDayDAO dayDAO = new WorkoutPlanDayDAO();
    private final WorkoutPlanDetailDAO detailDAO = new WorkoutPlanDetailDAO();
    private final WorkoutDAO workoutDAO = new WorkoutDAO();
    private final WorkoutService workoutService = new WorkoutService();

    /**
     * Tạo lộ trình 7 ngày từ mục tiêu của user: rải đều số buổi tập trong tuần,
     * mỗi buổi 1 bài (xoay vòng trong danh sách bài user được phép dùng).
     * Ghi 3 bảng trong cùng một transaction.
     */
    public WorkoutPlan generateSevenDayPlan(long userId) throws SQLException {
        WorkoutGoal goal = goalDAO.findByUserId(userId);
        int sessions = DEFAULT_SESSIONS_PER_WEEK;
        int minutesPerSession = 0; // 0 = dùng thời lượng mặc định của từng bài
        if (goal != null && goal.getWeeklySessionsTarget() > 0) {
            sessions = Math.min(goal.getWeeklySessionsTarget(), 7);
            if (goal.getWeeklyDurationTarget() > 0) {
                minutesPerSession = Math.max(goal.getWeeklyDurationTarget() / sessions, 1);
            }
        }

        List<Workout> pool = workoutService.listAvailableWorkouts(userId);
        if (pool.isEmpty()) {
            throw new IllegalStateException("Chưa có bài tập nào để tạo lộ trình");
        }

        Set<Integer> trainingDays = new HashSet<>();
        for (int i = 0; i < sessions; i++) {
            trainingDays.add(i * 7 / sessions + 1);
        }

        LocalDate start = LocalDate.now();
        WorkoutPlan plan = new WorkoutPlan();
        plan.setUserId(userId);
        plan.setPlanName("Lộ trình 7 ngày từ " + start);
        plan.setStartDate(start);
        plan.setEndDate(start.plusDays(6));
        plan.setActive(true);

        try (Connection conn = DatabaseConfig.getConnection()) {
            conn.setAutoCommit(false);
            try {
                planDAO.deactivateByUserId(conn, userId);
                long planId = planDAO.insert(conn, plan);

                int next = 0;
                for (int dayIndex = 1; dayIndex <= 7; dayIndex++) {
                    boolean training = trainingDays.contains(dayIndex);
                    Workout workout = training ? pool.get(next++ % pool.size()) : null;

                    WorkoutPlanDay day = new WorkoutPlanDay();
                    day.setPlanId(planId);
                    day.setDayIndex(dayIndex);
                    day.setDayName("Ngày " + dayIndex);
                    day.setRestDay(!training);
                    day.setFocusArea(training ? workout.getMuscleGroup() : "Nghỉ ngơi");
                    long dayId = dayDAO.insert(conn, day);

                    if (training) {
                        WorkoutPlanDetail detail = new WorkoutPlanDetail();
                        detail.setPlanDayId(dayId);
                        detail.setWorkoutId(workout.getWorkoutId());
                        detail.setDurationMinutes(
                            minutesPerSession > 0 ? minutesPerSession : workout.getDefaultDurationMinutes());
                        detail.setOrderIndex(1);
                        detailDAO.insert(conn, detail);
                    }
                }
                conn.commit();
                plan.setPlanId(planId);
                return plan;
            } catch (SQLException | RuntimeException e) {
                conn.rollback();
                throw e;
            }
        }
    }

    /** Lộ trình đầy đủ (các ngày, bài tập, calo) để hiển thị. */
    public WorkoutPlanView getPlan(long userId, long planId) throws SQLException {
        WorkoutPlan plan = requireOwnedPlan(userId, planId);
        double weight = workoutService.resolveWeightKg(userId);

        WorkoutPlanView view = new WorkoutPlanView(plan);
        for (WorkoutPlanDay day : dayDAO.findByPlanId(planId)) {
            WorkoutPlanView.DayView dayView = new WorkoutPlanView.DayView(day);
            for (WorkoutPlanDetail detail : detailDAO.findByDayId(day.getPlanDayId())) {
                Workout w = workoutDAO.findById(detail.getWorkoutId());
                dayView.addItem(new WorkoutPlanView.ItemView(
                    detail, w.getWorkoutName(), caloriesOf(w, detail, weight)));
            }
            view.getDays().add(dayView);
        }
        return view;
    }

    /** Lộ trình mới nhất của user, hoặc null nếu chưa có. */
    public WorkoutPlanView getLatestPlan(long userId) throws SQLException {
        List<WorkoutPlan> plans = planDAO.findByUserId(userId);
        return plans.isEmpty() ? null : getPlan(userId, plans.get(0).getPlanId());
    }

    public void changeDuration(long userId, long detailId, int minutes) throws SQLException {
        if (minutes <= 0) {
            throw new IllegalArgumentException("Số phút phải lớn hơn 0");
        }
        requireOwnedDetail(userId, detailId);
        detailDAO.updateDuration(detailId, minutes);
    }

    public void addWorkout(long userId, long dayId, long workoutId, int minutes) throws SQLException {
        if (minutes <= 0) {
            throw new IllegalArgumentException("Số phút phải lớn hơn 0");
        }
        WorkoutPlanDay day = requireOwnedDay(userId, dayId);
        if (day.isRestDay()) {
            throw new IllegalStateException("Đây là ngày nghỉ, không thể thêm bài tập");
        }
        workoutService.getWorkoutDetail(userId, workoutId); // kiểm tra tồn tại + quyền dùng

        int nextOrder = 1;
        for (WorkoutPlanDetail d : detailDAO.findByDayId(dayId)) {
            nextOrder = Math.max(nextOrder, d.getOrderIndex() + 1);
        }
        WorkoutPlanDetail detail = new WorkoutPlanDetail();
        detail.setPlanDayId(dayId);
        detail.setWorkoutId(workoutId);
        detail.setDurationMinutes(minutes);
        detail.setOrderIndex(nextOrder);
        detailDAO.insert(detail);
    }

    public void removeWorkout(long userId, long detailId) throws SQLException {
        requireOwnedDetail(userId, detailId);
        detailDAO.deleteById(detailId);
    }

    public double calculateDayCalories(long dayId, double weightKg) throws SQLException {
        double total = 0;
        for (WorkoutPlanDetail detail : detailDAO.findByDayId(dayId)) {
            total += caloriesOf(workoutDAO.findById(detail.getWorkoutId()), detail, weightKg);
        }
        return total;
    }

    private double caloriesOf(Workout w, WorkoutPlanDetail detail, double weightKg) {
        return CalorieCalculator.calculate(w.getMetValue(), weightKg, detail.getDurationMinutes());
    }

    // ---- Kiểm tra quyền sở hữu: chặn user sửa lộ trình của người khác bằng cách đoán id ----

    private WorkoutPlan requireOwnedPlan(long userId, long planId) throws SQLException {
        WorkoutPlan plan = planDAO.findById(planId);
        if (plan == null) {
            throw new IllegalArgumentException("Không tìm thấy lộ trình");
        }
        if (plan.getUserId() != userId) {
            throw new SecurityException("Bạn không có quyền với lộ trình này");
        }
        return plan;
    }

    private WorkoutPlanDay requireOwnedDay(long userId, long dayId) throws SQLException {
        WorkoutPlanDay day = dayDAO.findById(dayId);
        if (day == null) {
            throw new IllegalArgumentException("Không tìm thấy ngày trong lộ trình");
        }
        requireOwnedPlan(userId, day.getPlanId());
        return day;
    }

    private WorkoutPlanDetail requireOwnedDetail(long userId, long detailId) throws SQLException {
        WorkoutPlanDetail detail = detailDAO.findById(detailId);
        if (detail == null) {
            throw new IllegalArgumentException("Không tìm thấy bài tập trong lộ trình");
        }
        requireOwnedDay(userId, detail.getPlanDayId());
        return detail;
    }
}
