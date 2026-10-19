package com.nutrifit.service;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.FoodPreferenceDAO;
import com.nutrifit.dao.FoodCatalogDAO;
import com.nutrifit.dao.NutritionUserReadDAO;
import com.nutrifit.dto.FoodOption;
import com.nutrifit.dto.FoodPreferenceView;
import com.nutrifit.model.FoodPreference;
import java.sql.Connection;
import java.sql.SQLException;
import java.time.Clock;
import java.time.LocalDateTime;
import java.util.List;

public class FoodPreferenceService {
    private final FoodPreferenceDAO dao;
    private final FoodCatalogDAO catalog;
    private final NutritionUserReadDAO users;
    private final ConnectionProvider connections;
    private final Clock clock;

    public FoodPreferenceService() {
        this(new FoodPreferenceDAO(), new FoodCatalogDAO(), new NutritionUserReadDAO(),
                DatabaseConfig::getConnection, Clock.systemDefaultZone());
    }
    FoodPreferenceService(FoodPreferenceDAO dao, FoodCatalogDAO catalog, NutritionUserReadDAO users,
                          ConnectionProvider connections, Clock clock) {
        this.dao = dao; this.catalog = catalog; this.users = users; this.connections = connections; this.clock = clock;
    }
    public boolean hasPremiumAccess(long userId) throws SQLException {
        requireUser(userId);
        try (Connection c = connections.open()) { return users.hasPremiumAccess(c, userId, LocalDateTime.now(clock)); }
    }
    public List<FoodOption> listAvailableFoods(long userId) throws SQLException {
        requireUser(userId);
        try (Connection c = connections.open()) { requirePremium(c, userId); return catalog.listActive(c); }
    }
    public List<FoodPreferenceView> listSavedPreferences(long userId) throws SQLException {
        requireUser(userId);
        try (Connection c = connections.open()) { requirePremium(c, userId); return dao.findViewsByUser(c, userId); }
    }
    public List<FoodPreference> listPreferences(long userId) throws SQLException {
        requireUser(userId);
        try (Connection c = connections.open()) { requirePremium(c, userId); return dao.findByUser(c, userId); }
    }
    public void setPreference(long userId, long foodId, FoodPreference.PreferenceType type) throws SQLException {
        requireUser(userId);
        if (foodId <= 0 || type == null) throw new IllegalArgumentException("Invalid preference");
        try (Connection c = connections.open()) {
            requirePremium(c, userId);
            if (!dao.isActiveFood(c, foodId)) throw new IllegalArgumentException("Food missing or inactive");
            dao.upsert(c, userId, foodId, type);
        }
    }
    public void removePreference(long userId, long foodId) throws SQLException {
        requireUser(userId);
        if (foodId <= 0) throw new IllegalArgumentException("Invalid food ID");
        try (Connection c = connections.open()) { requirePremium(c, userId); dao.delete(c, userId, foodId); }
    }
    private void requirePremium(Connection c, long userId) throws SQLException {
        if (!users.hasPremiumAccess(c, userId, LocalDateTime.now(clock))) throw new SecurityException("PREMIUM_REQUIRED");
    }
    private static void requireUser(long userId) { if (userId <= 0) throw new SecurityException("Login required"); }
}
