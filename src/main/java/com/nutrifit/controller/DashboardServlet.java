
package com.nutrifit.controller;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.UserDAO;
import com.nutrifit.model.User;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

import java.io.IOException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

@WebServlet("/dashboard")
public class DashboardServlet extends HttpServlet {

    private final UserDAO userDAO = new UserDAO();

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        HttpSession session = request.getSession(false);

        if (session == null
                || !(session.getAttribute("userId") instanceof Long userId)) {

            response.sendRedirect(
                    request.getContextPath() + "/login");
            return;
        }

        try {
            User user = userDAO.findById(userId)
                    .orElse(null);

            if (user == null) {
                session.invalidate();
                response.sendRedirect(
                        request.getContextPath() + "/login");
                return;
            }

            request.setAttribute("user", user);

            try (Connection conn = DatabaseConfig.getConnection()) {

                // 1. Thông tin mục tiêu
                String profileSql = """
                    SELECT target_kcal, target_water_ml,
                           weight_kg, height_cm
                    FROM userprofiles
                    WHERE user_id = ?
                    LIMIT 1
                    """;

                try (PreparedStatement ps =
                             conn.prepareStatement(profileSql)) {

                    ps.setLong(1, userId);

                    try (ResultSet rs = ps.executeQuery()) {
                        if (rs.next()) {
                            request.setAttribute(
                                    "targetCalories",
                                    rs.getObject("target_kcal"));

                            request.setAttribute(
                                    "targetWater",
                                    rs.getObject("target_water_ml"));

                            request.setAttribute(
                                    "profileWeight",
                                    rs.getObject("weight_kg"));

                            request.setAttribute(
                                    "height",
                                    rs.getObject("height_cm"));
                        }
                    }
                }

                // 2. Tổng lượng nước hôm nay
                String waterSql = """
                    SELECT COALESCE(SUM(amount_ml), 0) AS total
                    FROM waterintakelog
                    WHERE user_id = ?
                      AND logged_date = CURRENT_DATE()
                    """;

                try (PreparedStatement ps =
                             conn.prepareStatement(waterSql)) {

                    ps.setLong(1, userId);

                    try (ResultSet rs = ps.executeQuery()) {
                        if (rs.next()) {
                            request.setAttribute(
                                    "waterToday",
                                    rs.getLong("total"));
                        }
                    }
                }

                // 3. Thống kê luyện tập hôm nay
                String workoutSql = """
                    SELECT COUNT(*) AS sessions,
                           COALESCE(SUM(duration_minutes), 0)
                               AS minutes,
                           COALESCE(SUM(estimated_calories), 0)
                               AS calories
                    FROM workoutlogs
                    WHERE user_id = ?
                      AND logged_date = CURRENT_DATE()
                    """;

                try (PreparedStatement ps =
                             conn.prepareStatement(workoutSql)) {

                    ps.setLong(1, userId);

                    try (ResultSet rs = ps.executeQuery()) {
                        if (rs.next()) {
                            request.setAttribute(
                                    "workoutSessions",
                                    rs.getLong("sessions"));

                            request.setAttribute(
                                    "workoutMinutes",
                                    rs.getLong("minutes"));

                            request.setAttribute(
                                    "workoutCalories",
                                    rs.getBigDecimal("calories"));
                        }
                    }
                }

                // 4. Cân nặng gần nhất
                String weightSql = """
                    SELECT weight_kg, recorded_date
                    FROM bodymetriclog
                    WHERE user_id = ?
                    ORDER BY recorded_date DESC, metric_id DESC
                    LIMIT 1
                    """;

                try (PreparedStatement ps =
                             conn.prepareStatement(weightSql)) {

                    ps.setLong(1, userId);

                    try (ResultSet rs = ps.executeQuery()) {
                        if (rs.next()) {
                            request.setAttribute(
                                    "latestWeight",
                                    rs.getBigDecimal("weight_kg"));

                            request.setAttribute(
                                    "weightDate",
                                    rs.getDate("recorded_date"));
                        }
                    }
                }
            }

            request.getRequestDispatcher(
                    "/WEB-INF/views/dashboard/dashboard.jsp"
            ).forward(request, response);

        } catch (SQLException e) {
            log("Dashboard database error", e);

            response.sendError(
                    HttpServletResponse.SC_INTERNAL_SERVER_ERROR,
                    "Không thể tải Dashboard lúc này.");
        }
    }
}
