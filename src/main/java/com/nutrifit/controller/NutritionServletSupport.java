package com.nutrifit.controller;

import com.nutrifit.model.MealEntry;
import com.nutrifit.model.FoodPreference;
import com.nutrifit.service.MealPlannerService;
import com.nutrifit.util.Csrf;
import com.nutrifit.util.CurrentUser;
import jakarta.servlet.ServletException;
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
                "Vui lòng đăng nhập để sử dụng nhật ký ăn uống");
        return null;
    }

    protected boolean requireCsrf(HttpServletRequest request, HttpServletResponse response)
            throws IOException {
        if (Csrf.valid(request)) return true;
        response.sendError(HttpServletResponse.SC_FORBIDDEN, "Biểu mẫu không hợp lệ hoặc đã hết hạn. Vui lòng tải lại trang");
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
            LocalDate day = LocalDate.parse(input);
            if (day.getYear() < 1000) throw new IllegalArgumentException("Date is outside the database range");
            return day;
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

    /** Render a controlled Nutrition error view; never expose submitted values or exception details. */
    protected void fail(HttpServletRequest request, HttpServletResponse response, Exception exception)
            throws ServletException, IOException {
        int status;
        String message;
        if (exception instanceof IllegalArgumentException || exception instanceof DateTimeParseException) {
            status = HttpServletResponse.SC_BAD_REQUEST;
            message = "Thông tin chưa hợp lệ. Hãy kiểm tra món ăn, bữa, khẩu phần hoặc ngày đã chọn. "
                    + "Nhật ký chỉ được chỉnh sửa trong ngày hiện tại; không thể đổi sang món đã có trong cùng bữa.";
        } else if (exception instanceof SecurityException) {
            status = HttpServletResponse.SC_FORBIDDEN;
            message = "Bạn không có quyền thực hiện thao tác này. Hãy kiểm tra quyền truy cập của tài khoản.";
        } else if (exception instanceof SQLException) {
            status = HttpServletResponse.SC_SERVICE_UNAVAILABLE;
            message = "Chưa thể truy cập dữ liệu. Vui lòng tải lại nhật ký để kiểm tra trước khi gửi lại thao tác.";
            LOG.log(Level.SEVERE, "Meal Planner database error", exception);
        } else {
            status = HttpServletResponse.SC_INTERNAL_SERVER_ERROR;
            message = "Không thể hoàn tất yêu cầu. Vui lòng tải lại nhật ký để kiểm tra trước khi gửi lại thao tác.";
            LOG.log(Level.SEVERE, "Unexpected Meal Planner error", exception);
        }
        response.setStatus(status);
        request.setAttribute("errorStatus", status);
        request.setAttribute("errorMessage", message);
        request.getRequestDispatcher("/WEB-INF/views/nutrition/nutrition-error.jsp").forward(request, response);
    }
}
