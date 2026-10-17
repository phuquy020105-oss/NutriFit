package com.nutrifit.dto;

import com.nutrifit.model.FoodPreference;
import java.time.LocalDateTime;

/** A saved preference keeps its ingredient name visible even when the food is inactive. */
public record FoodPreferenceView(long foodId, String foodName, FoodPreference.PreferenceType type,
                                 LocalDateTime updatedAt, boolean active) { }
