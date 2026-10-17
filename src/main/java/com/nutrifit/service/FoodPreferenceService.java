package com.nutrifit.service;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.FoodPreferenceDAO;
import com.nutrifit.dao.FoodCatalogDAO;
import com.nutrifit.dto.FoodOption;
import com.nutrifit.dto.FoodPreferenceView;
import com.nutrifit.model.FoodPreference;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.List;

public class FoodPreferenceService {
    private final FoodPreferenceDAO dao = new FoodPreferenceDAO();
    private final FoodCatalogDAO catalog = new FoodCatalogDAO();

    public List<FoodOption> listAvailableFoods(long userId) throws SQLException {
        requireUser(userId);
        try (Connection c = DatabaseConfig.getConnection()) {
            return catalog.listActive(c);
        }
    }

    public List<FoodPreferenceView> listSavedPreferences(long userId) throws SQLException {
        requireUser(userId);
        try (Connection c = DatabaseConfig.getConnection()) {
            return dao.findViewsByUser(c, userId);
        }
    }

    public List<FoodPreference> listPreferences(long userId) throws SQLException {
        requireUser(userId);
        try (Connection c = DatabaseConfig.getConnection()) {
            return dao.findByUser(c, userId);
        }
    }

    public void setPreference(long userId, long foodId, FoodPreference.PreferenceType type)
            throws SQLException {
        requireUser(userId);
        if (foodId <= 0 || type == null) throw new IllegalArgumentException("Invalid preference");
        try (Connection c = DatabaseConfig.getConnection()) {
            if (!dao.isActiveFood(c, foodId)) {
                throw new IllegalArgumentException("Food missing or inactive");
            }
            dao.upsert(c, userId, foodId, type);
        }
    }

    public void removePreference(long userId, long foodId) throws SQLException {
        requireUser(userId);
        if (foodId <= 0) throw new IllegalArgumentException("Invalid food ID");
        try (Connection c = DatabaseConfig.getConnection()) {
            dao.delete(c, userId, foodId);
        }
    }

    private static void requireUser(long userId) {
        if (userId <= 0) throw new SecurityException("Login required");
    }
}
