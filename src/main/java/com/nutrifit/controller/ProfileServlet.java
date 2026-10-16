
package com.nutrifit.controller;

import com.nutrifit.dao.UserDAO;
import com.nutrifit.model.User;
import com.nutrifit.service.ProfileService;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

import java.io.IOException;
import java.sql.SQLException;
import java.util.Optional;

@WebServlet("/profile")
public class ProfileServlet extends HttpServlet {

    private final UserDAO userDAO = new UserDAO();

    private final ProfileService profileService =
            new ProfileService();

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        HttpSession session = request.getSession(false);

        if (session == null
                || !(session.getAttribute("userId") instanceof Long)) {

            response.sendRedirect(
                    request.getContextPath() + "/login");
            return;
        }

        loadProfile(request, response);
    }

    @Override
    protected void doPost(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        request.setCharacterEncoding("UTF-8");

        HttpSession session = request.getSession(false);

        if (session == null
                || !(session.getAttribute("userId") instanceof Long)) {

            response.sendRedirect(
                    request.getContextPath() + "/login");
            return;
        }

        Long userId =
                (Long) session.getAttribute("userId");

        String action =
                request.getParameter("action");

        try {

            // =========================================
            // 1. CẬP NHẬT HỌ TÊN
            // =========================================

            if ("updateProfile".equals(action)) {

                String fullName =
                        request.getParameter("fullName");

                profileService.updateFullName(
                        userId, fullName);

                session.setAttribute(
                        "fullName", fullName.trim());

                session.setAttribute(
                        "profileSuccess",
                        "Cập nhật thông tin thành công.");

                response.sendRedirect(
                        request.getContextPath() + "/profile");

                return;
            }

            // =========================================
            // 2. ĐỔI MẬT KHẨU
            // =========================================

            if ("changePassword".equals(action)) {

                profileService.changePassword(
                        userId,
                        request.getParameter("currentPassword"),
                        request.getParameter("newPassword"),
                        request.getParameter("confirmPassword")
                );

                // Mật khẩu đã đổi và auth_version đã tăng.
                // Hủy session hiện tại.
                session.invalidate();

                // Tạo session mới chỉ để hiển thị thông báo.
                // Không lưu userId vào session mới.
                HttpSession newSession =
                        request.getSession(true);

                newSession.setAttribute(
                        "loginSuccess",
                        "Đổi mật khẩu thành công. "
                        + "Vui lòng đăng nhập lại bằng mật khẩu mới.");

                response.sendRedirect(
                        request.getContextPath() + "/login");

                return;
            }

            throw new IllegalArgumentException(
                    "Thao tác không hợp lệ.");

        } catch (IllegalArgumentException e) {

            request.setAttribute(
                    "error", e.getMessage());

        } catch (SQLException e) {

            log("Profile update failed", e);

            request.setAttribute(
                    "error",
                    "Không thể cập nhật thông tin lúc này.");
        }

        loadProfile(request, response);
    }

    private void loadProfile(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        HttpSession session =
                request.getSession(false);

        if (session == null
                || !(session.getAttribute("userId") instanceof Long userId)) {

            response.sendRedirect(
                    request.getContextPath() + "/login");
            return;
        }

        try {

            Optional<User> user =
                    userDAO.findById(userId);

            if (user.isEmpty()) {

                session.invalidate();

                response.sendRedirect(
                        request.getContextPath() + "/login");

                return;
            }

            request.setAttribute(
                    "user", user.get());

            Object success =
                    session.getAttribute("profileSuccess");

            if (success != null) {

                request.setAttribute(
                        "success", success);

                session.removeAttribute(
                        "profileSuccess");
            }

            request.getRequestDispatcher(
                    "/WEB-INF/views/profile/profile.jsp"
            ).forward(request, response);

        } catch (SQLException e) {

            log("Unable to load profile", e);

            response.sendError(
                    HttpServletResponse.SC_INTERNAL_SERVER_ERROR,
                    "Không thể tải thông tin tài khoản.");
        }
    }
}
