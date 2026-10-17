
package com.nutrifit.filter;

import com.nutrifit.dao.UserDAO;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.annotation.WebFilter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

import java.io.IOException;
import java.sql.SQLException;
import java.util.Optional;

@WebFilter(urlPatterns = {"/profile", "/profile/*",
                         "/dashboard", "/dashboard/*", "/chatbot"})
public class AuthFilter implements Filter {

    private final UserDAO userDAO = new UserDAO();

    @Override
    public void doFilter(
            ServletRequest servletRequest,
            ServletResponse servletResponse,
            FilterChain chain)
            throws IOException, ServletException {

        HttpServletRequest request =
                (HttpServletRequest) servletRequest;

        HttpServletResponse response =
                (HttpServletResponse) servletResponse;

        HttpSession session = request.getSession(false);

        if (session == null) {
            redirectToLogin(request, response);
            return;
        }

        Object userIdObject =
                session.getAttribute("userId");

        Object authVersionObject =
                session.getAttribute("authVersion");

        if (!(userIdObject instanceof Long userId)
                || !(authVersionObject instanceof Long sessionVersion)) {

            session.invalidate();
            redirectToLogin(request, response);
            return;
        }

        try {
            Optional<Long> databaseVersion =
                    userDAO.findAuthVersionById(userId);

            if (databaseVersion.isEmpty()
                    || databaseVersion.get().longValue()
                    != sessionVersion.longValue()) {

                session.invalidate();
                redirectToLogin(request, response);
                return;
            }

            chain.doFilter(request, response);

        } catch (SQLException e) {

            throw new ServletException(
                    "Không thể xác minh phiên đăng nhập.", e);
        }
    }

    private void redirectToLogin(
            HttpServletRequest request,
            HttpServletResponse response)
            throws IOException {

        response.sendRedirect(
                request.getContextPath() + "/login");
    }
}
