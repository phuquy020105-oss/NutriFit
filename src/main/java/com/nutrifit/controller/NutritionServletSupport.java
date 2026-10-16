package com.nutrifit.controller;

import com.nutrifit.model.MealEntry;
import com.nutrifit.model.FoodPreference;
import com.nutrifit.service.MealPlannerService;
import com.nutrifit.util.Csrf;
import com.nutrifit.util.CurrentUser;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.math.BigDecimal;
import java.sql.SQLException;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.OptionalLong;
import java.util.logging.Level;
import java.util.logging.Logger;

/** Common small HTTP helpers; no module user identity is accepted from input fields. */
abstract class NutritionServletSupport extends HttpServlet {
    private static final Logger LOG = Logger.getLogger(NutritionServletSupport.class.getName());

    protected Long requireUser(HttpServletRequest request, HttpServletResponse response)
            throws IOException {
        OptionalLong user = CurrentUser.id(request);
        if (user.isPresent()) return user.getAsLong();
        response.sendError(HttpServletResponse.SC_UNAUTHORIZED,
                "Please log in to access Meal Planner (Auth integration pending)");
        return null;
    }

    protected boolean requireCsrf(HttpServletRequest request, HttpServletResponse response)
            throws IOException {
        if (Csrf.valid(request)) return true;
        response.sendError(HttpServletResponse.SC_FORBIDDEN, "Invalid form token");
        return false;
    }

    protected static long parseId(String value) {
        String input = required(value);
        if (!input.matches("[0-9]{1,19}")) throw new IllegalArgumentException("Invalid identifier");
        try {
            long id = Long.parseLong(input);
            if (id > 0) return id;
        } catch (NumberFormatException ignored) {
            // An unsigned database ID must still fit the application's signed long API.
        }
        throw new IllegalArgumentException("Invalid identifier");
    }

    protected static MealEntry.MealType parseMealType(String value) {
        return MealEntry.MealType.valueOf(required(value));
    }

    protected static FoodPreference.PreferenceType parsePreferenceType(String value) {
        return FoodPreference.PreferenceType.valueOf(required(value));
    }

    protected static BigDecimal parseServings(String value) {
        String input = required(value);
        // Bound parsing work and reject exponent notation before constructing BigDecimal.
        if (input.length() > 32 || !input.matches("[0-9]+(?:\\.[0-9]+)?")) {
            throw new IllegalArgumentException("Invalid servings");
        }
        return MealPlannerService.validServings(new BigDecimal(input));
    }

    protected static LocalDate parseDate(String value) {
        String input = required(value);
        if (!input.matches("[0-9]{4}-[0-9]{2}-[0-9]{2}")) {
            throw new IllegalArgumentException("Date must use yyyy-MM-dd");
        }
        try {
            return LocalDate.parse(input);
        } catch (DateTimeParseException e) {
            throw new IllegalArgumentException("Invalid calendar date");
        }
    }

    protected static String required(String value) {
        if (value == null || value.isBlank()) throw new IllegalArgumentException("Missing parameter");
        return value.trim();
    }

    protected void fail(HttpServletResponse response, Exception exception) throws IOException {
        if (exception instanceof IllegalArgumentException || exception instanceof DateTimeParseException) {
            response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Invalid request parameters");
        } else if (exception instanceof SecurityException) {
            response.sendError(HttpServletResponse.SC_FORBIDDEN, "Access denied");
        } else if (exception instanceof SQLException) {
            LOG.log(Level.SEVERE, "Meal Planner database error", exception);
            response.sendError(HttpServletResponse.SC_SERVICE_UNAVAILABLE, "Database unavailable");
        } else {
            LOG.log(Level.SEVERE, "Unexpected Meal Planner error", exception);
            response.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR, "Unexpected error");
        }
    }
}
