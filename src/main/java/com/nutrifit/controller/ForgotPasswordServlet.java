
package com.nutrifit.controller;

import com.nutrifit.service.PasswordResetService;

import jakarta.mail.MessagingException;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.sql.SQLException;

@WebServlet("/forgot-password")
public class ForgotPasswordServlet extends HttpServlet {

    private final PasswordResetService service =
            new PasswordResetService();

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        request.getRequestDispatcher(
                "/WEB-INF/views/auth/forgot-password.jsp"
        ).forward(request, response);
    }

    @Override
    protected void doPost(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        request.setCharacterEncoding("UTF-8");

        String email = request.getParameter("email");

        // Lấy IP trực tiếp từ kết nối đến Tomcat.
        // Không tin X-Forwarded-For do client tự gửi.
        String clientIp = request.getRemoteAddr();

        try {
            service.requestReset(email, clientIp);

            // Phản hồi giống nhau dù email tồn tại,
            // không tồn tại hoặc đã vượt quota.
            request.setAttribute(
                    "success",
                    "Nếu email đã đăng ký và yêu cầu hợp lệ, "
                    + "mã OTP sẽ được gửi đến hộp thư. "
                    + "Vui lòng kiểm tra Gmail."
            );

        } catch (IllegalArgumentException e) {

            request.setAttribute(
                    "error",
                    e.getMessage()
            );

        } catch (SQLException | MessagingException |
                 IllegalStateException e) {

            getServletContext().log(
                    "Password reset request failed", e);

            request.setAttribute(
                    "error",
                    "Không thể xử lý yêu cầu lúc này. "
                    + "Vui lòng thử lại sau."
            );
        }

        request.getRequestDispatcher(
                "/WEB-INF/views/auth/forgot-password.jsp"
        ).forward(request, response);
    }
}
