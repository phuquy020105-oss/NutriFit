package com.nutrifit.service;

public final class CalorieCalculator {

    private CalorieCalculator() {
    }

    /** kcal = MET x cân nặng (kg) x thời gian (giờ), làm tròn 3 chữ số cho khớp DECIMAL(12,3). */
    public static double calculate(double met, double weightKg, int minutes) {
        if (met <= 0 || weightKg <= 0 || minutes <= 0) {
            throw new IllegalArgumentException("MET, cân nặng và số phút phải lớn hơn 0");
        }
        double kcal = met * weightKg * minutes / 60.0;
        return Math.round(kcal * 1000.0) / 1000.0;
    }
}
