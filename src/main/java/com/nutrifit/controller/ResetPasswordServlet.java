
package com.nutrifit.controller;

import com.nutrifit.service.PasswordResetService;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.sql.SQLException;

@WebServlet("/reset-password")
public class ResetPasswordServlet extends HttpServlet {

    private final PasswordResetService service =
            new PasswordResetService();

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        request.getRequestDispatcher(
                "/WEB-INF/views/auth/reset-password.jsp"
        ).forward(request, response);
    }

    @Override
    protected void doPost(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        request.setCharacterEncoding("UTF-8");

        String email = request.getParameter("email");
        String otp = request.getParameter("otp");
        String password = request.getParameter("password");
        String confirmPassword =
                request.getParameter("confirmPassword");

        if (password == null ||
                !password.equals(confirmPassword)) {

            request.setAttribute(
                    "error",
                    "Mật khẩu xác nhận không khớp."
            );

            request.getRequestDispatcher(
                    "/WEB-INF/views/auth/reset-password.jsp"
            ).forward(request, response);

            return;
        }

        try {
            service.resetPassword(email, otp, password);

            response.sendRedirect(
                    request.getContextPath()
                    + "/login?reset=success"
            );

            return;

        } catch (IllegalArgumentException e) {
            request.setAttribute("error", e.getMessage());

        } catch (SQLException e) {
            getServletContext().log(
                    "Password reset failed", e);

            request.setAttribute(
                    "error",
                    "Không thể đổi mật khẩu lúc này."
            );
        }

        request.getRequestDispatcher(
                "/WEB-INF/views/auth/reset-password.jsp"
        ).forward(request, response);
    }
}
