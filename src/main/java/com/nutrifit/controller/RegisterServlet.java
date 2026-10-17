
package com.nutrifit.controller;

import com.nutrifit.service.RegistrationService;
import jakarta.mail.MessagingException;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.sql.SQLException;
import java.util.Locale;

@WebServlet("/register")
public class RegisterServlet extends HttpServlet {

    private final RegistrationService registrationService =
            new RegistrationService();

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response
    ) throws ServletException, IOException {

        request.getRequestDispatcher(
                "/WEB-INF/views/auth/register.jsp"
        ).forward(request, response);
    }

    @Override
    protected void doPost(
            HttpServletRequest request,
            HttpServletResponse response
    ) throws ServletException, IOException {

        request.setCharacterEncoding("UTF-8");

        String fullName = request.getParameter("fullName");
        String email = request.getParameter("email");
        String password = request.getParameter("password");

        String clientIp = request.getRemoteAddr();

        try {
            registrationService.requestRegistration(
                    fullName,
                    email,
                    password,
                    clientIp
            );

            String normalizedEmail =
                    email.trim().toLowerCase(Locale.ROOT);

            request.getSession().setAttribute(
                    "registrationEmail",
                    normalizedEmail
            );

            response.sendRedirect(
                    request.getContextPath() + "/verify-otp"
            );

        } catch (IllegalArgumentException e) {

            request.setAttribute("error", e.getMessage());
            request.setAttribute("fullName", fullName);
            request.setAttribute("email", email);

            showRegister(request, response);

        } catch (SQLException | MessagingException |
                 IllegalStateException e) {

            getServletContext().log(
                    "Registration request failed", e
            );

            request.setAttribute(
                    "error",
                    "Không thể gửi OTP lúc này. Vui lòng thử lại sau."
            );

            showRegister(request, response);
        }
    }

    private void showRegister(
            HttpServletRequest request,
            HttpServletResponse response
    ) throws ServletException, IOException {

        request.getRequestDispatcher(
                "/WEB-INF/views/auth/register.jsp"
        ).forward(request, response);
    }
}
