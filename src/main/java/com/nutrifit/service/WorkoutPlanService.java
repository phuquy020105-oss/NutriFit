package com.nutrifit.service;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.WorkoutCategoryDAO;
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
import java.text.Normalizer;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

public class WorkoutPlanService {

    private static final int DEFAULT_SESSIONS_PER_WEEK = 3;
    static final int WARMUP_WORKOUTS_PER_SESSION = 3;
    static final int CALISTHENIC_WORKOUTS_PER_SESSION = 5;
    static final int STRETCHING_WORKOUTS_PER_SESSION = 2;
    static final int TOTAL_WORKOUTS_PER_SESSION =
        WARMUP_WORKOUTS_PER_SESSION + CALISTHENIC_WORKOUTS_PER_SESSION + STRETCHING_WORKOUTS_PER_SESSION;

    private final WorkoutGoalDAO goalDAO = new WorkoutGoalDAO();
    private final WorkoutPlanDAO planDAO = new WorkoutPlanDAO();
    private final WorkoutPlanDayDAO dayDAO = new WorkoutPlanDayDAO();
    private final WorkoutPlanDetailDAO detailDAO = new WorkoutPlanDetailDAO();
    private final WorkoutDAO workoutDAO = new WorkoutDAO();
    private final WorkoutCategoryDAO categoryDAO = new WorkoutCategoryDAO();
    private final WorkoutService workoutService = new WorkoutService();

