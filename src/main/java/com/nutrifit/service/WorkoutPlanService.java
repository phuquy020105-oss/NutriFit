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
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

public class WorkoutPlanService {

    /** Mặc định (mục tiêu giữ dáng): 4 buổi tập + 3 ngày nghỉ trong 7 ngày. */
    private static final int DEFAULT_SESSIONS_PER_WEEK = 4;
    static final int WARMUP_WORKOUTS_PER_SESSION = 3;
    static final int CALISTHENIC_WORKOUTS_PER_SESSION = 5;
    static final int STRETCHING_WORKOUTS_PER_SESSION = 2;
    static final int TOTAL_WORKOUTS_PER_SESSION =
        WARMUP_WORKOUTS_PER_SESSION + CALISTHENIC_WORKOUTS_PER_SESSION + STRETCHING_WORKOUTS_PER_SESSION;
    /** Mỗi bài ít nhất 1 phút => mỗi buổi tập ít nhất 10 phút. */
    static final int MIN_MINUTES_PER_WORKOUT = 1;
    static final int MIN_MINUTES_PER_SESSION = TOTAL_WORKOUTS_PER_SESSION * MIN_MINUTES_PER_WORKOUT;

    private final WorkoutGoalDAO goalDAO = new WorkoutGoalDAO();
    private final WorkoutPlanDAO planDAO = new WorkoutPlanDAO();
    private final WorkoutPlanDayDAO dayDAO = new WorkoutPlanDayDAO();
    private final WorkoutPlanDetailDAO detailDAO = new WorkoutPlanDetailDAO();
    private final WorkoutDAO workoutDAO = new WorkoutDAO();
    private final WorkoutCategoryDAO categoryDAO = new WorkoutCategoryDAO();
    private final WorkoutService workoutService = new WorkoutService();

    /**
     * Tạo lộ trình 7 ngày từ mục tiêu của user: rải đều số buổi tập trong tuần
     * (mặc định 4 buổi tập + 3 ngày nghỉ), mỗi buổi gồm 3 bài khởi động,
     * 5 bài Calisthenic và 2 bài giãn cơ, mỗi buổi tập ít nhất 10 phút.
     * Các nhóm cơ được chia đều cho các buổi để cả tuần phủ hết mọi nhóm cơ.
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
                    goal.getWeeklyDurationTarget() / sessions, MIN_MINUTES_PER_SESSION);
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
        requireEnoughWorkouts(warmupWorkouts, WARMUP_WORKOUTS_PER_SESSION, "khởi động");
        requireEnoughWorkouts(calisthenicWorkouts, CALISTHENIC_WORKOUTS_PER_SESSION, "Calisthenic");
        requireEnoughWorkouts(stretchingWorkouts, STRETCHING_WORKOUTS_PER_SESSION, "giãn cơ");

        // Chia đều các nhóm cơ cho các buổi tập để cả tuần phủ hết mọi nhóm cơ.
        Map<String, String> muscleGroups = muscleGroupNames(calisthenicWorkouts);
        List<Set<String>> groupsPerSession = assignGroupsToSessions(new ArrayList<>(muscleGroups.keySet()), sessions);
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
                    Set<String> sessionGroups = training ? groupsPerSession.get(sessionIndex) : Set.of();
                    List<Workout> sessionWorkouts = training
                        ? selectSessionWorkouts(
                            warmupWorkouts, calisthenicWorkouts, stretchingWorkouts, sessionGroups)
                        : List.of();
                    if (training) {
                        sessionIndex++;
                    }

                    WorkoutPlanDay day = new WorkoutPlanDay();
                    day.setPlanId(planId);
                    day.setDayIndex(dayIndex);
                    day.setDayName("Ngày " + dayIndex);
                    day.setRestDay(!training);
                    day.setFocusArea(training ? focusAreaOf(sessionGroups, muscleGroups) : "Nghỉ ngơi");
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
        String normalizedName = normalize(categoryName);
        for (String prefix : expectedPrefixes) {
            if (normalizedName.startsWith(prefix)) {
                return true;
            }
        }
        return false;
    }

    /** Bỏ dấu, chữ thường, chỉ giữ chữ-số, cách nhau bằng 1 khoảng trắng. */
    static String normalize(String text) {
        return Normalizer.normalize(text.replace('đ', 'd').replace('Đ', 'D'), Normalizer.Form.NFD)
            .replaceAll("\\p{M}", "")
            .toLowerCase(Locale.ROOT)
            .replaceAll("[^a-z0-9]+", " ")
            .trim();
    }

    static void requireEnoughWorkouts(List<Workout> workouts, int required, String categoryName) {
        if (workouts.size() < required) {
            throw new IllegalStateException(
                "Cần ít nhất " + required + " bài " + categoryName
                    + ", hiện chỉ có " + workouts.size() + " bài khả dụng");
        }
    }

