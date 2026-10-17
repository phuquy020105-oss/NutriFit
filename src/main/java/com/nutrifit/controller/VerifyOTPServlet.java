
package com.nutrifit.controller;

import com.nutrifit.service.RegistrationService;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

import java.io.IOException;
import java.sql.SQLException;

@WebServlet("/verify-otp")
public class VerifyOTPServlet extends HttpServlet {

    private final RegistrationService registrationService =
            new RegistrationService();

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response
    ) throws ServletException, IOException {

        HttpSession session = request.getSession(false);

        if (session == null ||
                session.getAttribute("registrationEmail") == null) {

            response.sendRedirect(
                    request.getContextPath() + "/register"
            );
            return;
        }

        request.getRequestDispatcher(
                "/WEB-INF/views/auth/verify-otp.jsp"
        ).forward(request, response);
    }

    @Override
    protected void doPost(
            HttpServletRequest request,
            HttpServletResponse response
    ) throws ServletException, IOException {

        request.setCharacterEncoding("UTF-8");

        HttpSession session = request.getSession(false);

        if (session == null ||
                session.getAttribute("registrationEmail") == null) {

            response.sendRedirect(
                    request.getContextPath() + "/register"
            );
            return;
        }

        String email = (String) session.getAttribute(
                "registrationEmail"
        );

        String otp = request.getParameter("otp");

        try {
            Long userId = registrationService.verifyRegistration(
                    email, otp
            );

            session.removeAttribute("registrationEmail");

            // Sau khi xác minh, người dùng đăng nhập
            // bằng tài khoản vừa tạo.
            response.sendRedirect(
                    request.getContextPath()
                    + "/login?registered=1"
            );

        } catch (IllegalArgumentException e) {

            request.setAttribute("error", e.getMessage());

            request.getRequestDispatcher(
                    "/WEB-INF/views/auth/verify-otp.jsp"
            ).forward(request, response);

        } catch (SQLException e) {

            getServletContext().log(
                    "OTP verification failed", e
            );

            request.setAttribute(
                    "error",
                    "Hệ thống gặp lỗi. Vui lòng thử lại sau."
            );

            request.getRequestDispatcher(
                    "/WEB-INF/views/auth/verify-otp.jsp"
            ).forward(request, response);
        }
    }
}
