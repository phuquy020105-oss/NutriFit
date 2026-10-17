
package com.nutrifit.controller;

import com.nutrifit.model.User;
import com.nutrifit.service.AuthService;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

import java.io.IOException;
import java.sql.SQLException;
import java.util.Optional;

@WebServlet(urlPatterns = {"/login", "/logout"})
public class AuthServlet extends HttpServlet {

    private final AuthService authService =
            new AuthService();

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        String path = request.getServletPath();

        if ("/login".equals(path)) {

            request.getRequestDispatcher(
                    "/WEB-INF/views/auth/login.jsp"
            ).forward(request, response);

            return;
        }

        response.sendError(
                HttpServletResponse.SC_METHOD_NOT_ALLOWED);
    }

    @Override
    protected void doPost(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        request.setCharacterEncoding("UTF-8");

        String path = request.getServletPath();

        // Đăng xuất
        if ("/logout".equals(path)) {

            HttpSession session =
                    request.getSession(false);

            if (session != null) {
                session.invalidate();
            }

            response.sendRedirect(
                    request.getContextPath() + "/login");

            return;
        }

        if (!"/login".equals(path)) {

            response.sendError(
                    HttpServletResponse.SC_NOT_FOUND);

            return;
        }

        // Đăng nhập
        String email = request.getParameter("email");
        String password = request.getParameter("password");

        try {

            Optional<User> result =
                    authService.login(email, password);

            if (result.isEmpty()) {

                request.setAttribute(
                        "error",
                        "Email hoặc mật khẩu không chính xác."
                );

                request.getRequestDispatcher(
                        "/WEB-INF/views/auth/login.jsp"
                ).forward(request, response);

                return;
            }

            User user = result.get();

            // Chống Session Fixation
            HttpSession oldSession =
                    request.getSession(false);

            if (oldSession != null) {
                oldSession.invalidate();
            }

            HttpSession session =
                    request.getSession(true);

            session.setAttribute(
                    "userId", user.getUserId());
            session.setAttribute(
                    "authVersion", user.getAuthVersion());

            session.setAttribute(
                    "role", user.getRole().name());

            session.setAttribute(
                    "fullName", user.getFullName());

            // Session timeout: 30 phút
            session.setMaxInactiveInterval(30 * 60);

            // Chuyển tới Profile
            // Đăng nhập thành công → chuyển tới Dashboard
            response.sendRedirect(
            request.getContextPath() + "/dashboard");

        } catch (SQLException e) {

            log("Database error during login", e);

            response.sendError(
                    HttpServletResponse.SC_INTERNAL_SERVER_ERROR,
                    "Không thể đăng nhập lúc này."
            );
        }
    }
}
