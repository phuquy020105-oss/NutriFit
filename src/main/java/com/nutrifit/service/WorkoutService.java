package com.nutrifit.service;

import com.nutrifit.dao.WorkoutDAO;
import com.nutrifit.dao.WorkoutLogDAO;
import com.nutrifit.model.Workout;
import com.nutrifit.model.WorkoutLog;

import java.sql.SQLException;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

public class WorkoutService {

    /** Dùng tạm cho đến khi lấy được cân nặng thật từ hồ sơ người dùng. */
    public static final double DEFAULT_WEIGHT_KG = 60.0;

    private final WorkoutDAO workoutDAO = new WorkoutDAO();
    private final WorkoutLogDAO workoutLogDAO = new WorkoutLogDAO();
    private final PremiumAccessService premiumAccessService = new PremiumAccessService();

    /** Bài FREE + bài PREMIUM (nếu có premium) + bài tự tạo của chính user. */
    public List<Workout> listAvailableWorkouts(long userId) throws SQLException {
        boolean premium = premiumAccessService.hasActivePremium(userId);
        List<Workout> result = new ArrayList<>();
        for (Workout w : workoutDAO.findAll()) {
            if (canAccess(w, userId, premium)) {
                result.add(w);
            }
        }
        return result;
    }

    /**
     * @throws IllegalArgumentException không có bài tập này (Servlet trả 404)
     * @throws SecurityException        không đủ quyền xem (Servlet trả 403)
     */
    public Workout getWorkoutDetail(long userId, long workoutId) throws SQLException {
        Workout w = workoutDAO.findById(workoutId);
        if (w == null) {
            throw new IllegalArgumentException("Không tìm thấy bài tập");
        }
        if (!canAccess(w, userId, premiumAccessService.hasActivePremium(userId))) {
            throw new SecurityException("Bạn không có quyền xem bài tập này (cần tài khoản Premium)");
        }
        return w;
    }

    /** Ghi log tập ngoài lộ trình. Trả về log đã lưu (có estimatedCalories). */
    public WorkoutLog recordWorkout(long userId, long workoutId, int minutes) throws SQLException {
        return recordWorkout(userId, workoutId, minutes, null);
    }

    /** planDetailId != null khi user tick hoàn thành một bài trong lộ trình. */
    public WorkoutLog recordWorkout(long userId, long workoutId, int minutes, Long planDetailId)
            throws SQLException {
        if (minutes <= 0) {
            throw new IllegalArgumentException("Số phút phải lớn hơn 0");
        }
        Workout w = getWorkoutDetail(userId, workoutId);

        WorkoutLog log = new WorkoutLog();
        log.setUserId(userId);
        log.setWorkoutId(workoutId);
        log.setPlanDetailId(planDetailId);
        log.setLoggedDate(LocalDate.now());
        log.setDurationMinutes(minutes);
        log.setMetValue(w.getMetValue());
        log.setEstimatedCalories(
            CalorieCalculator.calculate(w.getMetValue(), resolveWeightKg(userId), minutes));
        log.setLogId(workoutLogDAO.insert(log));
        return log;
    }

    public List<WorkoutLog> listLogs(long userId) throws SQLException {
        return workoutLogDAO.findByUserId(userId);
    }

    /** TODO: thay bằng cân nặng trong hồ sơ user (hỏi bạn làm module profile). */
    public double resolveWeightKg(long userId) throws SQLException {
        return DEFAULT_WEIGHT_KG;
    }

    private boolean canAccess(Workout w, long userId, boolean premium) {
        if (w.isCustom()) {
            return w.getCreatedBy() != null && w.getCreatedBy() == userId;
        }
        return !"PREMIUM".equals(w.getAccessLevel()) || premium;
    }
}