    /**
     * Tạo lộ trình 7 ngày từ mục tiêu của user: rải đều số buổi tập trong tuần,
     * mỗi buổi gồm 3 bài khởi động, 5 bài Calisthenic và 2 bài giãn cơ.
     * Ghi 3 bảng trong cùng một transaction.
     */
    public WorkoutPlan generateSevenDayPlan(long userId) throws SQLException {
        WorkoutGoal goal = goalDAO.findByUserId(userId);
        int sessions = DEFAULT_SESSIONS_PER_WEEK;
        int minutesPerSession = 0; // 0 = dùng thời lượng mặc định của từng bài
        if (goal != null && goal.getWeeklySessionsTarget() > 0) {
            sessions = Math.min(goal.getWeeklySessionsTarget(), 7);
            if (goal.getWeeklyDurationTarget() > 0) {
                minutesPerSession = Math.max(
                    goal.getWeeklyDurationTarget() / sessions, TOTAL_WORKOUTS_PER_SESSION);
            }
        }

        List<Workout> pool = workoutService.listAvailableWorkouts(userId);
        if (pool.isEmpty()) {
            throw new IllegalStateException("Chưa có bài tập nào để tạo lộ trình");
        }
        Map<Long, String> categoryNames = categoryDAO.findAll().stream()
            .collect(Collectors.toMap(category -> category.getCategoryId(),
                category -> category.getCategoryName()));
        List<Workout> warmupWorkouts = pool.stream()
            .filter(workout -> isCategory(categoryNames.get(workout.getCategoryId()),
                "khoi dong", "warm up", "warmup"))
            .toList();
        List<Workout> calisthenicWorkouts = pool.stream()
            .filter(workout -> isCategory(categoryNames.get(workout.getCategoryId()), "calis"))
            .toList();
        List<Workout> stretchingWorkouts = pool.stream()
            .filter(workout -> isCategory(categoryNames.get(workout.getCategoryId()),
                "gian co", "stretch"))
            .toList();
        Set<Integer> trainingDays = trainingDays(sessions);

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

                int sessionIndex = 0;
                for (int dayIndex = 1; dayIndex <= 7; dayIndex++) {
                    boolean training = trainingDays.contains(dayIndex);
                    List<Workout> sessionWorkouts = training
                        ? selectSessionWorkouts(
                            warmupWorkouts, calisthenicWorkouts, stretchingWorkouts, sessionIndex)
                        : List.of();
                    if (training) {
                        sessionIndex++;
                    }

                    WorkoutPlanDay day = new WorkoutPlanDay();
                    day.setPlanId(planId);
                    day.setDayIndex(dayIndex);
                    day.setDayName("Ngày " + dayIndex);
                    day.setRestDay(!training);
                    day.setFocusArea(training ? "Khởi động + Calisthenic + Giãn cơ" : "Nghỉ ngơi");
                    long dayId = dayDAO.insert(conn, day);

                    if (training) {
                        for (int i = 0; i < sessionWorkouts.size(); i++) {
                            Workout workout = sessionWorkouts.get(i);
                            WorkoutPlanDetail detail = new WorkoutPlanDetail();
                            detail.setPlanDayId(dayId);
                            detail.setWorkoutId(workout.getWorkoutId());
                            detail.setDurationMinutes(minutesPerSession > 0
                                ? splitDuration(minutesPerSession, sessionWorkouts.size(), i)
                                : workout.getDefaultDurationMinutes());
                            detail.setOrderIndex(i + 1);
                            detailDAO.insert(conn, detail);
                        }
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

    static boolean isCategory(String categoryName, String... expectedPrefixes) {
        if (categoryName == null) {
            return false;
        }
        String normalizedName = Normalizer.normalize(categoryName.replace('đ', 'd').replace('Đ', 'D'),
                Normalizer.Form.NFD)
            .replaceAll("\\p{M}", "")
            .toLowerCase(Locale.ROOT)
            .replaceAll("[^a-z0-9]+", " ")
            .trim();
        for (String prefix : expectedPrefixes) {
            if (normalizedName.startsWith(prefix)) {
                return true;
            }
        }
        return false;
    }

    static void requireEnoughWorkouts(List<Workout> workouts, int required, String categoryName) {
        if (workouts.size() < required) {
            throw new IllegalStateException(
                "Cần ít nhất " + required + " bài " + categoryName
                    + ", hiện chỉ có " + workouts.size() + " bài khả dụng");
        }
    }

    static List<Workout> selectSessionWorkouts(List<Workout> warmupWorkouts, List<Workout> calisthenicWorkouts,
                                               List<Workout> stretchingWorkouts, int sessionIndex) {
        requireEnoughWorkouts(warmupWorkouts, WARMUP_WORKOUTS_PER_SESSION, "khởi động");
        requireEnoughWorkouts(calisthenicWorkouts, CALISTHENIC_WORKOUTS_PER_SESSION, "Calisthenic");
        requireEnoughWorkouts(stretchingWorkouts, STRETCHING_WORKOUTS_PER_SESSION, "giãn cơ");

        List<Workout> selected = new ArrayList<>(TOTAL_WORKOUTS_PER_SESSION);
        addRotatingWorkouts(selected, warmupWorkouts, WARMUP_WORKOUTS_PER_SESSION, sessionIndex);
        addRotatingWorkouts(selected, calisthenicWorkouts, CALISTHENIC_WORKOUTS_PER_SESSION, sessionIndex);
        addRotatingWorkouts(selected, stretchingWorkouts, STRETCHING_WORKOUTS_PER_SESSION, sessionIndex);
        return selected;
    }

    static Set<Integer> trainingDays(int sessions) {
        if (sessions < 1 || sessions > 7) {
            throw new IllegalArgumentException("Số buổi tập phải từ 1 đến 7");
        }
        Set<Integer> days = new HashSet<>();
        for (int i = 0; i < sessions; i++) {
            days.add(i * 7 / sessions + 1);
        }
        return days;
    }

    static int splitDuration(int totalMinutes, int workoutCount, int index) {
        if (workoutCount <= 0 || totalMinutes < workoutCount || index < 0 || index >= workoutCount) {
            throw new IllegalArgumentException("Thời lượng phải đủ cho mỗi bài ít nhất 1 phút");
        }
        return totalMinutes / workoutCount + (index < totalMinutes % workoutCount ? 1 : 0);
    }

    private static void addRotatingWorkouts(List<Workout> selected, List<Workout> candidates, int count,
                                            int sessionIndex) {
        for (int i = 0; i < count; i++) {
            selected.add(candidates.get(Math.floorMod(sessionIndex + i, candidates.size())));
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
