package com.nutrifit.service;

import com.nutrifit.dao.UserProfileDAO;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.sql.SQLException;
import java.util.Map;
import java.util.Set;

public class OnboardingService {
    private final UserProfileDAO dao = new UserProfileDAO();
    private static final Map<String, Double> ACTIVITY = Map.of(
        "sedentary",1.2,"light",1.375,"moderate",1.55,
        "high",1.725,"very_high",1.9);
    private static final Set<String> GOALS = Set.of("lose","maintain","gain");

    public boolean isComplete(long userId) throws SQLException { return dao.isComplete(userId); }

    public void save(long userId, String gender, String ageText,
                     String heightText, String weightText,
                     String activity, String goal) throws SQLException {
        if (!Set.of("male","female").contains(gender)
                || !ACTIVITY.containsKey(activity) || !GOALS.contains(goal)) {
            throw new IllegalArgumentException("Vui lòng chọn thông tin hợp lệ.");
        }
        final int age;
        final BigDecimal height, weight;
        try {
            age = Integer.parseInt(ageText);
            height = new BigDecimal(heightText);
            weight = new BigDecimal(weightText);
        } catch (RuntimeException ex) {
            throw new IllegalArgumentException("Tuổi, chiều cao và cân nặng phải là số hợp lệ.");
        }
        if (age < 18 || age > 100 || height.compareTo(BigDecimal.valueOf(100)) < 0
                || height.compareTo(BigDecimal.valueOf(250)) > 0
                || weight.compareTo(BigDecimal.valueOf(25)) < 0
                || weight.compareTo(BigDecimal.valueOf(350)) > 0) {
            throw new IllegalArgumentException("Chỉ hỗ trợ người từ 18–100 tuổi, cao 100–250 cm, nặng 25–350 kg.");
        }
        double h = height.doubleValue(), w = weight.doubleValue();
        // Mifflin–St Jeor: chỉ số ước tính cho người trưởng thành.
        double bmr = 10*w + 6.25*h - 5*age + ("male".equals(gender) ? 5 : -161);
        double tdee = bmr * ACTIVITY.get(activity);
        double adjustment = switch (goal) { case "lose" -> -300; case "gain" -> 300; default -> 0; };
        double target = Math.max(1200, tdee + adjustment);
        int water = (int)(Math.round(w * 35 / 50.0) * 50);
        dao.save(userId,gender,age,height,weight,activity,goal,
            rounded(bmr),rounded(tdee),rounded(target),water);
    }
    private BigDecimal rounded(double d) {
        return BigDecimal.valueOf(d).setScale(2, RoundingMode.HALF_UP);
    }
}
