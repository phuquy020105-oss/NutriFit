package com.nutrifit.controller;

import com.nutrifit.model.FoodPreference;
import com.nutrifit.model.MealEntry;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.junit.jupiter.api.Test;
import java.lang.reflect.Proxy;
import java.math.BigDecimal;
import java.sql.SQLException;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.logging.Level;
import java.util.logging.Logger;
import static org.junit.jupiter.api.Assertions.*;

class NutritionServletSupportTest {
    private final NutritionServletSupport support = new NutritionServletSupport() { };

    @Test
    void rejectsMissingAndMalformedIdsWithoutReflectingInput() throws Exception {
        for (String value : new String[]{null, "", " ", "0", "-1", "1.2", "secret", "9223372036854775808"}) {
            assertBadInput(() -> NutritionServletSupport.parseId(value));
        }
        assertEquals(Long.MAX_VALUE, NutritionServletSupport.parseId("9223372036854775807"));
        assertEquals(7L, NutritionServletSupport.parseId(" 7 "));
    }

    @Test
    void rejectsMissingAndUnknownEnums() throws Exception {
        for (String value : new String[]{null, "", " ", "lunch", "UNKNOWN"}) {
            assertBadInput(() -> NutritionServletSupport.parseMealType(value));
            assertBadInput(() -> NutritionServletSupport.parsePreferenceType(value));
        }
        assertEquals(MealEntry.MealType.LUNCH, NutritionServletSupport.parseMealType("LUNCH"));
        assertEquals(FoodPreference.PreferenceType.DISLIKE,
                NutritionServletSupport.parsePreferenceType("DISLIKE"));
    }

    @Test
    void boundsDecimalParsingAndRejectsInvalidServings() throws Exception {
        for (String value : new String[]{null, "", " ", "abc", "NaN", "1,5", "0", "-1",
                "0.001", "1.001", "1000000", "1e2147483647", "1e-2147483647", "9".repeat(10000)}) {
            assertBadInput(() -> NutritionServletSupport.parseServings(value));
        }
        assertEquals(new BigDecimal("1.50"), NutritionServletSupport.parseServings(" 1.5 "));
        assertEquals(new BigDecimal("999999.99"), NutritionServletSupport.parseServings("999999.99"));
    }

    @Test
    void datesMustBeRealIsoCalendarDates() throws Exception {
        for (String value : new String[]{null, "", " ", "16/10/2026", "2026-1-01", "2026-02-29",
                "2026-13-01", "2026-10-16T00:00:00"}) {
            assertBadInput(() -> NutritionServletSupport.parseDate(value));
        }
        assertEquals(LocalDate.of(2024, 2, 29), NutritionServletSupport.parseDate("2024-02-29"));
    }

    @Test
    void missingActionsAreValidationErrors() throws Exception {
        for (String value : new String[]{null, "", " "}) {
            assertBadInput(() -> NutritionServletSupport.required(value));
        }
    }

    @Test
    void mapsFailuresWithoutSendingExceptionDetails() throws Exception {
        assertFailure(new IllegalArgumentException("secret input"), 400);
        assertFailure(new DateTimeParseException("secret input", "secret", 0), 400);
        assertFailure(new SecurityException("secret permission"), 403);
        assertFailure(new SQLException("secret database"), 503);
        assertFailure(new NullPointerException("secret server state"), 500);
    }

    @Test
    void missingAuthenticationStillReturns401AndNeverCreatesSession() throws Exception {
        HttpServletRequest request = (HttpServletRequest) Proxy.newProxyInstance(
                getClass().getClassLoader(), new Class<?>[]{HttpServletRequest.class}, (p, method, args) -> {
                    if (method.getName().equals("getSession")) {
                        assertArrayEquals(new Object[]{false}, args);
                        return null;
                    }
                    if (method.getName().equals("getParameter")) return "123";
                    if (method.getName().equals("setCharacterEncoding")) return null;
                    throw new AssertionError("Unexpected request access: " + method.getName());
                });
        AtomicInteger status = new AtomicInteger();
        HttpServletResponse response = response(status, new AtomicReference<>());
        assertNull(support.requireUser(request, response));
        assertEquals(401, status.get());
        new MealPlannerServlet().doGet(request, response);
        assertEquals(401, status.get());
        new MealPlannerServlet().doPost(request, response);
        assertEquals(401, status.get());
        new MealHistoryServlet().doGet(request, response);
        assertEquals(401, status.get());
        new FoodPreferenceServlet().doPost(request, response);
        assertEquals(401, status.get());
        new MealRecommendationsServlet().doGet(request, response);
        assertEquals(401, status.get());
        assertFalse(support.requireCsrf(request, response));
        assertEquals(403, status.get());
    }

    private void assertBadInput(org.junit.jupiter.api.function.Executable action) throws Exception {
        IllegalArgumentException error = assertThrows(IllegalArgumentException.class, action);
        assertFailure(error, 400);
    }

    private void assertFailure(Exception error, int expected) throws Exception {
        AtomicInteger status = new AtomicInteger();
        AtomicReference<String> message = new AtomicReference<>();
        Logger logger = Logger.getLogger(NutritionServletSupport.class.getName());
        Level previousLevel = logger.getLevel();
        try {
            logger.setLevel(Level.OFF);
            support.fail(response(status, message), error);
        } finally {
            logger.setLevel(previousLevel);
        }
        assertEquals(expected, status.get());
        assertFalse(message.get().contains("secret"));
        assertFalse(message.get().contains(error.getClass().getName()));
    }

    private HttpServletResponse response(AtomicInteger status, AtomicReference<String> message) {
        return (HttpServletResponse) Proxy.newProxyInstance(getClass().getClassLoader(),
                new Class<?>[]{HttpServletResponse.class}, (p, method, args) -> {
                    if (method.getName().equals("sendError")) {
                        status.set((int) args[0]);
                        message.set((String) args[1]);
                        return null;
                    }
                    throw new AssertionError("Unexpected response access: " + method.getName());
                });
    }
}
