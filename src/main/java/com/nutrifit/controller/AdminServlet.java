
package com.nutrifit.controller;

import com.nutrifit.model.User;
import com.nutrifit.service.AdminService;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.sql.SQLException;
import java.util.List;

@WebServlet(urlPatterns = {
        "/admin",
        "/admin/users",
        "/admin/users/change-role"
})
public class AdminServlet extends HttpServlet {

    private final AdminService adminService = new AdminService();

    // =====================================================
    // 1. XỬ LÝ GET
    // =====================================================

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        String path = request.getServletPath();

        try {

            switch (path) {

                case "/admin" -> showDashboard(
                        request, response);

                case "/admin/users" -> showUsers(
                        request, response);

                default -> response.sendError(
                        HttpServletResponse.SC_NOT_FOUND);
            }

        } catch (IllegalArgumentException e) {

            response.sendError(
                    HttpServletResponse.SC_BAD_REQUEST,
                    e.getMessage());

        } catch (SQLException e) {

            throw new ServletException(
                    "Không thể tải dữ liệu Admin.", e);
        }
    }

    // =====================================================
    // 2. XỬ LÝ POST
    // =====================================================

    @Override
    protected void doPost(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        // Chỉ cho phép POST đổi quyền
        if (!"/admin/users/change-role".equals(
                request.getServletPath())) {

            response.sendError(
                    HttpServletResponse.SC_METHOD_NOT_ALLOWED);
            return;
        }

        // ================================================
        // 2.1. KIỂM TRA SESSION
        // ================================================

        HttpSession session = request.getSession(false);

        if (session == null) {

            response.sendRedirect(
                    request.getContextPath() + "/login");
            return;
        }

        // ================================================
        // 2.2. KIỂM TRA CSRF TOKEN
        // ================================================

        Object tokenObject =
                session.getAttribute("csrfToken");

        String submittedToken =
                request.getParameter("_csrf");

        if (!(tokenObject instanceof String expectedToken)
                || submittedToken == null
                || !MessageDigest.isEqual(
                        expectedToken.getBytes(
                                StandardCharsets.UTF_8),
                        submittedToken.getBytes(
                                StandardCharsets.UTF_8))) {

            response.sendError(
                    HttpServletResponse.SC_FORBIDDEN,
                    "CSRF token không hợp lệ.");
            return;
        }

        // ================================================
        // 2.3. LẤY ADMIN ID TỪ SESSION
        // ================================================

        Object actorObject =
                session.getAttribute("userId");

        if (!(actorObject instanceof Long actorId)) {

            session.invalidate();

            response.sendRedirect(
                    request.getContextPath() + "/login");
            return;
        }

        // ================================================
        // 2.4. XỬ LÝ THAY ĐỔI QUYỀN
        // ================================================

        try {

            String userIdParam =
                    request.getParameter("userId");

            if (userIdParam == null
                    || userIdParam.isBlank()) {

                throw new IllegalArgumentException(
                        "Vui lòng chọn tài khoản.");
            }

            Long targetUserId =
                    Long.valueOf(userIdParam.trim());

            String newRole =
                    request.getParameter("role");

            boolean updated =
                    adminService.changeUserRole(
                            actorId,
                            targetUserId,
                            newRole);

            // Redirect sau POST để tránh gửi lại form
            String result = updated
                    ? "updated"
                    : "unchanged";

            response.sendRedirect(
                    request.getContextPath()
                            + "/admin/users?result="
                            + result);

        } catch (IllegalArgumentException e) {

            response.sendError(
                    HttpServletResponse.SC_BAD_REQUEST,
                    e.getMessage());

        } catch (SecurityException e) {

            response.sendError(
                    HttpServletResponse.SC_FORBIDDEN,
                    e.getMessage());

        } catch (SQLException e) {

            throw new ServletException(
                    "Không thể cập nhật quyền tài khoản.", e);
        }
    }

    // =====================================================
    // 3. HIỂN THỊ ADMIN DASHBOARD
    // =====================================================

    private void showDashboard(
            HttpServletRequest request,
            HttpServletResponse response)
            throws SQLException, ServletException, IOException {

        long totalUsers =
                adminService.getTotalUsers();

        long totalAdmins =
                adminService.getTotalAdmins();

        long totalPremiumUsers =
                adminService.getTotalPremiumUsers();

        long newUsersToday =
                adminService.getNewUsersToday();

        request.setAttribute(
                "totalUsers", totalUsers);

        request.setAttribute(
                "totalAdmins", totalAdmins);

        request.setAttribute(
                "totalPremiumUsers", totalPremiumUsers);

        request.setAttribute(
                "newUsersToday", newUsersToday);

        request.getRequestDispatcher(
                "/WEB-INF/views/admin/dashboard.jsp")
                .forward(request, response);
    }

    // =====================================================
    // 4. HIỂN THỊ DANH SÁCH NGƯỜI DÙNG
    // =====================================================

    private void showUsers(
            HttpServletRequest request,
            HttpServletResponse response)
            throws SQLException, ServletException, IOException {

        String keyword =
                request.getParameter("q");

        List<User> users =
                adminService.getUsers(keyword);

        request.setAttribute(
                "users", users);

        request.setAttribute(
                "keyword",
                keyword == null ? "" : keyword);

        request.setAttribute(
                "result",
                request.getParameter("result"));

        request.getRequestDispatcher(
                "/WEB-INF/views/admin/users.jsp")
                .forward(request, response);
    }
}