    /**
     * Chọn 10 bài cho một buổi: 3 khởi động, 5 Calisthenic, 2 giãn cơ (đúng thứ tự này).
     * Trong mỗi nhóm, ưu tiên các bài thuộc nhóm cơ mục tiêu của buổi đó.
     */
    static List<Workout> selectSessionWorkouts(List<Workout> warmupWorkouts, List<Workout> calisthenicWorkouts,
                                               List<Workout> stretchingWorkouts, Set<String> targetGroups) {
        requireEnoughWorkouts(warmupWorkouts, WARMUP_WORKOUTS_PER_SESSION, "khởi động");
        requireEnoughWorkouts(calisthenicWorkouts, CALISTHENIC_WORKOUTS_PER_SESSION, "Calisthenic");
        requireEnoughWorkouts(stretchingWorkouts, STRETCHING_WORKOUTS_PER_SESSION, "giãn cơ");

        List<Workout> selected = new ArrayList<>(TOTAL_WORKOUTS_PER_SESSION);
        selected.addAll(pickWorkouts(warmupWorkouts, targetGroups, WARMUP_WORKOUTS_PER_SESSION));
        selected.addAll(pickWorkouts(calisthenicWorkouts, targetGroups, CALISTHENIC_WORKOUTS_PER_SESSION));
        selected.addAll(pickWorkouts(stretchingWorkouts, targetGroups, STRETCHING_WORKOUTS_PER_SESSION));
        return selected;
    }

    // ---- Nhóm cơ ----

    private static final Set<String> FULL_BODY_KEYS = Set.of("toan than", "full body", "fullbody");

    /** Tách cột muscle_group (có thể "Ngực, Tay" hoặc "Ngực và Tay") thành {khoá chuẩn hoá -> tên hiển thị}. */
    static Map<String, String> parseMuscleGroups(Workout workout) {
        Map<String, String> result = new LinkedHashMap<>();
        String raw = workout.getMuscleGroup();
        if (raw == null) {
            return result;
        }
        for (String piece : raw.split("\\s*[,;/&+]\\s*|\\s+(?i:và|va)\\s+")) {
            String display = piece.trim();
            String key = normalize(display);
            if (!key.isEmpty()) {
                result.putIfAbsent(key, display);
            }
        }
        return result;
    }

    /** Tất cả nhóm cơ cụ thể (bỏ "toàn thân") xuất hiện trong danh sách bài, theo thứ tự gặp đầu tiên. */
    static Map<String, String> muscleGroupNames(List<Workout> workouts) {
        Map<String, String> all = new LinkedHashMap<>();
        for (Workout w : workouts) {
            parseMuscleGroups(w).forEach((key, display) -> {
                if (!FULL_BODY_KEYS.contains(key)) {
                    all.putIfAbsent(key, display);
                }
            });
        }
        return all;
    }

    /**
     * Chia các nhóm cơ cho từng buổi (nhóm thứ i thuộc buổi i % sessions) nên hợp của mọi buổi
     * luôn đủ hết các nhóm. Nếu số buổi nhiều hơn số nhóm thì buổi thừa dùng lại nhóm theo vòng.
     */
    static List<Set<String>> assignGroupsToSessions(List<String> groups, int sessions) {
        List<Set<String>> result = new ArrayList<>();
        for (int d = 0; d < sessions; d++) {
            Set<String> assigned = new LinkedHashSet<>();
            for (int i = d; i < groups.size(); i += sessions) {
                assigned.add(groups.get(i));
            }
            if (assigned.isEmpty() && !groups.isEmpty()) {
                assigned.add(groups.get(d % groups.size()));
            }
            result.add(assigned);
        }
        return result;
    }

    /**
     * Chọn đúng {@code count} bài khác nhau: lần lượt lấy mỗi nhóm cơ mục tiêu một bài (xoay vòng),
     * thiếu thì lấy bài "toàn thân", vẫn thiếu thì lấy bài còn lại theo thứ tự trong danh sách.
     */
    static List<Workout> pickWorkouts(List<Workout> pool, Set<String> targetGroups, int count) {
        Map<Long, Workout> picked = new LinkedHashMap<>();

        List<Deque<Workout>> queues = new ArrayList<>();
        for (String group : targetGroups) {
            Deque<Workout> queue = new ArrayDeque<>();
            for (Workout w : pool) {
                if (parseMuscleGroups(w).containsKey(group)) {
                    queue.add(w);
                }
            }
            queues.add(queue);
        }
        boolean progress = true;
        while (picked.size() < count && progress) {
            progress = false;
            for (Deque<Workout> queue : queues) {
                while (!queue.isEmpty() && picked.containsKey(queue.peekFirst().getWorkoutId())) {
                    queue.pollFirst();
                }
                if (!queue.isEmpty() && picked.size() < count) {
                    Workout w = queue.pollFirst();
                    picked.put(w.getWorkoutId(), w);
                    progress = true;
                }
            }
        }
        for (Workout w : pool) {
            if (picked.size() < count && parseMuscleGroups(w).keySet().stream().anyMatch(FULL_BODY_KEYS::contains)) {
                picked.putIfAbsent(w.getWorkoutId(), w);
            }
        }
        for (Workout w : pool) {
            if (picked.size() < count) {
                picked.putIfAbsent(w.getWorkoutId(), w);
            }
        }
        return new ArrayList<>(picked.values());
    }

    private static String focusAreaOf(Set<String> groupKeys, Map<String, String> displayNames) {
        return groupKeys.stream().map(k -> displayNames.getOrDefault(k, k)).collect(Collectors.joining(", "));
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