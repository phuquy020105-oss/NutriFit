package com.nutrifit.controller;

import com.nutrifit.model.MealEntry;
import com.nutrifit.util.Csrf;
import com.nutrifit.util.CurrentUser;
import com.nutrifit.util.Html;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.math.BigDecimal;
import java.sql.SQLException;
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
        long id = Long.parseLong(value);
        if (id <= 0) throw new IllegalArgumentException("Invalid identifier");
        return id;
    }

    protected static MealEntry.MealType parseMealType(String value) {
        return MealEntry.MealType.valueOf(value);
    }

    protected static BigDecimal parseServings(String value) {
        return new BigDecimal(value);
    }

    protected void fail(HttpServletResponse response, Exception exception) throws IOException {
        if (exception instanceof IllegalArgumentException) {
            response.sendError(HttpServletResponse.SC_BAD_REQUEST, exception.getMessage());
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
