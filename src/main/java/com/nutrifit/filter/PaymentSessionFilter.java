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

/** Applies only to protected payment UI/API paths; never to public VNPay IPN. */
@WebFilter(urlPatterns = {"/payment", "/payment/return", "/api/features"})
public final class PaymentSessionFilter implements Filter {
    private final UserDAO users = new UserDAO();
    @Override public void doFilter(ServletRequest rawRequest, ServletResponse rawResponse,
                                  FilterChain chain) throws IOException, ServletException {
        HttpServletRequest request = (HttpServletRequest) rawRequest;
        HttpServletResponse response = (HttpServletResponse) rawResponse;
        HttpSession session = request.getSession(false);
        if (session == null || !(session.getAttribute("userId") instanceof Long id)
                || !(session.getAttribute("authVersion") instanceof Long version)) {
            reject(request, response); return;
        }
        try {
            Optional<Long> current = users.findAuthVersionById(id);
            if (current.isEmpty() || current.get().longValue() != version.longValue()) {
                session.invalidate(); reject(request, response); return;
            }
        } catch (SQLException e) {
            throw new ServletException("Unable to validate payment session", e);
        }
        chain.doFilter(request, response);
    }
    private static void reject(HttpServletRequest req, HttpServletResponse res) throws IOException {
        if ("/api/features".equals(req.getServletPath())) {
            res.sendError(HttpServletResponse.SC_UNAUTHORIZED); return;
        }
        res.sendRedirect(req.getContextPath() + "/login");
    }
}
