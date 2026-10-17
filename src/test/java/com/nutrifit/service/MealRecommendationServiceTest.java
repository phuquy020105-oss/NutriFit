package com.nutrifit.service;

import com.nutrifit.model.MealEntry;
import org.junit.jupiter.api.Test;
import java.lang.reflect.Proxy;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class MealRecommendationServiceTest {
    @Test
    void serviceDeniesRecommendationsForFreeOrExpiredAccountsBeforeReadingCatalog() {
        for (boolean expired : new boolean[]{false, true}) {
            List<String> closed = new ArrayList<>();
            MealRecommendationService service = service(expired ? "PREMIUM" : "FREE",
                    Timestamp.valueOf(LocalDateTime.now().minusDays(2)), closed);
            assertThrows(SecurityException.class,
                    () -> service.recommend(42, MealEntry.MealType.LUNCH, 15));
            assertEquals(List.of("result", "statement", "connection"), closed);
        }
    }

    @Test
    void keepsExistingPremiumPolicyForFutureAndNullExpiry() throws Exception {
        assertTrue(service("PREMIUM", Timestamp.valueOf(LocalDateTime.now().plusDays(2)),
                new ArrayList<>()).hasPremiumAccess(42));
        assertTrue(service("PREMIUM", null, new ArrayList<>()).hasPremiumAccess(42));
        assertFalse(service("FREE", null, new ArrayList<>()).hasPremiumAccess(42));
    }

    @Test
    void invalidIdentityIsRejectedWithoutOpeningDatabase() throws Exception {
        MealRecommendationService service = new MealRecommendationService(() -> {
            throw new AssertionError("No database access expected");
        });
        assertFalse(service.hasPremiumAccess(0));
        assertThrows(SecurityException.class, () -> service.recommend(0, MealEntry.MealType.LUNCH, 15));
    }

    private MealRecommendationService service(String status, Timestamp expiry, List<String> closed) {
        ResultSet result = (ResultSet) Proxy.newProxyInstance(getClass().getClassLoader(),
                new Class<?>[]{ResultSet.class}, (p, method, args) -> switch (method.getName()) {
                    case "next" -> true;
                    case "getString" -> { assertEquals("subscription_status", args[0]); yield status; }
                    case "getTimestamp" -> { assertEquals("premium_expires_at", args[0]); yield expiry; }
                    case "close" -> { closed.add("result"); yield null; }
                    default -> throw new AssertionError("Unexpected result access: " + method.getName());
                });
        PreparedStatement statement = (PreparedStatement) Proxy.newProxyInstance(getClass().getClassLoader(),
                new Class<?>[]{PreparedStatement.class}, (p, method, args) -> switch (method.getName()) {
                    case "setLong" -> { assertEquals(1, args[0]); assertEquals(42L, args[1]); yield null; }
                    case "executeQuery" -> result;
                    case "close" -> { closed.add("statement"); yield null; }
                    default -> throw new AssertionError("Unexpected statement access: " + method.getName());
                });
        Connection connection = (Connection) Proxy.newProxyInstance(getClass().getClassLoader(),
                new Class<?>[]{Connection.class}, (p, method, args) -> switch (method.getName()) {
                    case "prepareStatement" -> {
                        assertEquals("SELECT subscription_status,premium_expires_at FROM users WHERE user_id=?", args[0]);
                        yield statement;
                    }
                    case "close" -> { closed.add("connection"); yield null; }
                    default -> throw new AssertionError("Unexpected connection access: " + method.getName());
                });
        return new MealRecommendationService(() -> connection);
    }
}
