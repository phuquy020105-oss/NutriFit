package com.nutrifit.dto;

import java.util.Locale;

/** Reuses Profile's existing goal; no BMR, TDEE or protein prescription is recalculated. */
public enum NutritionGoal {
    LOSE, MAINTAIN, GAIN;
    public static NutritionGoal fromProfile(String value) {
        if (value == null) return MAINTAIN;
        return switch (value.strip().toLowerCase(Locale.ROOT)) {
            case "lose" -> LOSE;
            case "gain" -> GAIN;
            default -> MAINTAIN;
        };
    }
}
